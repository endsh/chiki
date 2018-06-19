# coding: utf-8
from chiki import init_uploads
from chiki.admin import Admin, ModelView, IndexView, get_static_admin
from chiki.contrib.common import Item, StatLog, TraceLog
from chiki.contrib.common import ItemView, StatLogView, TraceLogView
from chiki.contrib.users.admin import (
    UserView, WeChatUserView, QQUserView, WeiBoUser,
    UserLogView, PhoneCodeView, EmailCodeView,
)
from simple.base import db, um
from simple.config import BaseConfig, WebConfig
from simple.articles import Article, ArticleView

sync_models = []


def init(app):
    """ 初始化后台管理 """

    um.init_app(app)

    admin = Admin(
        name=BaseConfig.SITE_NAME,
        index_view=IndexView('仪表盘', menu_icon_value='diamond'),
        base_template='base.html',
    )

    admin.category_icon_classes = {
        u'运营': 'fa fa-hdd-o',
        u'日志': 'fa fa-database',
    }

    # 常用
    admin.add_view(UserView(um.models.User,             name='用户', menu_icon_value='user'))
    admin.add_view(ArticleView(Article,                 name='文章', menu_icon_value='tasks'))

    # 帐号
    admin.add_view(WeChatUserView(um.models.WeChatUser, name='微信', menu_icon_value='weixin'))
    # admin.add_view(QQUserView(um.models.QQUser,     name='QQ用户', menu_icon_value='folder'))
    # admin.add_view(WeiBoUser(um.models.WeiBoUser,   name='微博用户', menu_icon_value='folder'))

    # 日志
    admin.add_view(ItemView(Item,           name='系统选项', category='日志'))
    admin.add_view(StatLogView(StatLog,     name='统计日志', category='日志'))
    admin.add_view(TraceLogView(TraceLog,   name='跟踪日志', category='日志'))

    admin.add_view(UserLogView(um.models.UserLog,           name='用户日志', category='日志'))
    admin.add_view(PhoneCodeView(um.models.PhoneCode,       name='手机验证码', category='日志'))
    admin.add_view(EmailCodeView(um.models.EmailCode,       name='邮箱验证码', category='日志'))

    WebStaticAdmin = get_static_admin('WebStaticAdmin')
    admin.add_view(WebStaticAdmin(WebConfig.RELEASE_STATIC_FOLDER,
        'http://www.simple.com/static/', name='文件', menu_icon_value='folder'))

    admin.init_app(app)
    db.init_app(app)
    init_uploads(app)
