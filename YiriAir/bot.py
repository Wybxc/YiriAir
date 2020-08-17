# -*- encoding=utf8 -*-

import time
import logging
from functools import wraps
from .driver import PocoDriver, Session, logger_yiri


class YiriAir():
    '''机器人主类，提供易用的 API 调用封装。
    '''

    def __init__(self, device, logging_level=logging.ERROR, query_interval=1):
        '''
        :param device: 设备地址，参看`driver.Devices`。
        :param logging_level: 日志等级，默认为`ERROR`级。
        :param query_interval: 查询消息的时间间隔，单位为秒。
        '''
        self.driver = PocoDriver(device, logging_level)
        self.current_session = Session(self.driver)
        self.query_interval = query_interval
        self.message_hooks = []

    def on_message(self, message_type: str = 'Text'):
        '''注册消息处理函数，用作装饰器。

        :param message_type: 消息类型，可以为 Text, Image, Voice, Unknown, Other。当前版本只有 Text 类型支持具体内容。
        '''
        def decorator(func):
            @wraps(func)
            def decorated(message, title):
                txt, msg_type, sender = message
                if msg_type == message_type:
                    return func(txt, title, sender)
            self.message_hooks.append(decorated)
            return decorated
        return decorator

    def send_message(self, msg_text: str) -> bool:
        '''向当前会话发送一条文本消息。

        :param msg_text: 要发送的消息。
        :returns: 是否成功，成功为 True，失败为 None.
        '''
        return self.current_session.send_message(msg_text)

    def run(self):
        '''主循环，运行机器人实例。
        '''
        logger_yiri.info('开始运行，按 Ctrl + C 退出……')
        while True:
            # 检查当前会话有无新消息
            messages = self.current_session.check_latest_message()
            for msg in messages:
                for hook in self.message_hooks:
                    hook(msg, self.current_session.title)
            # 检查其他会话有无新消息
            self.current_session.try_jump_to_new_session()

            time.sleep(self.query_interval)
