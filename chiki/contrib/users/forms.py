# coding: utf-8
from __future__ import unicode_literals
from chiki.contrib.users.base import user_manager
from chiki.forms import Form, VerifyCodeField
from chiki.forms import Strip, Lower, Length, DataRequired
from chiki.forms import Email, Regexp
from datetime import datetime, timedelta
from wtforms import BooleanField, PasswordField, TextField, HiddenField

__all__ = [
    'EmailForm', 'RegisterEmailForm', 'ResetPasswordEmailForm', 'BindEmailForm',
    'RegisterEmailAccessForm', 'ResetPasswordEmailAccessForm',
    'PhoneForm', 'RegisterPhoneForm', 'ResetPasswordPhoneForm', 'BindPhoneForm',
    'LoginForm',
]


class EmailForm(Form):
    """ 邮箱注册、绑定、重置密码 """

    email = TextField('邮箱')


class RegisterEmailForm(EmailForm):
    pass


class ResetPasswordEmailForm(EmailForm):
    pass


class BindEmailForm(EmailForm):
    authcode = TextField('验证码')
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, max=18),
        Regexp(
            r"""^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$""",
            message='密码只能包含英文字符，数字或其他可见符号'
        ),
    ])
    repassword = PasswordField('确认密码', validators=[DataRequired()])


class RegisterEmailAccessForm(EmailForm):
    authcode = HiddenField('验证码')
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, max=18),
        Regexp(
            r"""^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$""",
            message='密码只能包含英文字符，数字或其他可见符号'
        ),
    ])
    repassword = PasswordField('确认密码', validators=[DataRequired()])


class ResetPasswordEmailAccessForm(EmailForm):
    authcode = HiddenField('验证码')
    password = PasswordField('新密码', validators=[
        DataRequired(),
        Length(min=6, max=18),
        Regexp(
            r"""^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$""",
            message='密码只能包含英文字符，数字或其他可见符号'
        ),
    ])
    repassword = PasswordField('确认密码', validators=[DataRequired()])


class PhoneForm(Form):
    """ 手机注册、绑定、重置密码 """

    phone = TextField('手机', validators=[
        Strip(),
        DataRequired(),
        Regexp(
            r"""^1\d{10}$""",
            message='手机号码不正确'
        ),
    ])
    authcode = TextField('手机验证码')
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, max=18),
        Regexp(
            r"""^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$""",
            message='密码只能包含英文字符，数字或其他可见符号'
        ),
    ])


class RegisterPhoneForm(PhoneForm):
    verify_code = VerifyCodeField('验证码', key='users_register_phone')
    password = PasswordField('密码',
        validators=[
            DataRequired(),
            Length(min=6, max=18),
            Regexp(
                r"""^[\w\d\-\[\]{}|\\,.\/<>;:'"_`~!@#$%^&*()+= ]+$""",
                message='密码只能包含英文字符，数字或其他可见符号'
            ),
        ],
    )


class ResetPasswordPhoneForm(PhoneForm):
    verify_code = VerifyCodeField('验证码', key='users_reset_password_phone')
    repassword = PasswordField('确认密码', validators=[DataRequired()])


class BindPhoneForm(PhoneForm):
    verify_code = VerifyCodeField('验证码', key='users_bind_phone')
    repassword = PasswordField('确认密码', validators=[DataRequired()])


class LoginForm(Form):
    """ 用户登录 """

    account = TextField('邮箱/手机', validators=[
        Strip(),
        Lower(),
        DataRequired(),
    ])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住登录状态')
