# coding: utf-8
import requests


class Express(object):

    QUERY_URL = 'http://jisukdcx.market.alicloudapi.com/express/query'

    def __init__(self, app=None, code=None):
        self.code = code
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.express = self
        if not self.code:
            self.code = app.config.get('THIRD_EXPRESS', '')

    def query(self, number, type='auto'):
        headers = {'Authorization': 'APPCODE ' + self.code}
        params = dict(number=number, type=type)
        return requests.get(self.QUERY_URL, params=params, headers=headers).json()


def init_express(app):
    if 'THIRD_EXPRESS' in app.config:
        return Express(app)
