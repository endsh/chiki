# coding: utf-8
import os


class BaseConfig(object):
    """ 基础配置 """

    # 目录, i18n
    ROOT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_FOLDER = os.path.join(ROOT_FOLDER, 'data')
    DOC_FOLDER = os.path.join(ROOT_FOLDER, 'docs')
    LOG_FOLDER = os.path.join(ROOT_FOLDER, 'logs')
    STATIC_FOLDER = os.path.join(ROOT_FOLDER, 'media')
    TEMPLATE_FOLDER = os.path.join(ROOT_FOLDER, 'templates')
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    CHANGE_400_TO_200 = True

    # Secret Key
    SECRET_KEY = 'SECRET KEY'
    PASSWORD_SECRET = 'PASSWORD SECRET'
    WTF_CSRF_SECRET_KEY = 'WTF CSRF SECRET KEY'

    MONGODB_SETTINGS = dict(host='127.0.0.1', port=27017, db='simple')

    UPLOADS = dict(
        type='local', 
        link='/uploads/%s', 
        path=os.path.join(DATA_FOLDER, 'uploads'),
    )

    # 版本，网站名称等
    VERSION = '0.1.0'
    SITE_NAME = u'simple'


class AdminConfig(BaseConfig):
    """ 后台管理通用配置 """

    PORT = 5000
    ENVVAR = 'SIMPLE_ADMIN'
    SESSION_COOKIE_NAME = 'simple.admin'
    STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'admin')
    RELEASE_STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'admin/dist')
    TEMPLATE_FOLDER = os.path.join(BaseConfig.TEMPLATE_FOLDER, 'admin')

    INDEX_REDIRECT = '/admin/'

    # 后台管理员帐号密码
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = ''


class APIConfig(BaseConfig):
    """ 接口通用配置 """

    PORT = 5001
    ENVVAR = 'SIMPLE_API'
    SESSION_COOKIE_NAME = 'simple.api'
    STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'api')
    RELEASE_STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'api/dist')
    TEMPLATE_FOLDER = os.path.join(BaseConfig.TEMPLATE_FOLDER, 'api')


class WebConfig(BaseConfig):
    """ 网站通用配置 """

    PORT = 5002
    ENVVAR = 'SIMPLE_WEB'
    SESSION_COOKIE_NAME = 'simple'
    STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'web')
    RELEASE_STATIC_FOLDER = os.path.join(BaseConfig.STATIC_FOLDER, 'web/dist')
    TEMPLATE_FOLDER = os.path.join(BaseConfig.TEMPLATE_FOLDER, 'web')
