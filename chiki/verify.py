# coding: utf-8
import os
import random
import string
from cStringIO import StringIO
from flask import current_app, session, request, make_response
from wheezy.captcha import image
from .settings import FONT_ROOT

__all__ = [
    'VerifyManager', 'get_verify_code', 'validate_code',
    'init_verify',
]

_keys = set()
_codes = string.uppercase + string.digits
for code in '0oIl1':
   _codes = _codes.replace(code, '')

FONTS = [
    os.path.join(FONT_ROOT, '1.ttf'),
    os.path.join(FONT_ROOT, '2.ttf'),
    os.path.join(FONT_ROOT, '3.ttf'),
    os.path.join(FONT_ROOT, '4.ttf'),
]
BG_COLORS = ['#ffffff', '#fbfbfb', '#fdfeff']
TEXT_COLORS = ['#39f', '#3f9', '#93f', '#9f3', '#f93', '#f39']


class VerifyManager(object):

    def __init__(self, app=None, code_url='/verify_code'):
        self.code_url = code_url
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.verify = self

        @app.route(self.code_url)
        def verify_code():
            key = request.args.get('key', None)
            code, _ = get_verify_code(key, refresh=True)
            return code2image(code)


def get_verify_code(key, refresh=False, code_len=4):
    _keys.add(key)

    if 'verify_codes' not in session:
        session['verify_codes'] = {}

    codes = session['verify_codes']
    if key not in codes or refresh:
        codes[key] = {
            'code': ''.join(random.sample(_codes, code_len)),
            'times': 0,
        }

    return codes[key]['code'], codes[key]['times']


def validate_code(key):
    if 'verify_codes' not in session:
        session['verify_codes'] = {}

    codes = session['verify_codes']
    if key in codes:
        codes[key]['times'] += 1


def code2image(code):
    size = current_app.config.get('VERIFY_CODE_FONT_SIZE', 36)
    drawer = image.captcha(
        drawings=[
            image.background(random.choice(BG_COLORS)),
            image.text(
                fonts=FONTS, 
                font_sizes=(size, size + 2, size + 2),
                color=random.choice(TEXT_COLORS), 
                drawings=[image.rotate(), image.offset()],
            ),
        ],
        width=size * len(code),
        height=size + 4,
    )
    buf = StringIO()
    pic = drawer(code)
    pic.save(buf, 'GIF')
    response = make_response(buf.getvalue())
    response.headers['Content-Type'] = 'image/gif'
    return response


def init_verify(app):
    verify = VerifyManager()
    verify.init_app(app)
