# YiriAir
YiriAir是一款基于**安卓模拟器**和<strong>Airtest（Poco）</strong>的QQ消息自动收发框架。
在目前第三方协议基本不可用的状况下，这是较为可行的替代方案之一。

YiriAir 正在开发中，文档待完善。


## 安装
本项目已在 PyPI 上发布：
```
pip install YiriAir
```


## 使用
YiriAir需要在安卓模拟器上运行**QQ极速版**，经个人测试，表现较好的模拟器是逍遥模拟器。*（如果有闲置的安卓手机，也可以用真机代替模拟器。）*

使用的模拟器或真机需要打开**USB调试**。在模拟器上运行QQ极速版之后，需要在运行框架之前提前登录QQ账号，确保每次开启应用时都是已登录状态。此外，还需要在设置中打开**回车键发送消息**，并且需要保证QQ每次启动后**消息列表非空**。*（可能会在之后的版本中优化）*

以下是使用样例：
```Python
from YiriAir import YiriAir, Devices, Sender

if __name__ == '__main__':
    yiri = YiriAir(Devices.逍遥) # 使用逍遥模拟器    

    @yiri.on_message(session_type='Private') # 只接收私聊消息
    def on_message(msg: str, sender: Sender): # msg 是消息内容，sender 是消息来源
        print('>>> ' + msg)
        yiri.send_message('Hello World!')

    yiri.run()
```

`YiriAir`是框架的主要类，有一个初始化参数`device`，这个参数表示要连接的模拟器的地址（关于地址的格式，参看[这里](https://juejin.im/post/6844904118809526279)），在`Devices`中有一些可用的常量定义。

`YiriAir.on_message`是一个装饰器，可以注册处理消息的函数。

`YiriAir.send_message`是发送消息的方法。由于技术限制，目前仅支持向当前对话发送消息。

`YiriAir.run`是主循环，无限循环处理消息，必须在最后调用。


## 开源许可证
Airtest 版权归网易有限公司所有，本项目其他代码遵守：

GNU AFFERO GENERAL PUBLIC LICENSE version 3

其中部分要求:

- (见 LICENSE 第 13 节) 尽管本许可协议有其他规定，但如果您修改本程序，则修改后的版本必须显着地为所有通过计算机网络与它进行远程交互的用户（如果您的版本支持这种交互）提供从网络服务器通过一些标准或惯用的软件复制方法**免费**访问相应的**源代码**的机会。
- (见 LICENSE 第 4 节) 您可以免费或收费地传递这个项目的源代码或目标代码(即编译结果)，但前提是**提供明显的版权声明**（您需要标注本 GitHub 项目地址）。


## 支持
本项目仍在开发阶段。如有问题，欢迎[提出Issue](https://github.com/Wybxc/YiriAir/issues/new/choose)。