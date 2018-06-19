.. _common:

通用扩展
========
这里主要有短信、文件上传、 验证码、静态文件、IP处理、日志等的一些封装。

短信接口
--------
暂时只支持融联云通讯和互亿无线两种接口方式，两种都是可以通过配置设定。
目前只有通用用户模块中会使用到短信接口。发送短信请看
:func:`~chiki.sms.send_rong_sms` 及 :func:`~chiki.sms.send_ihuyi_sms`。

融联云通信的配置是这样子的::
    
    # 具体的字段情况融联云的文档，获得相应的字段进行配置即可
    SMS_RONG = dict(
        sid='sid',
        appid='appid',
        token='token',
    )

互亿无线的配置是这样子的::
    
    SMS_TPL = u'您的验证码是：%s,该验证码10分钟内有效，如非本人操作，请忽略！'
    SMS_IHUYI = dict(
        account='cf_....',
        password='....',
    )

Jinja2模版扩展
--------------
主要加了一些Filter，还有Context Processor。对Wtforms的Bootstrap
样式做了支持。

已支持的Filter有:
    - time2best: 对datetime进行人性化输出
    - time2date: 对datetime进行日期输出
    - line2br: 把\n转成<br>
    - text2html: 把\n转成<br>，并去除空行
    - kform: 对wtform进行渲染
    - kfield: 对wtform的字段进行渲染
    - kform_inline: 对wtform进行渲染，行内样式
    - kfield_inline: 对wtform的字段进行渲染，行内样式
    - alert: flash的输出或表单错误输出
    - rmb: %.2f格式化输出
    - rmb2: 先除以100, 再%.2f格式化输出

Content Processor有:
    - SITE_NAME: 网站名称，配置中的同名变量
    - VERSION: 代码版本，配置中的同名变量
    - is_ajax: ajax请求
    - current_app: current_app变量

前端支持
--------
对调试环境及生产环境下不同的前端文件支持，一般调试环境下是没有压缩
的偏源文件的静态文件，而生产环境下多为单一压缩过的文件。用法也比较简单::

    media = MediaManager(
        css=['css/web.min.css'], # 生产环境下
        cssx=[                   # 调试环境下
            'bower_components/weui/dist/style/weui.css',
            'node_modules/jquery-weui/dist/css/jquery-weui.css',
            'bower_components/bxslider-4/dist/jquery.bxslider.min.css',
            'dist/css/web.css'
        ],
        js=['js/web.min.js'],
        jsx=[
            'bower_components/jquery/dist/jquery.js',
            'bower_components/jquery-form/jquery.form.js',
            'bower_components/jquery-tmpl/jquery.tmpl.js',
            'bower_components/bxslider-4/dist/jquery.bxslider.min.js',
            'node_modules/jquery-weui/dist/js/jquery-weui.js',
            'dist/js/web.js',
        ],
    )
    media.init_app(app)

上面是对文件进行配置，文件路径想对于配置中的STATIC_FOLDER，然后就是在模板中
进行渲染输出::

    {% block static_header %}{{ static_header() }}{% endblock %}
    {% block static_ie8 %}{{ static_ie8() }}{% endblock %}

这样就会生成对应的HTML，如生产环境的例子::

    <link rel="stylesheet" href="/static/css/web.min.css?v=b450">
    <script src="/static/js/web.min.js?v=84c9"></script>
    <!--[if lt IE 9]>
    <script src="ie8.min.js"></script>
    <![endif]-->

此扩展还可支持多组静态文件的使用方式::

    media = MediaManager(
        default=dict(
            css=['css/web.min.css'],
            cssx=[
                'libs/bootstrap/css/bootstrap.css',
                'dist/css/web.css'
            ],
            js=['js/web.min.js'],
            jsx=[
                'bower_components/jquery/dist/jquery.js',
                'bower_components/jquery-form/jquery.form.js',
                'bower_components/jquery-tmpl/jquery.tmpl.js',
                'libs/bootstrap/js/bootstrap.js',
                'libs/area.js',
                'dist/js/web.js'
            ],
        ),
        weui=dict(
            css=['css/weui.min.css'],
            cssx=[
                'bower_components/weui/dist/style/weui.css',
                'node_modules/jquery-weui/dist/css/jquery-weui.css',
                'dist/css/weui.css',
            ],
            js=['js/weui.min.js'],
            jsx=[
                'bower_components/jquery/dist/jquery.js',
                'node_modules/jquery-weui/dist/js/jquery-weui.js',
                'libs/area.js',
                'dist/js/weui.js',
            ],
        ),
    )

模板1中使用default的文件::
    
    {% block static_header %}{{ static_header() }}{% endblock %}

模板2中使用weui的文件::
    
    {% block static_header %}{{ static_header('weui') }}{% endblock %}

日志扩展
--------
日志扩展支持邮件报错提醒，只需配置文件中加入以下配置即可(一般生产环境下才需要),
相应的实现在 :class:`~chiki.logger.Logger` 中::

    LOGGING = {
        'SMTP': {                               # SMTP 邮件发送日志
            'HOST': 'smtp.mxhichina.com',
            'TOADDRS': ['438985635@qq.com', ],
            'SUBJECT': u'admin 出错了 :-(',
            'USER': 'pms@haoku.net',
            'PASSWORD': '...',
        },
        'FILE': {                               # 本地日志
            'PATH': os.path.join(BaseConfig.LOG_FOLDER, 'admin.log'),
            'MAX_BYTES': 1024 * 1024 * 10,
            'BACKUP_COUNT': 5,
        }
    }

    # 写日志
    current_app.logger.error('测试错误')

文件存储扩展
------------
当本地存储文件时，需要提供本地文件/图片链接可访问支持::

    # UPLOADS 默认会被支持，其他的需要自己手动添加
    from chiki.uploads import init_uploads
    init_uploads(app, config='UPLOADS2')

图片验证码
----------
默认被支持，在表单扩展中被使用。请看:class:`~chiki.forms.VerifyCodeField`
及 `chiki.verify`。

IP工具
------
将IP地址转换为所在地及运营商，主要在后台管理中用到。这里需要涉及到
另外一个项目，等我有空，我会把它开源到github。
