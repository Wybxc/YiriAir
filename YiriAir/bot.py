# -*- encoding=utf8 -*-

import time
import logging
from functools import wraps
from .driver import PocoDriver, Session, logger_yiri


class Sender(dict):
    '''消息来源的信息，包括会话类型、标题、来源的群昵称。
    '''

    def __init__(self, session_type, title, sender):
        self['session_type'] = session_type
        self['title'] = title
        self['sender'] = sender

    @property
    def session_type(self):
        '''会话类型。
        '''
        return self['session_type']

    @property
    def title(self):
        '''标题。
        '''
        return self['title']

    @property
    def sender(self):
        '''来源的群昵称，私聊时为空。
        '''
        return self['sender']


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

    def on_message(self, session_type: str = 'All', message_type: str = 'Text'):
        '''注册消息处理函数，用作装饰器。

        消息处理函数需要有两个参数`msg`和`sender`

        :param message_type: 消息类型，可以为 Text, Image, Voice, Unknown, Other。当前版本只有 Text 类型支持具体内容。
        '''
        def decorator(func):
            @wraps(func)
            def decorated(message, title):
                msg_text, msg_type, sender = message
                if (session_type == 'All' or session_type == self.current_session.info.session_type) \
                        and (message_type == 'All' or message_type == msg_type):
                    return func(msg_text, Sender(self.current_session.info.session_type, title, sender))
            self.message_hooks.append(decorated)
            return decorated
        return decorator

    def send_message(self, msg_text: str) -> bool:
        '''向当前会话发送一条文本消息。

        :param msg_text: 要发送的消息。
        :returns: 是否成功，成功为 True，失败为 None.
        '''
        return self.current_session.send_message(msg_text)

    def is_at_me(self, msg_text: str) -> bool:
        '''判断一条消息是否 @ 机器人。
        '''
        return self.current_session.info.nickname and '@{}'.format(self.current_session.info.nickname) in msg_text

    def trim_at_me(self, msg_text: str) -> str:
        '''去除消息中的@部分。
        '''
        return msg_text.replace('@{}'.format(self.current_session.info.nickname), '', 1).strip()

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
