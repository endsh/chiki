# coding: utf-8
import sys
sys.path.append('../..')

import os
from chiki import init_admin
from chiki.base import db
from chiki.admin import Admin
from chiki.contrib.common import Item, StatLog, TraceLog
from chiki.contrib.common import ItemView, StatLogView, TraceLogView
from chiki.contrib.users import UserManager
from chiki.contrib.users.admin import (
    UserView, WeChatUserView, QQUserView, WeiBoUser,
    UserLogView, PhoneCodeView, EmailCodeView,
)


class Config(object):
    # 目录, i18n
    ROOT_FOLDER = os.path.abspath('.')
    STATIC_FOLDER = os.path.join(ROOT_FOLDER, 'media/admin')
    TEMPLATE_FOLDER = os.path.join(ROOT_FOLDER, 'templates/admin')

    INDEX_REDIRECT = '/admin/user'
    MONGODB_SETTINGS = dict(host='127.0.0.1', port=27017, db='chiki_users')
    
    SECRET_KEY = 'SECRET KEY'
    PASSWORD_SECRET = 'PASSWORD SECRET'
    WTF_CSRF_SECRET_KEY = 'WTF CSRF SECRET KEY'


def init(app):
    um = UserManager(app)
    db.init_app(app)
    admin = Admin(name='Chiki', base_template='base.html')

    admin.category_icon_classes = {
        u'运营': 'fa fa-hdd-o',
        u'日志': 'fa fa-database',
    }

    admin.add_view(UserView(um.models.User, name='用户'))
    admin.add_view(WeChatUserView(um.models.WeChatUser, name='微信用户'))
    admin.add_view(QQUserView(um.models.QQUser, name='QQ用户'))
    admin.add_view(WeiBoUser(um.models.WeiBoUser, name='微博用户'))

    # 日志
    admin.add_view(ItemView(Item,           name='系统选项', category='日志'))
    admin.add_view(StatLogView(StatLog,     name='统计日志', category='日志'))
    admin.add_view(TraceLogView(TraceLog,   name='跟踪日志', category='日志'))

    admin.add_view(UserLogView(um.models.UserLog,           name='用户日志', category='日志'))
    admin.add_view(PhoneCodeView(um.models.PhoneCode,       name='手机验证码', category='日志'))
    admin.add_view(EmailCodeView(um.models.EmailCode,       name='邮箱验证码', category='日志'))

    admin.init_app(app)


app = init_admin(init, Config, template_folder=Config.TEMPLATE_FOLDER)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
