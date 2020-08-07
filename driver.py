# -*- encoding=utf8 -*-
import time
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from airtest.core.api import auto_setup, keyevent, home, start_app, stop_app
import logging


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
        if txt[4:] == '请使用最新版手机QQ查看。':
            return '', 'Unknown'
        else:
            return txt, 'Plain Text'
    # 回复消息
    elif layout_type == 'android.widget.LinearLayout':
        txt = chat_item_content_layout.child('com.tencent.qqlite:id/chat_item_content_text').get_text()
        return txt, 'Reply'
    # 图片或多媒体信息
    elif layout_type == 'android.widget.RelativeLayout':
        if chat_item_content_layout.child("com.tencent.qqlite:id/pic").exists():
            return '', 'Image'
    # 其他
    return '', 'Other'


class PocoDriver():
    def __init__(self, device, logging_level=logging.ERROR):
            logger = logging.getLogger("airtest")
            logger.setLevel(logging_level)

            auto_setup(__file__, devices=[device])

            stop_app('com.tencent.qqlite')
            start_app('com.tencent.qqlite')
            self.poco = AndroidUiautomationPoco(
                use_airtest_input=True, screenshot_each_action=False)
            self.poco.click((0.5, 0.117))
        
    def __call__(self, *args, **kwargs):
        return self.poco(*args, **kwargs)


class Session():
    def __init__(self, driver, hot=False):
        self.poco = driver
        message_list = self.get_message_list()
        if message_list:
            self.latest_message = message_list[-1]
        else:
            self.latest_message = None
        self.title = self.get_title()
        self._hot = hot

    def _get_message_list_iter(self):
        try:
            msg_list = self.poco("com.tencent.qqlite:id/listView1").child("com.tencent.qqlite:id/base_chat_item_layout")
            if not msg_list.exists():            
                return
            for msg_container in msg_list:
                msg = msg_container.child(
                    "com.tencent.qqlite:id/chat_item_content_layout")
                if msg.get_position()[0] < 0.5:
                    txt, msg_type = _analyze_message_type(msg)
                    if msg_type == 'Plain Text' or msg_type == 'Reply':
                        yield txt.strip()
        except:
            pass

    def get_message_list(self):
        return list(self._get_message_list_iter())

    def send_message(self, msg_text):
        try:
            input_box = self.poco("com.tencent.qqlite:id/input")
            input_box.click()
            input_box.set_text(msg_text)
            keyevent("ENTER")
            return True
        except:
            return False

    def get_title(self):
        return self.poco("com.tencent.qqlite:id/title").get_text()

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
