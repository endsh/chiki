.. _projection:

项目结构
========

chiki的设计主要是为了同时支持移动应用接口与网站开发。由cookiecutter-chiki生成的
项目有比较固定的目录结构及应用结构。运行入口文件是manage.py，主要包含了服务器运行、
数据处理服务等。

目录结构
--------

一般的目录结构是这样的::

    ├── data                        # 数据
    ├── docs                        # 文档目录
    ├── logs                        # 日志目录
    ├── deploy                      # 部署
    │   ├── etc                     # 配置文件
    │   │   ├── admin.cfg           # flask 生产环境下的配置
    │   │   ├── uwsgi.admin.ini     # uwsgi 配置文件
    │   │   └── ...
    │   ├── files
    │   │   ├── bash_profile        # bash 环境变量等
    │   │   ├── id_rsa              # 用于git同步的密钥
    │   │   ├── id_rsa.pub
    │   │   └── pip.conf            # 使用国内的pip源
    │   ├── nginx
    │   │   └── simple.nginx.conf   # nginx配置文件
    │   └── fabfile.py              # fab管理文件
    ├── simple                      # 程序主目录
    │   ├── __init__.py             # 后台、接口、网站总入口
    │   ├── admin                   # 后台入口模块
    │   │   └── __init__.py
    │   ├── api.py                  # 接口入口模块
    │   ├── web.py                  # 网站入口模块
    │   ├── base.py                 # 全局变量等
    │   ├── config.py               # 默认配置
    │   ├── const.py                # 接口错误码定义
    │   ├── utils.py                # 工具函数
    │   ├── services                # 数据处理服务
    │   └── articles                # 业务模块
    │       ├── __init__.py
    │       ├── admin.py            # 后台管理视图
    │       ├── apis.py             # 业务接口
    │       ├── models.py           # 数据模型
    │       ├── forms.py            # 表单模型
    │       ├── helpers.py          # 工具函数
    │       ├── pages.py            # 移动内嵌页
    │       └── views.py            # 网页蓝图
    ├── media
    │   ├── admin                   # 后台 - 前端文件
    │   ├── api                     # 内嵌页 - 前端文件
    │   └── web                     # 网站 - 前端文件
    │       ├── dist                # 发行目录
    │       ├── grunt
    │       ├── Gruntfile.js
    │       ├── img                 # 图片
    │       ├── libs                # 手动前端库
    │       ├── package.json
    │       ├── readme.md
    │       ├── bower.json          # bower依赖
    │       ├── src                 # 前端源码
    │       │   ├── js
    │       │   │   └── web.js
    │       │   └── less
    │       │       └── web.less
    │       └── web.json
    ├── templates                   # 模版目录
    │   ├── admin
    │   ├── api
    │   └── web
    ├── requirements                # 虚拟环境依赖
    │   ├── dev.txt
    │   └── prod.txt
    ├── requirements.txt
    ├── manage.py                   # 管理入口
    ├── tests                       # 自动测试
    └── wsgi                        # uwsgi 入口
        ├── __init__.py
        ├── admin.py
        ├── api.py
        └── web.py

应用结构
--------

chiki把一个项目规定为3个程序admin/api/web，即后台/接口/网站。通常发布版会部署为三个域名：
admin.example.com,api.example.com,www.example.com 。对应有程序主目录下的
admin.py/api.py/web.py 三个程序入口文件，manage.py的三个运行命令::

    python manage.py admin -d -r  // 后台管理服务器
    python manage.py api -d -r    // 移动接口(rest)服务器
    python manage.py web -d -r    // 网站服务器

以上这些均可由模版生成，实际开发过程只需添加业务模块，如::
    
    └── articles                # 业务模块
        ├── __init__.py
        ├── admin.py            # 后台管理视图
        ├── apis.py             # 业务接口
        ├── models.py           # 数据模型
        ├── forms.py            # 表单模型
        ├── helpers.py          # 工具函数
        ├── pages.py            # 移动内嵌页
        └── views.py            # 网页蓝图

相应的在入口文件admin.py/api.py/web.py导入业务模块即可。

项目配置
--------

