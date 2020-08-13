# -*- encoding=utf8 -*-

import time
from .driver import PocoDriver, Session, logger_yiri


class YiriAir():
    def __init__(self, device, query_interval=1):
        self.driver = PocoDriver(device)
        self.current_session = Session(self.driver)
        self.query_interval = query_interval
        self.message_hooks = []

    def on_message(self, message_type='Text'):
        def decorator(func):
            def decorated(message, title):
                txt, msg_type, sender = message
                if msg_type == message_type:
                    return func(txt, title, sender)
            self.message_hooks.append(decorated)
            return decorated
        return decorator

    def send_message(self, msg_text):
        return self.current_session.send_message(msg_text)

    def run(self):
        while True:
            try:
                messages = self.current_session.check_latest_message()
                for msg in messages:
                    for hook in self.message_hooks:
                        hook(msg, self.current_session.title)
                self.current_session = self.current_session.jump_to_new_session()
            except RpcRemoteException as e:
                logger_yiri.error(e)
                self.current_session.normalize_qqlite()
            time.sleep(self.query_interval)
