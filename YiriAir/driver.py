# -*- encoding=utf8 -*-
import time
from functools import wraps
from typing import Any, List, Tuple
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.exceptions import PocoNoSuchNodeException
from hrpc.exceptions import RpcRemoteException
from poco.proxy import UIObjectProxy
from airtest.core.api import auto_setup, keyevent, start_app
import logging

# 修改日志格式及输出等级
logger_yiri_handler = logging.StreamHandler()
logger_yiri_handler.setLevel(logging.INFO)
logger_yiri_formatter = logging.Formatter(
    fmt='[%(levelname)s][%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M')
logger_yiri_handler.setFormatter(logger_yiri_formatter)
logger_yiri = logging.getLogger('YiriAir')
logger_yiri.addHandler(logger_yiri_handler)
logger_yiri.setLevel(logging.INFO)


class Devices():
    '''各种常用设备的地址。
    '''
    DEFAULT = "Android:///"
    NOX = "Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP^&^&ori_method=ADBORI"
    MUMU = "Android://127.0.0.1:5037/127.0.0.1:7555?cap_method=JAVACAP^&^&ori_method=ADBORI"
    逍遥 = "Android://127.0.0.1:5037/127.0.0.1:21503?cap_method=JAVACAP^&^&ori_method=ADBORI"


def _analyze_message_type(chat_item_content_layout: UIObjectProxy) -> Tuple[str, str]:
    '''分析消息节点的类型，并返回其内容。

    :param chat_item_content_layout: `name`为`com.tencent.qqlite:id/chat_item_content_layout`的UI节点。
    :returns: 消息内容和消息类型。
    '''
    layout_type = chat_item_content_layout.attr('type')

    # 文本消息（或不支持的消息）
    if layout_type == 'android.widget.TextView':
        txt = chat_item_content_layout.get_text().strip()
        if txt[4:] == '请使用最新版手机QQ查看。':
            return '', 'Unknown'
        else:
            return txt, 'Text'
    # 回复消息
    elif layout_type == 'android.widget.LinearLayout':
        txt = chat_item_content_layout.child(
            'com.tencent.qqlite:id/chat_item_content_text').get_text().strip()
        return txt, 'Text'
    # 图片、语音或多媒体信息
    elif layout_type == 'android.widget.RelativeLayout':
        # 图片
        if chat_item_content_layout.child("com.tencent.qqlite:id/pic").exists():
            return '', 'Image'
        # 语音
        elif chat_item_content_layout.child("com.tencent.qqlite:id/qq_aio_ptt_flag_time_container").exists():
            return '', 'Voice'
    # 其他
    return '', 'Other'


class PocoDriver():
    '''代理执行 poco 命令。
    '''

    def __init__(self, device, logging_level=logging.ERROR):
        logger = logging.getLogger("airtest")
        logger.setLevel(logging_level)

        auto_setup(__file__, devices=[device])

        start_app('com.tencent.qqlite')
        self.poco = AndroidUiautomationPoco(
            use_airtest_input=True, screenshot_each_action=False)

        self.normalize_qqlite()

    def __call__(self, *args, **kwargs):
        return self.poco(*args, **kwargs)

    def normalize_qqlite(self):
        '''初始化或重新初始化QQ轻聊版。（自动打开第一个聊天窗口）
        '''
        # 退回主界面
        footer = self.poco("com.tencent.qqlite:id/tw_main")
        while not footer.exists():
            keyevent("BACK")
        # 切换到第一列
        footer.child("com.tencent.qqlite:id/tab1").click()
        # 打开第一个聊天窗口
        self.poco("com.tencent.qqlite:id/contentFrame").offspring("com.tencent.qqlite:id/vPager").offspring(
            "com.tencent.qqlite:id/recent_chat_list").child("android.widget.LinearLayout")[0].click()