在config.py文件下一般会有4个类：`BaseConfig`、`AdminConfig`、`ApiConfig`、`WebConfig`。
`BaseConfig`为基础配置，其他类均继承于此，对应的为admin/api/web三个程序的默认配置，
主要在程序主目录 `__init__.py` 中被引用。下面对一些常用的配置项做一点介绍::

    class BaseConfig(object):
        """ 基础配置 """

        # 目录, i18n
        ROOT_FOLDER = os.path.dirname(                          # 根目录
            os.path.dirname(os.path.abspath(__file__)))
        DATA_FOLDER = os.path.join(ROOT_FOLDER, 'data')         # 数据
        DOC_FOLDER = os.path.join(ROOT_FOLDER, 'docs')          # 文档
        LOG_FOLDER = os.path.join(ROOT_FOLDER, 'logs')          # 日志
        STATIC_FOLDER = os.path.join(ROOT_FOLDER, 'media')      # 前端
        TEMPLATE_FOLDER = os.path.join(ROOT_FOLDER, 'templates') # 模版
        BABEL_DEFAULT_LOCALE = 'zh_CN'                          # i18n
        CHANGE_400_TO_200 = True                    # abort 400 to 200

        # 密码等安全密钥
        SECRET_KEY = 'SECRET KEY'
        PASSWORD_SECRET = 'PASSWORD SECRET'
        WTF_CSRF_SECRET_KEY = 'WTF CSRF SECRET KEY'

        # 数据库配置
        MONGODB_SETTINGS = dict(
            host='127.0.0.1',
            port=27017,
            db='chiki',
        )

        # redis 配置，按需
        REDIS = dict(host='127.0.0.1', port=6379,
            db=0, prefix='chiki', expire=7 * 86400)

        # 文件存储配置
        UPLOADS = dict(
            type='local', 
            link='/uploads/%s', 
            path=os.path.join(DATA_FOLDER, 'uploads'),
        )

        # 版本，网站名称等
        VERSION = '0.1.0'
        SITE_NAME = u'Chiki'


    class AdminConfig(BaseConfig):
        """ 后台管理通用配置 """

        PORT = 5000                                     # 监听端口
        ENVVAR = 'SIMPLE_ADMIN'                       # 环境变量
        SESSION_COOKIE_NAME = 'coolnote.admin'          # session key
        STATIC_FOLDER = os.path.join(                   # 前端目录
            BaseConfig.STATIC_FOLDER, 'admin')
        RELEASE_STATIC_FOLDER = os.path.join(           # 发行版前端目录
            BaseConfig.STATIC_FOLDER, 'admin/dist')
        TEMPLATE_FOLDER = os.path.join(                 # 模版目录
            BaseConfig.TEMPLATE_FOLDER, 'admin')

        INDEX_REDIRECT = '/admin/'                      # 首页重定向

        # 后台管理员帐号密码
        ADMIN_USERNAME = 'admin'
        ADMIN_PASSWORD = ''

上面的ENVVAR结合deploy/files/bash_profile找到相应的配置文件::
    
    export SIMPLE_ADMIN="/home/simple/simple/etc/admin.cfg"

即deploy/etc/admin.cfg文件(部署环境的额外配置)::

    # coding: utf-8
    import os
    from simple.config import BaseConfig

    # 日志配置，支持邮箱报错
    LOGGING = {
        'SMTP': {
            'HOST': 'smtp.mxhichina.com',
            'TOADDRS': [
                '438985635@qq.com', 
            ],
            'SUBJECT': u'chiki admin 出错了 :-(',
            'USER': 'pms@haoku.net',
            'PASSWORD': '',
        },
        'FILE': {
            'PATH': os.path.join(BaseConfig.LOG_FOLDER, 'admin.log'),
            'MAX_BYTES': 1024 * 1024 * 10,
            'BACKUP_COUNT': 5,
        }
    }

    # 文件存储 - 阿里云
    UPLOADS = dict(
        host='oss-cn-shenzhen-internal.aliyuncs.com',
        access_id='',
        secret_access_key='',
        link='http://cdn2.haoku.net/%s',
        bucket='hkcdn2',
        prefix='chiki/',
        type='oss',
    )

运行管理
--------

服务器运行::

    python manage.py admin -d -r  // 后台管理服务器
    python manage.py api -d -r    // 移动接口(rest)服务器
    python manage.py web -d -r    // 网站服务器

服务运行(services下创建name.py)::
    
    python manage.py service name

services下创建name.py例子::
    
    # coding: utf-8

    def run():
        print 'hello, service!'
