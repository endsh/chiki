# coding: utf-8
import re
import urllib
import urllib2
import json
import socket
import traceback
import ConfigParser
from flask import current_app
from .CCPRestSDK import REST

__all__ = [
    'send_rong_sms', 'send_ihuyi_sms', 'send_jisu_sms'
]


def send_rong_sms(phone, datas, temp_id):
    settings = current_app.config.get('SMS_RONG')
    host = settings.get('host', 'app.cloopen.com')
    port = settings.get('port', 8883)
    version = settings.get('version', '2013-12-26')
    sid = settings.get('sid')
    token = settings.get('token')
    appid = settings.get('appid')

    rest = REST(host, str(port), version)
    rest.setAccount(sid, token)
    rest.setAppId(appid)
    result = rest.sendTemplateSMS(phone, datas, temp_id)
    return result.get("statusCode") == "000000"


def send_ihuyi_sms(phone, text):
    settings = current_app.config.get('SMS_IHUYI')
    params = dict(
        account=settings['account'],
        password=settings['password'],
        mobile=phone,
        content=text,
    )
    tpl = 'http://106.ihuyi.cn/webservice/sms.php?method=Submit&%s'
    url = tpl % urllib.urlencode(params)

    res = ''
    for i in range(3):
        try:
            res = urllib.urlopen(url).read()
            break
        except:
            current_app.logger.error('短信接口出错：' + traceback.format_exc())
    if not re.search(r'<code>2</code>', res):
        current_app.logger.error('短信接口出错：' + str(res))
    return True if re.search(r'<code>2</code>', res) else False


def send_jisu_sms(phone, text):
    app = current_app.config.get('SMS_JISU')
    data = dict(
        appkey=app['appkey'],
        mobile=phone,
        content=text,
    )
    url_values = urllib.urlencode(data)
    url = "http://api.jisuapi.com/sms/send" + "?" + url_values

    request = urllib2.Request(url)
    result = urllib2.urlopen(request)
    jsonarr = json.loads(result.read())

    res = jsonarr["status"]
    if res != u"0":
        return jsonarr["msg"]

    return True if res == u"0" else False
