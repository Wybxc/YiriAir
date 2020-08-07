# -*- encoding=utf8 -*-

import time
from .driver import PocoDriver, Session


class YiriAir():
    def __init__(self, device, query_interval=1):
        self.driver = PocoDriver(device)
        self.current_session = Session(self.driver)
        self.query_interval = query_interval
        self.message_hooks = []

    def on_message(self):
        def decorator(func):
            def decorated(message, title):
                return func(message, title)
            self.message_hooks.append(decorated)
            return decorated
        return decorator

    def send_message(self, msg_text):
        return self.current_session.send_message(msg_text)

    def run(self):
        while True:
            messages = self.current_session.check_latest_message()
            for msg in messages:
                for hook in self.message_hooks:
                    hook(msg, self.current_session.title)
            self.current_session = self.current_session.jump_to_new_session()
            time.sleep(self.query_interval)
