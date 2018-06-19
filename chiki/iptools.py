# coding: utf-8
import time
import xmlrpclib
from flask import current_app

__all__ = [
    'parse_ip',
]

iptools, last = None, 0


def tools():
    global iptools, last
    if iptools is not None:
        return iptools

    location = current_app.config.get('IPTOOLS_LOCATION', 
        'http://127.0.0.1:12121')

    if time.time() - last > 300:
        try:
            iptools = xmlrpclib.ServerProxy(location)
        except Exception, e:
            print str(e)
            iptools = None

        last = time.time()

    return iptools


def parse_ip(ip, format='%(pro_d)s-%(city_d)s # %(isp_d)s'):
    if not ip:
        return ''

    t = tools()
    if t is not None:
        try:
            res = t.parse_ip(ip)
            if res['pro_d']:
                return format % res
        except Exception, e:
            print str(e)

    return ip or ''