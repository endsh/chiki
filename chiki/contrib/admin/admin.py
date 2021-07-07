# coding: utf-8
from chiki.base import db
from chiki.admin import ModelView
from chiki.admin.formatters import formatter_link, formatter_model


def format_info(m):
    return '姓名：%s<br>登陆账号：%s<br>登陆密码：%s<br>登陆网址：%s' % (
        m.name, m.username, m.password,
        db.Item.get('login_url', 'http://localhost/'))


class AdminUserView(ModelView):
    """ 管理员 """
    # can_edit = False
    # can_delete = False
    column_list = ('name', 'username', 'root', 'active', 'logined',
                   'modified', 'created', 'group', 'info')
    column_center_list = column_list
    column_formatters = dict(
        username=formatter_link(
            lambda m: (m.username, '/admin/adminchangelog/?flt1_2=%s' % m.id)),
        info=formatter_model(format_info),
    )


class GroupView(ModelView):
    """ 管理组 """
    column_center_list = ('name', 'modified', 'created')
    column_formatters = dict(
        name=formatter_link(
            lambda x: (x.name, '/admin/adminuser/?flt1_2=%s' % x.id)),
    )

    form_args = dict(
        power=dict(allow_blank=True),
        can_create=dict(allow_blank=True),
        can_edit=dict(allow_blank=True),
        can_delete=dict(allow_blank=True),
    )

    def __unicode__(self):
        return self.name


class AdminUserLoginLogView(ModelView):
    """ 管理登录日志 """

    can_edit = False
    can_delete = False
    column_center_list = ('user', 'type', 'spm', 'ip', 'created')

    def __unicode__(self):
        return '管理员登陆日志(%s)' % self.id


class AdminChangeLogView(ModelView):
    """ 管理员操作日志 """

    can_delete = False
    can_edit = False
    column_center_list = ('user', 'type', 'created')
    column_filters = ('user', 'model')

    def __unicode__(self):
        return '管理员操作日志(%s)' % self.id
