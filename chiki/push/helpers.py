# coding: utf-8
import json
import jpush
from .models import PushLog, PushAllLog
from flask import current_app


def push_helper(alert=None, type=None, title=None, builder_id=1, badge="+1", audience=jpush.all_,
                platform=jpush.platform("ios", "android"), **kwargs):

    jpush_setting = current_app.config.get('JPUSH')
    push = jpush.JPush(jpush_setting['appkey'], jpush_setting['secret'])
    obj = push.create_push()
    obj.platform = platform
    obj.audience = audience
    if alert is not None:
        android_msg = dict(builder_id=builder_id, extras=kwargs)
        if title is not None:
            android_msg['title'] = title
        ios_msg = dict(extras=kwargs)
        if badge is not None:
            ios_msg['badge'] = badge
        obj.notification = jpush.notification(alert=alert, android=android_msg, ios=ios_msg)
    else:
        obj.message = jpush.message(alert, content_type=type, title=title, extras=kwargs)

    try:
        obj.send()
        return 0
    except jpush.JPushFailure, e:
        return e.error_code


def push2user(user, type, data={}, alert=None, title=None, builder_id=1, badge="+1"):
    audience = jpush.audience(jpush.alias('u%s' % user.phone))
    extras = data

    code = push_helper(
        alert=alert, type=type, title=title, builder_id=builder_id, badge=badge,
        audience=audience, **extras)

    PushLog(user=user.id, type=type, data=json.dumps(data), alert=alert, title=title, code=code).save()

    return True if code == 0 else False


def push2all(type, alert=None, title=None, builder_id=1, audience=jpush.all_, **kwargs):

    code = push_helper(
        type=type, alert=alert, title=title, builder_id=builder_id,
        badge=None, audience=audience, **kwargs)
    PushAllLog(type=type, alert=alert, title=title, code=code, data=json.dumps(kwargs)).save()

    return True if code == 0 else False
