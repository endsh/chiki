# coding: utf-8
from chiki.admin import ModelView
from datetime import datetime
from chiki.admin import formatter_model


class UserView(ModelView):
    show_popover = True
    column_default_sort = ('registered', True)
    column_list = (
        'id', 'phone', 'avatar', 'location', 'debug', 'active', 'channel', 'spm', 'ip',
        'generate', 'error', 'logined', 'registered'
    )
    column_center_list = (
        'id', 'phone', 'avatar', 'debug', 'active', 'channel', 'spm', 'ip',
        'generate', 'error', 'logined', 'registered'
    )
    column_searchable_list = ('phone', 'nickname')
    column_filters = ('id', 'phone')
    form_excluded_columns = ('id', 'generate')

    def on_model_change(self, form, model, created=False):
        model.create()
        if created:
            model.generate = True
        model.modified = datetime.now()


@formatter_model
def formatter_address(model):
    address = '%s%s' % (model.province if model.province else '', model.city if model.city else '')
    return address


@formatter_model
def formatter_headimgurl(model):
    html = """
    <a href=%s target="_blank" style="text-decoration:none">
        <img src=%s style="height: 40px; width:40px; margin: -6px 0">
    </a>""" % (model.headimgurl, model.headimgurl)
    return html


class WeChatUserView(ModelView):
    show_popover = True
    column_labels = dict(address='地址')
    column_default_sort = ('created', True)
    column_list = (
        'headimgurl', 'user', 'nickname', 'address', 'scene', 'remark', 'groupid',
        'subscribe', 'subscribe_time', 'modified', 'created'
    )
    column_center_list = (
        'user', 'scene', 'nickname', 'address', 'remark', 'groupid',
        'subscribe', 'subscribe_time', 'modified', 'created', 'headimgurl'
    )
    column_hidden_list = ('scene', 'remark')
    column_searchable_list = ('unionid', 'mp_openid', 'nickname')
    column_filters = (
        'user', 'nickname', 'sex', 'address', 'scene', 'unionid', 'mp_openid',
        'subscribe_time', 'updated', 'expires_in', 'modified', 'created'
    )
    column_formatters = dict(
        address=formatter_address,
        headimgurl=formatter_headimgurl,
        )
    form_excluded_columns = ('address',)


class QQUserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = (
        'user', 'openid', 'is_yellow_vip', 'is_yellow_year_vip',
        'access_token', 'expires_in', 'refresh_token', 'modified', 'created'
    )
    column_center_list = (
        'user', 'openid', 'is_yellow_vip', 'is_yellow_year_vip',
        'access_token', 'expires_in', 'refresh_token', 'modified', 'created'
    )
    column_searchable_list = ('openid',)
    column_filters = ('openid', 'is_yellow_vip', 'vip', 'yellow_vip_level', 'level', 'is_yellow_year_vip')


class WeiBoUserView(ModelView):
    show_popover = True
    column_default_sort = ('created', True)
    column_list = (
        'user', 'uid', 'subscribe', 'subscribe_time', 'follow',
        'access_token', 'expires_in', 'refresh_token', 'modified', 'created'
    )
    column_center_list = (
        'user', 'uid', 'subscribe', 'subscribe_time', 'follow', 'access_token',
        'expires_in', 'refresh_token', 'modified', 'created'
    )
    column_searchable_list = ('province', 'city',)
    column_filters = ('user', 'uid')


class UserLogView(ModelView):
    column_center_list = ('user', 'type', 'key', 'device', 'spm', 'ip', 'ua', 'created')
    column_searchable_list = ('key', 'device', 'spm', 'ip')
    column_filters = ('key', 'user', 'device', 'ip', 'ua', 'created')


class PhoneCodeView(ModelView):
    column_center_list = ('phone', 'action', 'code', 'ip', 'ua', 'error', 'created')
    column_filters = ('phone', 'action', 'code', 'ip', 'ua', 'error', 'created')
    column_searchable_list = ('phone',)


class EmailCodeView(ModelView):
    column_center_list = ('email', 'action', 'code', 'token', 'error', 'created')
