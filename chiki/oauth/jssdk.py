# coding: utf-8
import time
import json
import random
import requests
import hashlib
import string
from flask import current_app, request, render_template_string
from flask import make_response
from chiki.contrib.common import Item

DEFAULT_JS_API_LIST = '|'.join([x.strip() for x in """
onMenuShareTimeline|onMenuShareAppMessage|onMenuShareQQ|
onMenuShareWeibo|onMenuShareQZone|startRecord|stopRecord|
onVoiceRecordEnd|playVoice|pauseVoice|stopVoice|onVoicePlayEnd|
uploadVoice|downloadVoice|chooseImage|previewImage|uploadImage|
downloadImage|translateVoice|getNetworkType|openLocation|
getLocation|hideOptionMenu|showOptionMenu|hideMenuItems|
showMenuItems|hideAllNonBaseMenuItem|showAllNonBaseMenuItem|
closeWindow|scanQRCode|chooseWXPay|openProductSpecificView|
addCard|chooseCard|openCard""".split('|')])


class JSSDK(object):

    TPL = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi'

    def __init__(self, app=None, wxauth=None):
        self._ticket = ''
        self._expires_at = 0
        self.wxauth = wxauth
        self.key = wxauth.key
        self.appid = wxauth.get_config('mp').get('appid')
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.url = '/weixin-config-%s.js' % self.key
        self.endpoint = 'weixin_config_js_%s' % self.key

        @app.route(self.url, endpoint=self.endpoint)
        def weixin_config():
            apis = Item.data('wx_js_api_list_%s' % self.key,
                             DEFAULT_JS_API_LIST).split('|')
            apis = [str(x) for x in apis]
            sign = self.sign
            config = dict(
                debug=True if request.args.get('debug') == 'true' else False,
                appId=self.appid,
                timestamp=sign['timestamp'],
                nonceStr=sign['nonceStr'],
                signature=sign['signature'],
                jsApiList=apis,
            )
            js = render_template_string("wx.config({{ config | safe }});",
                config=json.dumps(config))
            resp = make_response(js)
            resp.headers['Control-Cache'] = 'no-cache'
            resp.headers['Content-Type'] = 'text/javascript; charset=utf-8'
            return resp

    @property
    def nonce(self):
        a = lambda: random.choice(string.ascii_letters + string.digits)
        return ''.join(a() for _ in range(15))

    @property
    def ticket(self):
        now = int(time.time())
        if self._expires_at - now < 60:
            self.refresh()

        return self._ticket

    def refresh(self, retry=True):
        url = self.TPL % self.wxauth.client.token
        res = requests.get(url).json()

        if res['errcode'] != 0:
            if retry and 'access_token' in res['errmsg']:
                self.wxauth.client.refresh_token()
                return self.refresh(False)
            current_app.logger.error(str(res))
            return ''

        self._ticket = res['ticket']
        self._expires_at = res['expires_in'] + time.time()
        return self._ticket

    @property
    def sign(self):
        res = dict(
            nonceStr=self.nonce,
            timestamp=int(time.time()),
            jsapi_ticket=self.ticket,
            url=request.headers.get('Referer', request.url),
        )
        text = '&'.join(['%s=%s' % (x.lower(), res[x]) for x in sorted(res)])
        res['signature'] = hashlib.sha1(text).hexdigest()

        if request.args.get('debug') == 'true':
            res['text'] = text
            Item.set_data('jssdk:info', json.dumps(res))
        return res
