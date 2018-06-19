# coding: utf-8
import sys
sys.path.append('../../..')

import pytest
import os
import json
from mongoengine.connection import connect
from chiki import init_api
from chiki.base import db
from chiki.api import api
from chiki.contrib.users import UserManager, um
from flask.ext.login import login_user


class Config(object):
    DEBUG = True
    TESTING = True
    MONGODB_SETTINGS = dict(host='127.0.0.1', port=27017, db='chiki_users')
    SECRET_KEY = 'SECRET KEY'
    PASSWORD_SECRET = 'PASSWORD SECRET'
    WTF_CSRF_SECRET_KEY = 'WTF CSRF SECRET KEY'
    LOGIN_DISABLED = False


def init(app):
    um = UserManager(app)
    db.init_app(app)
    um.init_apis(api)
    api.init_app(app)


def create_api():
    return init_api(init, Config)


@pytest.fixture
def client(request):
    app = create_api()
    client = app.test_client()
    dbname = app.config.get('MONGODB_SETTINGS').get('db')

    conn = db.connect(**app.config.get('MONGODB_SETTINGS'))
    conn.drop_database(dbname)


    @app.route('/chiki/create_wechat_user')
    def chiki_create_wechat_user():
        user = um.models.WeChatUser().save()
        login_user(user)
        return ''

    def teardown():
        # conn = connect()
        # conn.drop_database(db)
        pass

    request.addfinalizer(teardown)

    return client


def get_data(data):
    obj = json.loads(data)
    if 'data' in obj:
        return obj['data']


def send_phone_code(client, phone, action=None, key='SUCCESS'):
    um = client.application.user_manager
    action = um.models.PhoneCode.ACTION_REGISTER if not action else action
    rv = client.post('/users/sendcode/phone?action=%s' % action, data=dict(phone=phone))
    assert key in rv.data
    return get_data(rv.data)


def auth_phone_code(client, phone, authcode, action=None, key='SUCCESS'):
    um = client.application.user_manager
    action = um.models.PhoneCode.ACTION_REGISTER if not action else action
    rv = client.post('/users/authcode/phone?action=%s' % action, data=dict(phone=phone, authcode=authcode))
    assert key in rv.data
    return get_data(rv.data)


def register_phone(client, phone, password, authcode, key='SUCCESS'):
    data = dict(phone=phone, password=password, authcode=authcode)
    rv = client.post('/users/register/phone', data=data)
    assert key in rv.data
    return get_data(rv.data)


def send_email_code(client, email, action=None, key='SUCCESS'):
    """ 发送验证码 """
    um = client.application.user_manager
    action = um.models.EmailCode.ACTION_REGISTER if not action else action
    rv = client.post('/users/sendcode/email?action=%s' % action, data=dict(email=email))
    assert key in rv.data
    return get_data(rv.data)


def auth_email_code(client, email, authcode, action=None, key='SUCCESS'):
    um = client.application.user_manager
    action = um.models.EmailCode.ACTION_REGISTER if not action else action
    rv = client.post('/users/authcode/email?action=%s' % action, data=dict(email=email, authcode=authcode))
    assert key in rv.data
    return get_data(rv.data)


def register_email(client, email, password, authcode, key='SUCCESS'):
    data = dict(email=email, password=password, authcode=authcode)
    rv = client.post('/users/register/email', data=data)
    assert key in rv.data
    return get_data(rv.data)


def login(client, account, password, key='SUCCESS'):
    rv = client.post('/users/login', data=dict(account=account, password=password))
    assert key in rv.data
    return get_data(rv.data)


def logout(client, key='SUCCESS'):
    rv = client.post('/users/logout')
    assert key in rv.data
    return get_data(rv.data)


def reset_password_phone(client, phone, password, authcode, key='SUCCESS'):
    data = dict(phone=phone, password=password, authcode=authcode)
    rv = client.post('/users/reset_password/phone', data=data)
    assert key in rv.data
    return get_data(rv.data)


def reset_password_email(client, email, password, authcode, key='SUCCESS'):
    data = dict(email=email, password=password, authcode=authcode)
    rv = client.post('/users/reset_password/email', data=data)
    assert key in rv.data
    return get_data(rv.data)


def get_userinfo(client, key='SUCCESS'):
    rv = client.get('/u')
    if key == 'SUCCESS':
        assert key in rv.data
        return get_data(rv.data)
    else:
        assert '/users/login' in rv.data


def create_wechat_user(client):
    client.get('/chiki/create_wechat_user')


def bind_phone(client, phone, password, authcode, key='SUCCESS'):
    data = dict(phone=phone, password=password, authcode=authcode)
    rv = client.post('/u/bind/phone', data=data)
    assert key in rv.data
    return get_data(rv.data)


def bind_email(client, email, password, authcode, key='SUCCESS'):
    data = dict(email=email, password=password, authcode=authcode)
    rv = client.post('/u/bind/email', data=data)
    assert key in rv.data
    return get_data(rv.data)


