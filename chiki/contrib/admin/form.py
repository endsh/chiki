#coding: utf-8
from datetime import datetime
from chiki.forms import Form
from chiki.utils import today
from wtforms import BooleanField, PasswordField, TextField
from chiki.forms import Strip, Lower, DataRequired
from .models import AdminUser, AdminUserLoginLog


class LoginForm(Form):
    account = TextField('用户名/邮箱/手机',
                        validators=[Strip(), Lower(), DataRequired()])
    password = PasswordField('密码', validators=[])
    remember = BooleanField('记住登录状态')

    def validate_account(self, field):
        admin = AdminUser.objects(
            username=self.account.data).first()
        if not admin:
            raise ValueError('用户不存在')
        if not admin.active:
            raise ValueError('用户被冻结')
        if admin.password != self.password.data:
            AdminUserLoginLog.error(admin.id)
            count = AdminUserLoginLog.objects(
                created__gte=max(today(), admin.freezed or today()),
                user=admin.id,
                type=AdminUserLoginLog.TYPE.ERROR).count()
            if count >= 20:
                admin.active = False
                admin.freezed = datetime.now()
                admin.save()
            raise ValueError('密码错误')

        self.admin = admin
