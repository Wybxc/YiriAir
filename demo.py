from YiriAir import YiriAir, Devices, Sender

if __name__ == '__main__':
    yiri = YiriAir(Devices.逍遥)
    print('初始化完成。')

    @yiri.on_message()
    def on_message(msg: str, sender: Sender):
        print('>>> ' + msg)
        if yiri.is_at_me(msg) or sender.session_type == 'Private':
            yiri.send_message('msg={}, session_type={}, title={}, sender={}'
                              .format(msg, sender.session_type, sender.title, sender.sender))

    @yiri.on_message(session_type='Private')
    def on_private_message(msg: str, sender: Sender):
        yiri.send_message('收到私聊消息！')

    yiri.run()
