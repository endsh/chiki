Chiki - 基于Flask的应用层框架
=================================

Chiki是一个基于Flask的应用层框架。这是一个广州小酷科技内部基于10多个
Web项目积累产出的一个框架，主要目的是提高开发效率，固化通用的模块。

Chiki框架主要采用Flask扩展的设计方式，即单个模块可用也可不用。
目前主要包含了后台管理(flask-amdin)的一些扩展，接口(flask-restful)
的一些扩展，还有wtforms,mongoengine,jinja2等的一些扩展，还有数据统计，短信、文件上传、
验证码、静态文件、IP处理、日志等的一些封装，以及内置通用模块、用户模块、第三方登录
集成、微信公众平台等相关支持。

Chiki相关的还有一个项目模版 `CookieCutter Chiki`_ 。使用该模版生成项目，即可直接
支持自动化部署(nginx+uwsgi+fabric)、gitlab项目同步、服务器简单管理、前端优化
(grunt+bower)。

注意：Chiki主要采用mongodb数据库，SQLAlchemy支持较少，需要的话自己做支持。mongodb
使用起来比mysql等其他数据库，简单得多，不需要建表就可以直接用。

相关链接
--------
- 文档地址: http://www.chiki.org/
- 后台Demo: http://demo.chiki.org/
- Chiki交流群(QQ): 144782626

关于作者
--------
- 老龄菜鸟程序员一个
- 19岁开始入门计算机编程
- 喜欢长跑、TVB电视剧、电影
- 喜欢一个人发呆、冥想
- 喜欢创业
- QQ: 438985635
- 微信: Tinysh
- 博客: http://yaosimin.com/


.. _CookieCutter Chiki: https://github.com/endsh/cookiecutter-chiki