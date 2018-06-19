# coding: utf-8
from chiki.utils import json_error
from chiki.web import error
from chiki.contrib.users.base import user_manager as um
from flask import Blueprint, request, render_template, redirect
from flask import url_for, current_app
from flask.ext.login import current_user, login_user, logout_user, login_required

bp = Blueprint('users', __name__)


@bp.route('/register.html')
def register():
    next = request.args.get('next', url_for('users.login'))
    if current_user.is_authenticated():
        return redirect(next)

    if current_app.config.get('REGISTER_WECHAT') and hasattr(current_app, 'wxauth'):
        ua = request.headers.get('User-Agent', '').lower()
        if 'micromessenger' in ua and '192.168' not in request.host:
            return current_app.wxauth.auth(current_app.wxauth.ACTION_MP, next)

    email_form = um.forms.RegisterEmailForm()
    phone_form = um.forms.RegisterPhoneForm()
    return render_template(
        um.tpls.register,
        next=next, email_form=email_form, phone_form=phone_form
    )


@bp.route('/register/email.html')
def register_email():
    next = request.args.get('next', url_for('users.login'))
    if current_user.is_authenticated():
        return redirect(next)

    token = request.args.get('token')
    code = um.models.EmailCode.get(token)
    if not code:
        return error('该链接已过期')

    form = um.forms.RegisterEmailAccessForm()
    form.email.data = code.email
    form.authcode.data = code.code
    return render_template(
        um.tpls.register_email,
        next=next, code=code, form=form
    )


def login_from_account(next):
    form = um.forms.LoginForm()
    if not um.allow_email or not um.allow_phone:
        form.account.label.text = '帐号'
    return render_template(um.tpls.login, form=form)


@bp.route('/login.html')
def login():
    """ 用户登录 """
    next = request.args.get('next', um.config.login_next or '/')
    if current_user.is_authenticated():
        return redirect(next)

    if next and not next.startswith('http://'):
        next = 'http://%s%s' % (request.host, next)

    if current_app.config.get('WEB_LOGIN_RES_CODE', False):
        return json_error(msg='请登录', login=False)

    if hasattr(current_app, 'ipay'):
        ipay = current_app.ipay
        if ipay.auto_auth:
            return ipay.auth(next)

    if hasattr(current_app, 'wxauth'):
        wxauth = current_app.wxauth
        action = request.args.get('action', '')
        if action == 'account':
            return login_from_account(next)
        if action == 'mp':
            return wxauth.auth(wxauth.ACTION_MP, next)
        if action == 'qrcode':
            return wxauth.auth(wxauth.ACTION_QRCODE, next)

        ua = request.headers.get('User-Agent', '').lower()
        if 'micromessenger' in ua and '192.168' not in request.host \
                and um.config.auto_wxauth:
            return wxauth.auth(wxauth.ACTION_MP, next)

    return login_from_account(next)


@bp.route('/logout.html')
def logout():
    next = request.args.get('next', url_for('users.login'))
    if current_user.is_authenticated():
        logout_user()
    return redirect(next)


@bp.route('/reset_password.html')
def reset_password():
    next = request.args.get('next', url_for('users.login'))
    if current_user.is_authenticated():
        return redirect(next)

    email_form = um.forms.ResetPasswordEmailForm()
    phone_form = um.forms.ResetPasswordPhoneForm()
    return render_template(
        um.tpls.reset_password,
        next=next, email_form=email_form, phone_form=phone_form
    )


@bp.route('/reset_password/email.html')
def reset_password_email():
    next = request.args.get('next', url_for('users.login'))
    if current_user.is_authenticated():
        return redirect(next)

    token = request.args.get('token')
    code = um.models.EmailCode.get(token)
    if not code:
        return error('该链接已过期')

    form = um.forms.ResetPasswordEmailAccessForm()
    form.email.data = code.email
    form.authcode.data = code.code
    return render_template(
        um.tpls.reset_password_email,
        next=next, code=code, form=form
    )


@bp.route('/bind.html')
@login_required
def bind():
    next = request.args.get('next', url_for('users.login'))
    if not um.need_email and not um.need_phone:
        return redirect(next)

    if not current_user.is_user() and current_user.user:
        user = um.models.User.objects(id=current_user.user).first()
        if user:
            login_user(user)
            return redirect(next)
        current_user.user = 0
        current_user.save()

    email_form = um.forms.BindEmailForm()
    phone_form = um.forms.BindPhoneForm()
    return render_template(
        um.tpls.bind, next=next, email_form=email_form, phone_form=phone_form)


@bp.route('/wechat-test.html')
def wechat_test():
    wxuser = um.models.WeChatUser.objects(mp_openid='wechat-test').first()
    if not wxuser:
        wxuser = um.models.WeChatUser(mp_openid='wechat-test')
        wxuser.save()
    wxuser.user = None
    wxuser.save()

    login_user(wxuser)
    next = request.args.get('next', um.config.login_next or '/')
    return redirect(next)

