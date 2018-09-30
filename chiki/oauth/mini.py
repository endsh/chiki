# coding: utf-8
import json
import base64
import inspect
import requests
import urlparse
import werobot.client
import functools
import traceback
from Crypto.Cipher import AES
from chiki.utils import json_error, json_success
from chiki.base import Base
from chiki.contrib.users import um
from chiki.utils import err_logger, is_json, is_api
from chiki.oauth.jssdk import JSSDK
from chiki.contrib.common import Item
from datetime import datetime
from flask import current_app, request, redirect, url_for
from flask import make_response, render_template_string
from urllib import quote, urlencode
from flask.ext.login import current_user, login_user

__all__ = [
    'Mini',
]


class Mini(Base):

    JSCODE_URL = 'https://api.weixin.qq.com/sns/jscode2session'

    def __init__(self, app=None, key=None, config=None, holder=None):
        self.success_callback = None
        self.error_callback = None
        super(Mini, self).__init__(app, key, config, holder)

    def init_app(self, app):
        super(Mini, self).init_app(app)
        self.url = self.get_config(
            'mini_jscode_url', '/oauth/mini/[key]/jscode')
        self.endpoint = self.get_config(
            'mini_jscode_endpoint', 'mini_[key]_jscode')
        self.client = werobot.client.Client(
            self.get_config('appid'), self.get_config('secret'))
        self.client.TYPE = 'mini'

        @app.route(self.url, endpoint=self.endpoint, methods=['POST'])
        def jscode():
            return self.jscode()

    def create_code(self, path):
        url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token=' + self.client.token
        return requests.post(url, data=json.dumps(dict(path=path))).content

    def get_jscode_url(self, code, config=None):
        query = dict(
            appid=self.get_config('appid', config=config),
            secret=self.get_config('secret', config=config),
            js_code=code,
            grant_type='authorization_code',
        )
        return '%s?%s' % (self.JSCODE_URL, urlencode(query))

    def jscode(self):
        ct = request.headers.get('Content-Type', '')
        form = request.json if 'json' in ct else request.form
        code = form.get('code')
        if code:
            url = self.get_jscode_url(code)
            res = requests.get(url).json()
            if 'openid' in res:
                return self.success(res)

            current_app.logger.error('jscode: ' + json.dumps(res))
            return json_error(msg='获取session_key失败')
        elif current_user.is_authenticated():
            um.funcs.on_wechat_login('mini', '')
            # try:
            #     if Item.bool('allow_invite', False, name='允许渠道'):
            #         um.funcs.on_wechat_login('mini', '')
            #     current_user.wechat_user.update_info(
            #         form.get('userInfo'), action='mini')
            #     current_user.wechat_user.save()
            #     current_user.wechat_user.sync(current_user)
            #     current_user.save()
            # except:
            #     current_app.logger.error(traceback.format_exc())
            return json_success(data=um.funcs.userinfo(current_user))
        return json_error(key='LOGIN_REQIURED')

    def success(self, access):
        user = um.funcs.get_wechat_user(access, 'mini')
        try:
            if not user:
                userinfo = dict(
                    openid=access['openid'],
                    unionid=access.get('unionid', ''),
                    session_key=access.get('session_key'),
                )

                user = um.funcs.create_wechat_user(userinfo, 'mini')
            else:
                user.modify(
                    unionid=access.get('unionid', ''),
                    session_key=access.get('session_key'),
                    modified=datetime.now(),
                )

            um.funcs.wechat_login(user)

            if user.user:
                real_user = um.models.User.objects(id=user.user).first()
                if not real_user:
                    user.user = 0
                    user.save()
                else:
                    user = real_user

            login_user(user, remember=True)

            if current_user.is_authenticated() and current_user.is_user():
                um.models.UserLog.login(user.id, 'web', 'mini')
                user.login()
        except:
            current_app.logger.error(traceback.format_exc())

        if request.args.get('access') == 'true':
            return json_success(data=um.funcs.userinfo(user), access=access)

        return json_success(data=um.funcs.userinfo(user))

    def decrypt(self, sessionKey, encryptedData, iv):
        sessionKey = base64.b64decode(sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)
        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)

        dec = cipher.decrypt(encryptedData)
        decrypted = json.loads(self._unpad(dec))

        # if decrypted['watermark']['appid'] != appId:
        #     raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s) -1:])]
