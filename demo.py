from YiriAir import YiriAir, Devices

if __name__ == '__main__':
    yiri = YiriAir(Devices.逍遥)
    print('初始化完成。')

    @yiri.on_message()
    def on_message(msg, title, sender):
        print('>>> ' + msg)
        if msg[:4] == '####' or yiri.is_at_me(msg):
            yiri.send_message('msg={}, title={}, sender={}'.format(msg, title, sender))
    
    yiri.run()
