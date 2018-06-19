# coding: utf-8
import json
import inspect
import requests
import urlparse
import werobot.client
import functools
from chiki.api import abort, success
from chiki.api.const import *
from chiki.base import Base
from chiki.utils import err_logger, is_json, is_api, add_args
from chiki.oauth.jssdk import JSSDK
from datetime import datetime
from flask import current_app, request, redirect, url_for
from flask import make_response, render_template_string
from urllib import quote, urlencode

__all__ = [
    'WXAuth',
]


class WXAuth(Base):
    """微信登录有三种方式：公众号授权登录(mp)、扫码登录(qrcode)、手机登录(mobile)，
    只需相应加上配置，就支持相应的方式::

        WXAUTH = dict(
            mp=dict(
                appid='wx5d4a******b12c76',
                secret='bc1cdd******fd1496f1a8ae751f965b',
            ),
            mobile=dict(appid='', secret=''),
            qrcode=dict(appid='', secret=''),
        )

    下面有不少方法中有config的参数，用于动态加载配置。配置示例：

        dict(
            mp=dict(
                appid=self.appid,
                secret=self.secret,
            ),
            callback_host=self.host,
        )
    """

    ACTION_MP = 'mp'
    ACTION_MOBILE = 'mobile'
    ACTION_QRCODE = 'qrcode'

    ARGS_ERROR = 'args_error'
    AUTH_ERROR = 'auth_error'
    ACCESS_ERROR = 'access_error'
    GET_USERINFO_ERROR = 'get_userinfo_error'
    MSGS = {
        ARGS_ERROR: '参数错误',
        AUTH_ERROR: '授权失败',
        ACCESS_ERROR: '获取令牌失败',
        GET_USERINFO_ERROR: '获取用户信息失败',
    }

    SNSAPI_BASE = 'snsapi_base'
    SNSAPI_USERINFO = 'snsapi_userinfo'
    SNSAPI_LOGIN = 'snsapi_login'
    AUTH_CONNECT_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    AUTH_QRCONNECT_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    ACCESS_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    REFRESH_URL = 'https://api.weixin.qq.com/sns/oauth2/refresh_token'
    USERINFO_URL = 'https://api.weixin.qq.com/sns/userinfo'
    CHECK_URL = 'https://api.weixin.qq.com/sns/auth'

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.success_callback = None
        self.error_callback = None
        self.config_callback = None
        self.wxclients = dict()
        super(WXAuth, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(WXAuth, self).init_app(app)
        self.callback_url = self.get_config(
            'wxauth_url', '/oauth/wechat/callback/[key]')
        self.endpoint = self.get_config(
            'wxauth_endpoint', 'wxauth_[key]_callback')
        self.js_url = self.get_config(
            'wxauth_js_url', '/weixin-[key]-login.js')
        self.js_endpoint = self.get_config(
            'wxauth_js_endpoint', 'wxauth_[key]_js_login')
        mp = self.get_config(self.ACTION_MP)
        if mp:
            self.client = werobot.client.Client(
                mp.get('appid'), mp.get('secret'))
            self.client.key = self.key
            if not hasattr(app, 'wxclient'):
                app.wxclient = self.client

        @app.route(self.callback_url, endpoint=self.endpoint)
        def wxauth_callback():
            """ 微信授权完成后的回调 """
            return self.callback()

        @app.route(self.js_url, endpoint=self.js_endpoint)
        def weixin_login():
            """ PC网页版扫码登陆所需的js """
            qrcode = self.get_config(self.ACTION_QRCODE)
            js = ''
            if qrcode:
                config = dict(
                    id=request.args.get('id', ''),
                    appid=qrcode.get('appid', ''),
                    scope=self.SNSAPI_LOGIN,
                    redirect_uri=quote(url_for(
                        self.endpoint, scope=self.SNSAPI_LOGIN,
                        action=self.ACTION_QRCODE, _external=True)),
                    state='STATE',
                    style=request.args.get('style', 'white'),
                    href=request.args.get('href', ''),
                )
                js = render_template_string(
                    "var wxauth = new WxLogin({{ config | safe }});",
                    config=json.dumps(config))
            resp = make_response(js)
            resp.headers['Control-Cache'] = 'no-cache'
            resp.headers['Content-Type'] = 'text/javascript; charset=utf-8'
            return resp

        self.jssdk = JSSDK(app, self)

    def get_wxclient(self, appid, secret):
        """ 生成werobot客户端，用于发送模版消息等 """
        if appid not in self.wxclients:
            self.wxclients[appid] = werobot.client.Client(appid, secret)
        return self.wxclients.get(appid)

    def quote(self, **kwargs):
        return dict((x, quote(y.encode('utf-8') if type(
            y) is unicode else y)) for x, y in kwargs.iteritems())

    def get_access_url(self, action, code, config=None):
        """ 生成获取access_token的链接 """
        config = self.get_config(action, config=config)
        query = dict(
            appid=config.get('appid'),
            secret=config.get('secret'),
            code=code,
            grant_type='authorization_code',
        )
        return '%s?%s' % (self.ACCESS_URL, urlencode(query))

    @err_logger
    def access_token(self, action, code, config=None):
        """ 通过code换取网页授权access_token """
        url = self.get_access_url(action, code, config=config)
        return requests.get(url).json()

    def get_refresh_url(self, action, token, config=None):
        """ 生成获取refresh_token的链接 """
        config = self.get_config(action, config=config)
        query = dict(
            appid=config.get('appid'),
            refresh_token=token,
            grant_type='refresh_token',
        )
        return '%s?%s' % (self.REFRESH_URL, urlencode(query))

    @err_logger
    def refresh_token(self, action, token, config=None):
        """ werobot.client需要refresh_token """
        url = self.get_refresh_url(action, token, config=config)
        return requests.get(url).json()

    def get_userinfo_url(self, token, openid, lang='zh_CN'):
        """ access_token 获取用户信息的链接 """
        query = dict(access_token=token, openid=openid, lang=lang)
        return '%s?%s' % (self.USERINFO_URL, urlencode(query))

    @err_logger
    def get_userinfo(self, token, openid):
        """ access_token 获取用户信息 """
        url = self.get_userinfo_url(token, openid)
        res = requests.get(url)
        return json.loads(res.content)

    @err_logger
    def get_user_info(self, openid):
        """ 用openid获取用户信息 """
        try:
            return self.client.get_user_info(openid)
        except:
            self.client.refresh_token()
            return self.client.get_user_info(openid)

    def get_check_url(self, token, openid):
        """ 检测用户access_token是否过期的链接 """
        query = dict(access_token=token, openid=openid)
        return '%s?%s' % (self.CHECK_URL, urlencode(query))

    @err_logger
    def check_token(self, token, openid):
        """ 检测用户access_token是否过期 """
        url = self.get_check_url(token, openid)
        return requests.get(url).json()['errcode'] == 0

    def get_auth_url(self, action, next, scope=SNSAPI_BASE, state='STATE',
                     config=None, **kwargs):
        """ 生成微信网页授权链接。

        :param action: 公众号授权登录(mp)、扫码登录(qrcode)
        :param next: 授权后下一步链接
        :param scope: snsapi_base|snsapi_userinfo
        :param state: STATE
        :param config: 自定义公众号配置(appid,secret等)
        """
        if action == self.ACTION_QRCODE:
            scope = self.SNSAPI_LOGIN

        conf = self.get_config(action, config=config)
        host = self.get_config('callback_host', config=config)
        appid = conf.get('appid')
        if not host:
            callback = url_for(self.endpoint, scope=scope, next=next,
                               action=action, appid=appid, _external=True,
                               **kwargs)
        else:
            callback = url_for(self.endpoint, scope=scope, next=next,
                               action=action, appid=appid, **kwargs)
            callback = 'http://%s%s' % (host, callback)
        query = self.quote(
            appid=conf.get('appid'),
            callback=callback,
            scope=scope,
            state=state,
        )
        url = self.AUTH_CONNECT_URL
        if action != 'mp':
            url = self.AUTH_QRCONNECT_URL
        return '{url}?appid={appid}&redirect_uri={callback}' \
            '&response_type=code&scope={scope}&state={state}' \
            '#wechat_redirect'.format(url=url, **query)

    def get_action(self, action):
        if not action:
            ua = request.headers.get('User-Agent', '').lower()
            if 'micromessenger' in ua:
                action = self.ACTION_MP
            elif is_api():
                action = self.ACTION_MOBILE
            else:
                action = self.ACTION_QRCODE
        return action

    def auth(self, action='', next='', scope=SNSAPI_BASE, state='STATE',
             config=None, **kwargs):
        """发起微信登录，在需要的地方带用即可。

        :param action: 公众号授权登录(mp)、扫码登录(qrcode)
        :param next: 授权后下一步链接
        :param scope: snsapi_base|snsapi_userinfo
        :param state: STATE
        """
        action = self.get_action(action)
        if action == 'mobile' or is_json():
            return abort(WXAUTH_REQUIRED)

        if config is None:
            config = self.load_config()

        return redirect(self.get_auth_url(
            action, next, scope, state, config, **kwargs))

    def callback(self):
        action = request.args.get('action', 'mp')
        code = request.args.get('code', '')
        next = request.args.get('next', '')
        scope = request.args.get('scope', self.SNSAPI_BASE)
        appid = request.args.get('appid', '')

        config = self.load_config(appid)
        rh = self.get_config('replace_host', True, config=config)
        if rh and request.host not in next and next.startswith('http://'):
            url = request.url.replace(
                request.host, urlparse.urlparse(next).netloc)
            return redirect(url)

        if action not in ['mp', 'mobile', 'qrcode']:
            return self.error(self.ARGS_ERROR, action, next)

        if not code:
            return self.error(self.AUTH_ERROR, action, next)

        access = self.access_token(action, code, config=config)
        if not access or 'openid' not in access:
            log = '%s\naccess error\naccess: %s\nurl: %s' \
                  '\nnext: %s\ncode: %s\naccess: %s'
            current_app.logger.error(log % (
                str(datetime.now()) + '-' * 80,
                self.get_access_url(action, code),
                request.url, next, code, str(access)))
            return self.error(self.ACCESS_ERROR, action, next)

        return self.success(action, scope, access, next, config=config)

    def load_config(self, appid=None):
        if callable(self.config_callback):
            return self.config_callback(appid)

    def success(self, action, scope, access, next, config=None):
        if next and 'redirect=true' in next:
            return redirect(add_args(next, mp_openid=access['openid']))
        callback = self.success_callback
        if not callback:
            return '授权成功，请设置回调'

        if type(callback) == functools.partial or \
                'config' in inspect.getargspec(callback)[0]:
            res = callback(action, scope, access, next, config=config)
        else:
            res = callback(action, scope, access, next)

        if res:
            return res

        if is_json():
            if current_user.is_authenticated():
                return success()
            return error(msg='登录出错')
        return redirect(next)

    def error(self, err, action, next):
        if self.error_callback:
            res = self.error_callback(err, action, next)
            if res:
                return res
        if is_json():
            return error(msg='授权失败(%s): %s' % (action, err))
        return '授权失败(%s): %s' % (action, err)

    def success_handler(self, callback):
        """授权成功回调::

            @app.wxauth.success_handler
            def wxauth_success(action, scope, access, next):
                pass

        :param action: mp|qrcode|mobile
        :param scope: snsapi_base|snsapi_userinfo
        :param access: 微信授权成功返回的信息
        :param next: 下一步的链接
        :rtype: None或自定义Response
        """
        self.success_callback = callback
        return callback

    def error_handler(self, callback):
        """授权失败回调::

            @app.wxauth.error_handler
            def wxauth_error(err, action, next):
                pass

        :param err: 错误吗
        :param action: mp|qrcode|mobile
        :param next: 下一步的链接
        :rtype: None或自定义Response
        """
        self.error_callback = callback
        return callback

    def config_handler(self, callback):
        """配置加载回调，动态加载配置::

            @app.wxauth.error_handler
            def wxauth_config(appid=None):
                return current_app.config.get("WXAUTH")

        :param appid: 根据appid加载配置
        """
        self.config_callback = callback
        return callback