def do_phone(client):
    um = client.application.user_manager
    PhoneCode = um.models.PhoneCode
    phone = '13800138000'
    phone2 = '138001380001'
    phone3 = '13800138001'
    password = '123456'
    password2 = '123457'

    # 发送手机验证码
    send_phone_code(client, phone2, key='PHONE_FORMAT_ERROR')
    send_phone_code(client, phone, action='123', key='ACCESS_DENIED')
    send_phone_code(client, phone)
    send_phone_code(client, phone, key='PHONE_CODE_TIME_LIMIT')
    send_phone_code(client, phone, action=PhoneCode.ACTION_RESET_PASSWORD, key='PHONE_UNREGISTERED')

    # 验证手机验证码
    code = PhoneCode.objects(action=PhoneCode.ACTION_REGISTER, phone=phone).first()
    assert code is not None
    send_phone_code(client, phone2, key='PHONE_FORMAT_ERROR')
    send_phone_code(client, phone, action='123', key='ACCESS_DENIED')
    auth_phone_code(client, phone, authcode=code.code)
    for _ in range(10):
        auth_phone_code(client, phone, authcode=0, key='PHONE_CODE_ERROR')
    auth_phone_code(client, phone, authcode=code.code, key='PHONE_CODE_ERROR')

    # 用户手机注册
    code.delete()
    send_phone_code(client, phone)
    code = PhoneCode.objects(action=PhoneCode.ACTION_REGISTER, phone=phone).first()
    assert code is not None
    register_phone(client, phone, password, code.code)
    get_userinfo(client)
    logout(client)
    register_phone(client, phone, password, code.code, key='PHONE_EXISTS')
    code.delete()
    send_phone_code(client, phone, key='PHONE_REGISTERED')

    # 用户手机登录
    get_userinfo(client, key='LOGIN_REQUIRED')
    login(client, phone2, password, key='ACCOUNT_NOT_EXISTS')
    login(client, phone, password)
    get_userinfo(client)
    logout(client)

    # 登录错误锁住帐号
    get_userinfo(client, key='LOGIN_REQUIRED')
    for _ in range(10):
        login(client, phone, password2, key='PASSWORD_ERROR')
    login(client, phone, password, key='ACCOUNT_LOCKED')

    # 重置密码
    send_phone_code(client, phone, action=PhoneCode.ACTION_RESET_PASSWORD)
    code = PhoneCode.objects(action=PhoneCode.ACTION_RESET_PASSWORD, phone=phone).first()
    assert code is not None
    reset_password_phone(client, phone, password2, code.code)
    get_userinfo(client)
    logout(client)
    login(client, phone, password2)
    get_userinfo(client)
    logout(client)

    # 微信绑定
    create_wechat_user(client)
    send_phone_code(client, phone, action=PhoneCode.ACTION_BIND)
    code = PhoneCode.objects(action=PhoneCode.ACTION_BIND, phone=phone).first()
    assert code is not None
    bind_phone(client, phone, password2, code.code)
    get_userinfo(client)

    create_wechat_user(client)
    send_phone_code(client, phone3, action=PhoneCode.ACTION_BIND)
    code = PhoneCode.objects(action=PhoneCode.ACTION_BIND, phone=phone3).first()
    assert code is not None
    bind_phone(client, phone3, password2, code.code)
    get_userinfo(client)
    logout(client)


def do_email(client):
    # 邮箱
    um = client.application.user_manager
    EmailCode = um.models.EmailCode
    email = '438985635@qq.com'
    email2 = '1380'
    email3 = '438985636@qq.com'
    password = '123456'
    password2 = '123457'

    # 发送手机验证码
    send_email_code(client, email2, key='EMAIL_FORMAT_ERROR')
    send_email_code(client, email, action='123', key='ACCESS_DENIED')
    send_email_code(client, email)
    send_email_code(client, email, key='EMAIL_CODE_TIME_LIMIT')
    send_email_code(client, email, action=EmailCode.ACTION_RESET_PASSWORD, key='EMAIL_UNREGISTERED')

    # 验证手机验证码
    code = EmailCode.objects(action=EmailCode.ACTION_REGISTER, email=email).first()
    assert code is not None
    send_email_code(client, email2, key='EMAIL_FORMAT_ERROR')
    send_email_code(client, email, action='123', key='ACCESS_DENIED')
    auth_email_code(client, email, authcode=code.code)
    for _ in range(10):
        auth_email_code(client, email, authcode=0, key='EMAIL_CODE_ERROR')
    auth_email_code(client, email, authcode=code.code, key='EMAIL_CODE_ERROR')

    # 用户手机注册
    code.delete()
    send_email_code(client, email)
    code = EmailCode.objects(action=EmailCode.ACTION_REGISTER, email=email).first()
    assert code is not None
    register_email(client, email, password, code.code)
    get_userinfo(client)
    logout(client)
    register_email(client, email, password, code.code, key='EMAIL_EXISTS')
    code.delete()
    send_email_code(client, email, key='EMAIL_REGISTERED')

    # 用户手机登录
    get_userinfo(client, key='LOGIN_REQUIRED')
    login(client, email2, password, key='ACCOUNT_NOT_EXISTS')
    login(client, email, password)
    get_userinfo(client)
    logout(client)

    # 登录错误锁住帐号
    get_userinfo(client, key='LOGIN_REQUIRED')
    for _ in range(10):
        login(client, email, password2, key='PASSWORD_ERROR')
    login(client, email, password, key='ACCOUNT_LOCKED')

    # 重置密码
    send_email_code(client, email, action=EmailCode.ACTION_RESET_PASSWORD)
    code = EmailCode.objects(action=EmailCode.ACTION_RESET_PASSWORD, email=email).first()
    assert code is not None
    reset_password_email(client, email, password2, code.code)
    get_userinfo(client)
    logout(client)
    login(client, email, password2)
    get_userinfo(client)
    logout(client)

    # 微信绑定
    create_wechat_user(client)
    send_email_code(client, email, action=EmailCode.ACTION_BIND)
    code = EmailCode.objects(action=EmailCode.ACTION_BIND, email=email).first()
    assert code is not None
    bind_email(client, email, password2, code.code)
    get_userinfo(client)

    create_wechat_user(client)
    send_email_code(client, email3, action=EmailCode.ACTION_BIND)
    code = EmailCode.objects(action=EmailCode.ACTION_BIND, email=email3).first()
    assert code is not None
    bind_email(client, email3, password2, code.code)
    get_userinfo(client)


def test_users(client):
    do_phone(client)
    do_email(client)