class Session():
    '''一个聊天会话。
    '''

    def __init__(self, driver: PocoDriver):
        '''
        :param driver: 使用的 PocoDriver。
        '''
        self.poco = driver
        self._locked = False  # 锁机制：在执行需要poco的操作时会加锁，防止操作之间互相干扰
        self.init_session()

    def init_session(self, hot=False):
        '''初始化会话，包括“最新”消息、会话标题。

        :param hot: 是否为“热”会话（收到新消息而打开的会话）。
        '''
        self._hot = hot

        self.latest_message = None
        message_list = self.get_message_list()
        if message_list:
            self.latest_message = message_list[-1]

        self.title = self.get_title()
        logger_yiri.info('Session set up. Title: {}'.format(self.title))

    def normalize_qqlite(self):
        '''初始化或重新初始化QQ轻聊版，并初始化会话。
        '''
        self.poco.normalize_qqlite()
        self.init_session()

    def _poco_action(null: Any = None):
        '''修饰包含 poco 操作的方法的装饰器，提供锁相关及错误处理。
        '''
        def decorator(func):
            @wraps(func)
            def decorated(self, *args, **kwargs):
                try:
                    # 请求锁
                    while self._locked:
                        time.sleep(0)
                    self._locked = True

                    result = func(self, *args, **kwargs)                    
                    return result

                except PocoNoSuchNodeException as e:  # 未找到节点
                    logger_yiri.error(e)
                    self.normalize_qqlite()
                    return null
                except RpcRemoteException as e:  # 节点变化过快或操作过快
                    logger_yiri.error(e)
                    self.normalize_qqlite()
                    return null
                finally:
                    # 释放锁
                    self._locked = False                    
            return decorated
        return decorator

    @_poco_action()
    def get_message_list(self) -> List[Tuple[str, str, str]]:
        '''获取当前会话显示的所有消息。

        :returns: 一个 list，其中每个元素均为三元组，分别为 (消息内容, 消息类型, 发送者名片)
        '''
        def _get_message_list_iter():
            msg_list = self.poco(
                "com.tencent.qqlite:id/listView1").child("com.tencent.qqlite:id/base_chat_item_layout")
            if not msg_list.exists():
                return
            for msg_container in msg_list:
                msg = msg_container.child(
                    "com.tencent.qqlite:id/chat_item_content_layout")
                if msg.get_position()[0] < 0.5:
                    sender = msg_container.child(
                        "com.tencent.qqlite:id/chat_item_nick_name")
                    sender = sender.get_text()[:-1] if sender.exists() else ''
                    txt, msg_type = _analyze_message_type(msg)
                    yield txt, msg_type, sender
        return list(_get_message_list_iter())

    @_poco_action(null=False)
    def send_message(self, msg_text: str) -> bool:
        '''向当前会话发送一条文本消息。

        :param msg_text: 要发送的消息。
        :returns: 是否成功，成功为 True，失败为 None.
        '''
        input_box = self.poco("com.tencent.qqlite:id/input")
        input_box.click()
        input_box.set_text(msg_text)
        keyevent("ENTER")
        return True

    @_poco_action()
    def get_title(self):
        '''获取会话标题

        :returns: str，会话标题。
        '''
        return self.poco("com.tencent.qqlite:id/title").get_text()

    def try_jump_to_new_session(self):
        '''检查是否有来自其他会话的消息，如果有，那么跳转到新的会话。
        '''
        msgbox = self.poco("com.tencent.qqlite:id/msgbox")
        if msgbox.exists():
            msgbox.click()
            time.sleep(0.1)
            self.init_session(hot=True)

    def check_latest_message(self) -> List[Tuple[str, str, str]]:
        '''检查并返回“新”消息。

        :returns: 一个 list，其中每个元素均为三元组，分别为 (消息内容, 消息类型, 发送者名片)
        '''
        message_list = self.get_message_list()
        if message_list:
            if self._hot:
                self.latest_message = message_list[-1]
                self._hot = False
                return [message_list[-1]]

            if self.latest_message is None:
                self.latest_message = message_list[-1]
                return []

            def check_latest_message_iter():
                # TODO: 优化新消息判断逻辑
                for msg in reversed(message_list):
                    if msg == self.latest_message:
                        break
                    yield msg

            result = reversed(list(check_latest_message_iter()))
            self.latest_message = message_list[-1]
            return result
        else:
            return []
