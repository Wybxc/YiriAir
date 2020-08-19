from YiriAir import YiriAir, Devices, Sender

if __name__ == '__main__':
    yiri = YiriAir(Devices.逍遥)
    print('初始化完成。')

    b2x = lambda bs: ''.join(['%X ' % ord(b) for b in bs])

    @yiri.on_message()
    def on_message(msg: str, sender: Sender):
        print('>>> ' + msg)
        if yiri.is_at_me(msg) or sender.session_type == 'Private':
            yiri.send_message('msg={}, session_type={}, title={}, sender={}'
                              .format(msg, sender.session_type, sender.title, sender.sender))

    yiri.run()
