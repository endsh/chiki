# coding: utf-8
import re
import os
import sys
import json
import types
import errno
import random
import string
import functools
import hashlib
import traceback
import requests
import urlparse
from urllib import urlencode
from datetime import datetime, date
from StringIO import StringIO
from flask import jsonify, current_app, request, redirect
from flask.ext.login import current_user

import urllib3
urllib3.disable_warnings()

__all__ = [
    'strip', 'json_success', 'json_error', 'datetime2best', 'time2best',
    'today', 'err_logger', 'parse_spm', 'get_spm', 'get_version', 'get_os',
    'get_platform', 'get_channel', 'get_ip', 'is_ajax', 'str2datetime',
    'is_json', 'is_empty', 'randstr', 'AttrDict', 'url2image', 'retry',
    'tpl_data', 'get_module', 'rmb3', 'check_encode', 'url_with_user',
    'get_url_arg', 'create_short_url', 'ip_limit', 'random_index', 'is_debug',
    'sign', 'add_args', 'import_file', 'unicode2utf8', 'json2utf8',
    'url_external', 'is_wechat',
]


def down(url, source=None):
    try:
        if source:
            return StringIO(requests.get(
                url, headers=dict(Referer=source), verify=False).content)
        return StringIO(requests.get(url, verify=False).content)
    except:
        current_app.logger.error(traceback.format_exc())


def get_format(image):
    format = image.split('.')[-1]
    if format in ['jpg', 'jpeg']:
        return 'jpg'
    if format in ['gif', 'bmp', 'png', 'ico']:
        return format
    return ''


def url2image(url, source=None, format=''):
    return dict(stream=down(url, source=source), format=get_format(url) or format) if url else None


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def today():
    return datetime.strptime(str(date.today()), '%Y-%m-%d')


def strip(val, *args):
    if not val:
        return val

    if isinstance(val, dict):
        return dict((x, strip(y) if x not in args else y) for x, y in val.iteritems())
    if isinstance(val, list):
        return list(strip(x) for x in val)
    if hasattr(val, 'strip'):
        return val.strip()
    return val


def json_success(**kwargs):
    kwargs['code'] = 0
    return jsonify(kwargs)


def json_error(**kwargs):
    kwargs['code'] = -1
    return jsonify(kwargs)


