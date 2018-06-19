
Simple
===============================

Simple web project based on chiki.

使用入门
--------

运行后台管理::

    python manage.py admin -d -r
运行接口程序::
    
    python manage.py api -d -r
运行 Web 程序::

    python manage.py web -d -r

目录详解
--------
    
::

    ├── simple # 程序目录
    │   ├── admin
    │   │   └── __init__.py
    │   ├── api.py
    │   ├── base.py
    │   ├── config.py
    │   ├── const.py
    │   ├── __init__.py
    │   └── web.py
    ├── data                # 数据
    ├── deploy              # 项目部署
    │   ├── etc
    │   ├── files
    │   ├── nginx
    │   └── fabfile.py      # 部署脚本
    ├── docs                # 文档目录
    ├── media               # 静态文件
    ├── templates           # 模板
    ├── requirements        # python 依赖
    │   ├── dev.txt         # 开发环境
    │   └── prod.txt        # 生产环境
    ├── requirements.txt
    ├── tests               # 测试
    ├── CHANGES             # 更新日志
    ├── TODO                # 开发计划
    ├── manage.py           # 管理脚本
    ├── wsgi.py             # 用于 uwsgi 使用的脚本
    └── README.md           # 项目简介


程序部署
--------

在目录deploy下，第一次部署::
    
    fab deploy:true

更新代码，并重启服务器::
    
    fab update && fab uwsgi_reload


自动测试
--------

运行所有的测试::
    
    python manage.py test