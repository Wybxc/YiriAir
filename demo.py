from YiriAir import YiriAir, Devices

if __name__ == '__main__':
    yiri = YiriAir(Devices.XIAO_YAO)
    print('初始化完成。')

    @yiri.on_message()
    def on_message(msg, title, sender):
        print(f'>>> {msg}')
        if msg[:4] == '####':
            yiri.send_message(f'msg={msg}, title={title}, sender={sender}')
    
    yiri.run()
