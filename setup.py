# -*- encoding=utf8 -*-

from setuptools import setup, find_packages

setup(
    name='YiriAir',
    version='0.0.3.1',
    description=(
        '基于安卓模拟器和 UI 控件搜索的 QQ 消息自动收发框架。'
    ),
    long_description=open('README.rst', encoding='utf-8').read(),
    author='wybxc',
    author_email='wybxc@qq.com',
    license='AGPL-3.0 License',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/Wybxc/YiriAir',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=[
        'airtest>=1.1.1',
        'pocoui>=1.0.78',
    ]
)
