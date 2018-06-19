# coding: utf-8
import json
import time
import requests
import werobot.client
from chiki.contrib.common import Item, MiniTPLLog
from flask import current_app
from flask.ext.werobot import WeRoBot
from werobot.messages import handle_for_type, WeChatMessage
from urllib import urlencode

__all__ = [
    'patch_monkey', 'WeRoBot',
]


def patch_monkey():

    class Client(werobot.client.Client):

        SEND_TPL_URL = 'https://api.weixin.qq.com/cgi-bin/message/template/send'
        SEND_MINI_TPL_URL = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send'
        CUSTOM_RUL = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token='

        key = 'default'
        TYPE = 'wxauth'

        @property
        def token(self):
            now = time.time()
            key = '%s:access_token_%s' % (self.TYPE, self.key)
            token = json.loads(Item.data(key, '{}'))
            if not token or token['deadline'] <= now:
                token = self.grant_token()
                token['deadline'] = now + token['expires_in']
                Item.set_data(key, json.dumps(token))
            return token['access_token']

        def refresh_token(self):
            now = time.time()
            key = '%s:access_token' % self.TYPE
            token = self.grant_token()
            token['deadline'] = now + token['expires_in']
            Item.set_data(key, json.dumps(token))

        def send_msg(self, msg):
            return requests.post(self.CUSTOM_RUL + self.token, data=msg).content

        def send_tpl(self, openid, tpl, url='', data=dict(), retry=True):
            data = json.dumps(dict(touser=openid, data=data, template_id=tpl, url=url))
            xurl = '%s?%s' % (self.SEND_TPL_URL, urlencode(dict(access_token=self.token)))
            res = requests.post(xurl, data=data).json()
            if res['errcode'] == 0:
                return True

            if retry and 'access_token' in res['errmsg']:
                self.refresh_token()
                self.send_tpl(openid, tpl, url, data, False)

            current_app.logger.error('robot send_tpl error: %s' % json.dumps(res))
            return False

        def send_mini_tpl(self, openid, tpl, form_id='', url='', data=dict(), retry=True):
            data = json.dumps(dict(touser=openid, data=data, template_id=tpl, page=url, form_id=form_id))
            xurl = '%s?%s' % (self.SEND_MINI_TPL_URL, urlencode(dict(access_token=self.token)))
            res = requests.post(xurl, data=data).json()
            if res['errcode'] == 0:
                return res
            #     return True

            if retry and 'access_token' in res['errmsg']:
                self.refresh_token()
                self.send_mini_tpl(openid, tpl, form_id, url, data, False)

            current_app.logger.error('robot send_tpl error: %s' % json.dumps(res))
            return res

    werobot.client.Client = Client

    @handle_for_type('event')
    class EventMessage(WeChatMessage):

        def __init__(self, message):
            message.pop('type')
            self.type = message.pop('Event').lower()
            if self.type == 'click':
                self.key = message.pop('EventKey')
            elif self.type in ['subscribe', 'scan']:
                try:
                    self.key = int(message.pop('EventKey', '')[8:] or 0)
                except:
                    self.key = 0
            elif self.type == 'location':
                self.latitude = float(message.pop('Latitude'))
                self.longitude = float(message.pop('Longitude'))
                self.precision = float(message.pop('Precision'))
            super(EventMessage, self).__init__(message)

    def scan(self, f):
        self.add_handler(f, type='scan')
        return f

    def mini(self, f):
        if 'miniprogrampage' not in self._handlers:
            self._handlers['miniprogrampage'] = []
        self.add_handler(f, type='miniprogrampage')
        return f

    def user_enter_tempsession(self, f):
        self.add_handler(f, type='user_enter_tempsession')
        return f

    WeRoBot.message_types = [
        'subscribe', 'unsubscribe', 'click', 'view',
        'text', 'image', 'link', 'location', 'voice', 'scan',
        'user_enter_tempsession',
    ]
    WeRoBot.scan = scan
    WeRoBot.mini = mini
    WeRoBot.user_enter_tempsession = user_enter_tempsession


patch_monkey()
robot = WeRoBot()
