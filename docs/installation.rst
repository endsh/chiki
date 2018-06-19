.. _installation:

安装
====

chiki暂时只能通过clone github上的代码，然后运行``python setup.py install``
进行安装。怎么提交到pypi上，我暂时还没了解怎么弄。

virtualenv虚拟环境
------------------

virtualenv+virtualenvwrapper是一个很流行的工具，可以用来隔离不同项目依赖的库环境。
ubuntu下可以运行安装::

    sudo apt-get install python-virtualenv virtualenvwrapper -y

virtualenvwrapper有几个常用的命令::

    mkvirtualenv name // 创建名字为name虚拟环境
    workon name       // 切换到name虚拟环境下
    deactivate        // 退出虚拟环境

在虚拟环境下，python、pip、还有其他的libs都是使用虚拟环境所安装的版本。virtualenv
安装目录在/home/user/.virtualenvs下。

pip 安装
--------

通过pip安装::
    
    pip install chiki

克隆 & 安装
-----------

从github克隆并安装chiki框架，chiki依赖安装的只有部分lib，还有一些欠缺的需要自己手动安装，
因为部分扩展不一定会被用到，可能需要注意的是flask-admin也需要自己手动克隆安装
(python setup.py install)，因为需要支持中文::

    git clone https://github.com/endsh/chiki.git chiki
    cd chiki && python setup.py install

使用项目模版
------------

chiki还有一个项目模版 `CookieCutter Chiki`_ ，安装了chiki后，运行以下命令即可
生成一个新的空项目::

    chiki https://github.com/endsh/cookiecutter-chiki.git -a -w

这里给一运行的例子::
    
    author [linshao]: author                    // 作者
    email [438985635@qq.com]: name@email.com    // 邮箱
    name [simple]: simple                       // 项目名称
    site_name [simple]: 网站名称                  // 网站名称
    project_name [Simple]: Simple               // 项目全名
    project_short_description [...]:            // 一句话简介
    version [0.1.0]:                            // 版本
    log_email_user [pms@haoku.net]:             // 报错邮箱
    log_email_password []:                      // smtp密码
    admin_host [admin.simple.com]:              // 后台host
    api_host [api.simple.com]:                  // 接口host
    web_host [www.simple.com]:                  // 网站host
    port [5000]:                                // 运行端口
    has_api [True]:                             // 接口应用
    has_web [True]:                             // 网站应用
    today [2016-02-12]:                         // 创建日期

以上的字段都是必须输入的，直接回车使用默认值，这些变量用于渲染项目模版。


.. _CookieCutter Chiki: https://github.com/endsh/cookiecutter-chiki
