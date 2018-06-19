# coding: utf-8
import sys
sys.path.append('../..')

import os
from chiki import MediaManager, init_uploads, init_web
from chiki.base import db
from chiki.api import wapi
from chiki.contrib.users import UserManager
from flask import redirect
from flask.ext.login import login_user, login_required

media = MediaManager(
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
        'dist/js/web.js'
    ],
)


class Config(object):

    # 目录, i18n
    ROOT_FOLDER = os.path.abspath('.')
    STATIC_FOLDER = os.path.join(ROOT_FOLDER, 'media/web')
    TEMPLATE_FOLDER = os.path.join(ROOT_FOLDER, 'templates/web')

    MONGODB_SETTINGS = dict(host='127.0.0.1', port=27017, db='chiki_users')

    SECRET_KEY = 'SECRET KEY'
    PASSWORD_SECRET = 'PASSWORD SECRET'
    WTF_CSRF_SECRET_KEY = 'WTF CSRF SECRET KEY'

    SITE_NAME = u'酷记事'
    SERVICE_EMAIL = ''

    MAIL_SERVER = ''
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = ''

    CHIKI_USER = dict(
        allow_phone=True,
        login_next='/users/abc',
    )

    WXAUTH = dict(
        qrcode=dict(
            appid='',
            secret='',
        )
    )


def init(app):
    db.init_app(app)
    user = UserManager(app)
    user.init_wapis(wapi)
    user.init_web()
    wapi.init_app(app)
    media.init_app(app)

    @app.route('/test')
    def test():
        u = user.models.WeChatUser.objects(unionid='1212').first()
        if not u:
            u = user.models.WeChatUser(unionid='1212').save()
        login_user(u)
        return redirect(user.config.bind_url)


    @app.route('/')
    @login_required
    def index():
        return '123'


app = init_web(init, Config, template_folder=Config.TEMPLATE_FOLDER)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
