#　coding: utf-8
from flask import request, render_template


def message(msg, style='info', url='', timeout=0, **kwargs):
    return render_template('msg.html', msg=msg, style=style,
                           url=url, timeout=timeout, **kwargs)


def success(msg, url='', timeout=0, **kwargs):
    return message(msg, style='success', url=url, timeout=timeout, **kwargs)


def error(msg, url='', timeout=0, **kwargs):
    return message(msg, style='warn', url=url, timeout=timeout, **kwargs)


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('ajax') == 'true'
