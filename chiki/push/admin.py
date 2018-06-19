# coding: utf-8
import json
from chiki.admin import ModelView
from chiki.admin import formatter_link, formatter_len


class PushLogView(ModelView):
    """推送日志"""

    column_default_sort = ('created', True)
    column_list = ('user', 'type', 'data', 'title', 'alert', 'code', 'created')
    column_center_list = ('user', 'type', 'code', 'created')
    column_filters = ('user', 'created')
    column_formatters = dict(
        user=formatter_link(lambda m: (m.user, '/admin/user/?flt1_0=%s' % str(m.user))),
    )


class PushActionView(ModelView):
    """推送"""
    column_center_list = ('action', 'created',)
    column_filters = ('key', 'name', 'created')


class PushAllLogView(ModelView):
    '''全员推送日志'''

    column_default_sort = ('created', True)
    column_list = ('title', 'alert', 'data', 'code', 'created')
    column_center_list = ('code', 'created')
    column_filters = ('title', 'code', 'created',)
    column_formatters = dict(
        alert=formatter_link(lambda m: (m.alert, str(url(m.data))), max_len=15),
        data=formatter_len(40)
    )


def url(data):
    items = json.loads(data)
    url = items.pop('url')
    return url
