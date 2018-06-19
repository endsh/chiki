# coding: utf-8
from chiki.base import db
from chiki.utils import sign
from datetime import datetime
from flask import current_app, request
from werkzeug.utils import cached_property
from chiki.utils import get_ip, get_spm


class AdminUser(db.Document):
    """ 管理员 """

    xid = db.IntField(verbose_name='XID')
    username = db.StringField(verbose_name='用户')
    password = db.StringField(verbose_name='密码')
    group = db.ReferenceField('Group', verbose_name='组')
    root = db.BooleanField(default=False, verbose_name='超级管理员')
    active = db.BooleanField(default=True, verbose_name='激活')
    freezed = db.DateTimeField(verbose_name='冻结时间')
    logined = db.DateTimeField(default=datetime.now, verbose_name='登录时间')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.username

    def is_user(self):
        return True

    def is_authenticated(self):
        """ 是否登录 """
        return True

    def is_active(self):
        """ 是否激活 """
        return self.active

    def is_anonymous(self):
        """ 是否游客 """
        return False

    def get_id(self):
        s = sign(current_app.config.get('SECRET_KEY'), password=self.password)
        return '{0}|{1}'.format(self.id, s)


class Group(db.Document):
    """ 管理组 """

    name = db.StringField(verbose_name='组名')
    power = db.ListField(db.ReferenceField('View'), verbose_name='使用权限')
    can_create = db.ListField(db.ReferenceField('View'), verbose_name='创建权限')
    can_edit = db.ListField(db.ReferenceField('View'), verbose_name='编辑权限')
    can_delete = db.ListField(db.ReferenceField('View'), verbose_name='删除权限')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.name

    @cached_property
    def power_list(self):
        return [x.name for x in self.power]

    @cached_property
    def can_create_list(self):
        return [x.name for x in self.can_create]

    @cached_property
    def can_edit_list(self):
        return [x.name for x in self.can_edit]

    @cached_property
    def can_delete_list(self):
        return [x.name for x in self.can_delete]


class AdminUserLoginLog(db.Document):
    """ 管理登录日志 """

    TYPE = db.choices(login='登录', logout='退出', error='密码错误')

    user = db.ReferenceField('AdminUser', verbose_name='用户')
    type = db.StringField(choices=TYPE.CHOICES, verbose_name='类型')
    spm = db.StringField(max_length=100, verbose_name='SPM')
    ip = db.StringField(max_length=20, verbose_name='IP')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return '%s' % self.user.username

    @staticmethod
    def log(user, type, spm=None, ip=None):
        spm = spm if spm else get_spm()
        ip = ip if ip else get_ip()
        AdminUserLoginLog(user=user, type=type, spm=spm, ip=ip).save()

    @staticmethod
    def login(user):
        AdminUserLoginLog.log(user, AdminUserLoginLog.TYPE.LOGIN)

    @staticmethod
    def logout(user):
        AdminUserLoginLog.log(user, AdminUserLoginLog.TYPE.LOGOUT)

    @staticmethod
    def error(user):
        AdminUserLoginLog.log(user, AdminUserLoginLog.TYPE.ERROR)


class AdminChangeLog(db.Document):
    """ 管理员操作日志 """

    TYPE = db.choices(edit='修改', created='创建', delete='删除')

    user = db.ReferenceField('AdminUser', verbose_name='用户')
    model = db.StringField(verbose_name='模块')
    before_data = db.StringField(verbose_name='操作前')
    after_data = db.StringField(verbose_name='操作后')
    type = db.StringField(verbose_name='类型', choices=TYPE.CHOICES)
    spm = db.StringField(verbose_name='spm')
    ip = db.StringField(verbose_name='IP')
    headers = db.StringField(verbose_name='头信息')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    @staticmethod
    def log(user, model, before_data, after_data, type, **kwargs):
        ip = kwargs.get('ip', get_ip())
        spm = kwargs.get('spm', get_spm())
        headers = kwargs.get('headers', request.headers)
        AdminChangeLog(
            user=user, model=model, before_data=before_data,
            after_data=after_data, type=type, ip=ip, spm=spm,
            headers=str(headers)
        ).save()

    @staticmethod
    def modify_data(user, model, **kwargs):
        # 使用 before = after = dict(id=model.id) 到有内存引用的问题
        before = dict(id=model.id)
        after = dict(id=model.id)
        if kwargs.get('form'):
            try:
                for k, v in kwargs.get('form').data.iteritems():
                    if v != model[k]:
                        before[k] = model[k]
                        after[k] = v
            except:
                pass
        else:
            before = model.to_mongo()
        if kwargs.get('type') == 'delete':
            after = ''
        AdminChangeLog.log(
            user=user, model=model.__class__.__name__,
            before_data=str(before), after_data=str(after),
            type=kwargs.get('type'),
        )

    @staticmethod
    def dropdown_modify(user, model, **kwargs):
        before_data = dict(id=kwargs.get('id'))
        after_data = dict(id=kwargs.get('id'))
        key = kwargs.get('key')
        before_data[key] = kwargs.get('before_data')
        after_data[key] = kwargs.get('after_data')

        AdminChangeLog.log(
            user=user, model=model.__name__, before_data=str(before_data),
            after_data=str(after_data), type='edit', what='waht')
