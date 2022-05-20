# -*- encoding=utf8 -*-
import time
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.exceptions import PocoNoSuchNodeException
from hrpc.exceptions import RpcRemoteException
from airtest.core.api import auto_setup, keyevent, start_app
import logging

logger_yiri_handler = logging.StreamHandler()
logger_yiri_handler.setLevel(logging.INFO)
logger_yiri_formatter = logging.Formatter(fmt='[%(levelname)s][%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M')
logger_yiri_handler.setFormatter(logger_yiri_formatter)
logger_yiri = logging.getLogger('YiriAir')
logger_yiri.addHandler(logger_yiri_handler)
logger_yiri.setLevel(logging.INFO)

class Devices():
    DEFAULT = "Android:///"
    NOX = "Android://127.0.0.1:5037/127.0.0.1:62001?cap_method=JAVACAP^&^&ori_method=ADBORI"
    MUMU = "Android://127.0.0.1:5037/127.0.0.1:7555?cap_method=JAVACAP^&^&ori_method=ADBORI"
    XIAO_YAO = "Android://127.0.0.1:5037/127.0.0.1:21503?cap_method=JAVACAP^&^&ori_method=ADBORI"


def _analyze_message_type(chat_item_content_layout):
    layout_type = chat_item_content_layout.attr('type')

    # 文本消息（或不支持的消息）
    if layout_type == 'android.widget.TextView':
        txt = chat_item_content_layout.get_text().strip()
        return ('', 'Unknown') if txt[4:] == '请使用最新版手机QQ查看。' else (txt, 'Text')
    elif layout_type == 'android.widget.LinearLayout':
        txt = chat_item_content_layout.child(
            'com.tencent.qqlite:id/chat_item_content_text').get_text().strip()
        return txt, 'Text'
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
        footer = self.poco("com.tencent.qqlite:id/tw_main")
        while not footer.exists():
            keyevent("BACK")
        footer.child("com.tencent.qqlite:id/tab1").click()
        self.poco("com.tencent.qqlite:id/contentFrame").offspring("com.tencent.qqlite:id/vPager").offspring(
            "com.tencent.qqlite:id/recent_chat_list").child("android.widget.LinearLayout")[0].click()


class Session():
    def __init__(self, driver, hot=False):
        self.poco = driver

        self.latest_message = None        
        self.init_latest_message()
        self._hot = hot

    def init_latest_message(self):
        if message_list := self.get_message_list():
            self.latest_message = message_list[-1]
        self.title = self.get_title()
        logger_yiri.info(f'Session set up. Title: {self.title}')

    def normalize_qqlite(self):
        self.poco.normalize_qqlite()
        self.init_latest_message()

    def _get_message_list_iter(self):
        try:
            msg_list = self.poco(
                "com.tencent.qqlite:id/listView1").child("com.tencent.qqlite:id/base_chat_item_layout")
            if not msg_list.exists():
                return
            for msg_container in msg_list:
                msg = msg_container.child(
                    "com.tencent.qqlite:id/chat_item_content_layout")                
                if msg.get_position()[0] < 0.5:
                    sender = msg_container.child("com.tencent.qqlite:id/chat_item_nick_name")
                    sender = sender.get_text()[:-1] if sender.exists() else ''
                    txt, msg_type = _analyze_message_type(msg)
                    yield txt, msg_type, sender
        except PocoNoSuchNodeException as e:
            logger_yiri.error(e)
            self.normalize_qqlite()
        except RpcRemoteException as e:
            logger_yiri.error(e)
            self.normalize_qqlite()

    def get_message_list(self):
        return list(self._get_message_list_iter())

    def send_message(self, msg_text):
        try:
            input_box = self.poco("com.tencent.qqlite:id/input")
            input_box.click()
            input_box.set_text(msg_text)
            keyevent("ENTER")
            return True
        except PocoNoSuchNodeException as e:
            logger_yiri.error(e)
            self.normalize_qqlite()
            return False

    def get_title(self):
        try:
            return self.poco("com.tencent.qqlite:id/title").get_text()
        except PocoNoSuchNodeException as e:
            logger_yiri.error(e)
            self.normalize_qqlite()

    def exit(self):
        self.poco("com.tencent.qqlite:id/ivTitleBtnLeft").click()

    def jump_to_new_session(self):
        msgbox = self.poco("com.tencent.qqlite:id/msgbox")
        if msgbox.exists():
            msgbox.click()
            time.sleep(0.1)
            return Session(self.poco, hot=True)
        else:
            return self

    def check_latest_message(self):
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
                for msg in reversed(message_list):
                    msg = msg
                    if msg == self.latest_message:
                        break
                    yield msg
            result = reversed(list(check_latest_message_iter()))
            self.latest_message = message_list[-1]
            return result
        else:
            return []