def datetime2best(input):
    tmp = datetime.now() - input
    if tmp.days in [0, -1]:
        seconds = tmp.days * 86400 + tmp.seconds
        if seconds < -3600:
            return '%d小时后' % (-seconds // 3600)
        elif seconds < -60:
            return '%d分钟后' % (-seconds // 60)
        elif seconds < 0:
            return '%d秒后' % -seconds
        elif seconds < 60:
            return '%d秒前' % seconds
        elif seconds < 3600:
            return '%d分钟前' % (seconds // 60)
        else:
            return '%d小时前' % (seconds // 3600)
    elif tmp.days < -365:
        return '%d年后' % (-tmp.days // 365)
    elif tmp.days < -30:
        return '%d个月后' % (-tmp.days // 30)
    elif tmp.days < -1:
        return '%d天后' % -(tmp.days + 1)
    elif tmp.days < 30:
        return '%d天前' % tmp.days
    elif tmp.days < 365:
        return '%d个月前' % (tmp.days // 30)
    else:
        return '%d年前' % (tmp.days // 365)


def time2best(input):
    if type(input) != datetime:
        input = datetime.fromtimestamp(input)
    return datetime2best(input)


def err_logger(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            current_app.logger.error(traceback.format_exc())
    return wrapper


def parse_spm(spm):
    if spm:
        spm = spm.replace('unknown', '0')
    if spm and re.match(r'^(\d+\.)+\d+$', spm):
        res = map(lambda x: int(x), spm.split('.'))
        while len(res) < 5:
            res.append(0)
        return res[:5]
    return 0, 0, 0, 0, 0


def get_spm():
    spm = request.args.get('spm')
    if spm:
        return spm

    spm = []
    oslist = ['ios', 'android', 'windows', 'linux', 'mac']
    plist = ['micromessenger', 'weibo', 'qq']
    ua = request.args.get('User-Agent', '').lower()

    for index, os in enumerate(oslist):
        if os in ua:
            spm.append(index + 1)
            break
    else:
        spm.append(index + 1)

    for index, p in enumerate(plist):
        if p in ua:
            spm.append(index + 1)
            break
    else:
        spm.append(index + 1)

    spm.append(0)
    spm.append(0)

    return '.'.join([str(x) for x in spm])


def get_version():
    return parse_spm(get_spm())[3]


def get_channel():
    return parse_spm(get_spm())[2]


def get_os():
    return parse_spm(get_spm())[0]


def get_platform():
    return parse_spm(get_spm())[1]


def get_ip():
    if 'Cdn-Real-Ip' in request.headers:
        return request.headers['Cdn-Real-Ip']
    if 'X-Real-Forwarded-For' in request.headers:
        return request.headers['X-Real-Forwarded-For'].split(',')[0]
    if 'X-FORWARDED-FOR' in request.headers:
        return request.headers['X-FORWARDED-FOR'].split(',')[0]
    return request.headers.get('X-Real-Ip') or request.remote_addr


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('is_ajax', 'false') == 'true' \
        or request.headers.get('Accept', '').startswith('application/json') \
        or 'application/json' in request.headers.get('Content-Type', '')


def is_wechat():
    ua = request.headers['User-Agent'].lower()
    return 'micromessenger' in ua


def is_api():
    return 'API' in current_app.config.get('ENVVAR', '')


def is_json():
    return is_api() or is_ajax()


def is_empty(fd):
    fd.seek(0)
    first_char = fd.read(1)
    fd.seek(0)
    return not bool(first_char)


def str2datetime(datestr):
    try:
        return datetime.strptime(datestr, '%Y-%m-%d %H:%M:%s')
    except ValueError:
        return datetime.min


def randstr(x=32):
    a = lambda: random.choice(string.ascii_letters + string.digits)
    return ''.join(a() for _ in range(x))


def retry(times=3):
    def wrapper(func):
        res = None
        for i in range(times):
            try:
                res = func()
                break
            except:
                current_app.logger.error(traceback.format_exc())
        return res
    return wrapper


def tpl_data(color="#333333", **kwargs):
    res = dict()
    for key, value in kwargs.iteritems():
        res[key] = dict(value=value, color=color)
    return res


def get_module():

    def main_module_name():
        mod = sys.modules['__main__']
        file = getattr(mod, '__file__', None)
        return file and os.path.splitext(os.path.basename(file))[0]

    def modname(fvars):

        file, name = fvars.get('__file__'), fvars.get('__name__')
        if file is None or name is None:
            return None

        if name == '__main__':
            name = main_module_name()
        return name

    return modname(globals())


def rmb3(num):
    d = float('%.2f' % (num / 100.0))
    return str([str(d), int(d)][int(d) == d])


def check_encode(text, code='gb18030'):
    try:
        text.encode(code)
        return True
    except:
        pass
    return False


def url_with_user(url):
    if current_user.is_authenticated() and current_user.is_user():
        res = urlparse.urlparse(url)
        if 'uid=' not in res.query:
            if res.query:
                query = '%s&uid=%d' % (res.query, current_user.id)
            else:
                query = 'uid=%d' % current_user.id
            url = '%s://%s%s?%s' % (res.scheme, res.netloc, res.path, query)
            if res.fragment:
                url += '#' + res.fragment
    return url


def get_url_arg(url, key):
    res = urlparse.parse_qs(urlparse.urlparse(url).query).get(key)
    return res[0] if res else None


def create_short_url(key, url, **kwargs):
    tpl = 'http://api.t.sina.com.cn/short_url/shorten.json?%s'
    res = requests.get(
        tpl % urlencode(dict(source=key, url_long=url)), **kwargs).json()
    return res[0]['url_short'] if res[0]['type'] == 0 else url


def ip_limit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from chiki.base import db
        ip = get_ip()
        regx = db.Item.data('ip_regx', '^116\.23\.|^59\.41\.', name='IP正则')
        limit = db.Item.get('ip_limit', 100, name='IP限制')
        url = db.Item.data('ip_redirect', 'http://www.qq.com/', name='IP跳转')
        if not re.match(regx, ip) and db.User.objects(ip=ip).count() >= limit:
            return redirect(url)
        return func(*args, **kwargs)
    return wrapper


def random_index(rate):
    start, index = 0, 0
    num = random.randint(0, sum(rate))
    for index, scope in enumerate(rate):
        start += scope
        if num < start:
            break
    return index


def is_debug():
    return current_app.debug or \
        request.args.get('debug') == 'true' or \
        request.host.startswith('0.0.0.0') or \
        request.host.startswith('127.0.') or \
        request.host.startswith('192.168.')


def sign(key, **kwargs):
    keys = sorted(filter(
        lambda x: x[1] is not None, kwargs.iteritems()), key=lambda x: x[0])
    text = '&'.join(['%s=%s' % x for x in keys])
    text += '&key=%s' % key
    return hashlib.md5(text.encode('utf-8')).hexdigest().upper()


def add_args(url, **kwargs):
    if '?' in url:
        return url + '&' + urlencode(kwargs)
    return url + '?' + urlencode(kwargs)


def import_file(filename):
    d = types.ModuleType('module')
    d.__file__ = filename
    try:
        with open(filename, mode='rb') as fd:
            exec(compile(fd.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if e.errno in (errno.ENOENT, errno.EISDIR):
            return False
        e.strerror = 'Unable to load file (%s)' % e.strerror
        raise
    return d


def unicode2utf8(obj):
    u = unicode2utf8
    if type(obj) == str:
        return obj
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    if isinstance(obj, dict):
        return dict((u(k), u(v)) for k, v in obj.iteritems())
    if isinstance(obj, list):
        return [u(x) for x in obj]
    return obj


def json2utf8(ensure_ascii=False, indent=None, **kwargs):
    return json.dumps(
        unicode2utf8(kwargs), ensure_ascii=ensure_ascii, indent=indent)


def url_external(url):
    if url.startswith('/'):
        return 'http://' + request.host + url
    return url
