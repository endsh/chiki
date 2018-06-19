# coding: utf-8
import random
import functools
import traceback
from chiki.api import abort
from chiki.api.const import *
from chiki.base import db
from chiki.contrib.common import Item, Channel
from chiki.web import error
from chiki.utils import get_url_arg, is_json
from flask import current_app, request, redirect
from flask.ext.login import login_user, current_user, login_required

__all__ = [
    'init_wxauth', 'get_wechat_user', 'create_wechat_user',
    'wechat_login', 'on_wechat_login', 'on_invite',
    'wxauth_required',
]


def get_wechat_user(access, action='mp'):
    um = current_app.user_manager
    openid = '%s_openid' % action
    wxuser = None
    if 'unionid' in access and access['unionid']:
        wxuser = um.models.WeChatUser.objects(
            unionid=access['unionid']).first()
    if not wxuser:
        query = {openid: access['openid']}
        wxuser = um.models.WeChatUser.objects(**query).first()
    if wxuser and not getattr(wxuser, openid):
        setattr(wxuser, openid, access['openid'])
        wxuser.save()
    return wxuser


def create_wechat_user(userinfo, action):
    um = current_app.user_manager
    return um.models.WeChatUser.create(userinfo, action)


def wechat_login(wxuser):
    um = current_app.user_manager
    model = um.config.oauth_model
    if model == 'auto' and not wxuser.current:
        um.models.User.from_wechat(wxuser)
    wxuser.update()


def on_invite(user, uid):
    um = current_app.user_manager
    if not user.inviter and uid and uid != user.id:
        inviter = um.models.User.objects(id=uid).first()
        if inviter and inviter.active and inviter.is_allow_invite(user):
            ids = []
            ids.append(inviter.inviter.id if inviter.inviter else 0)
            ids.append(inviter.inviter2.id if inviter.inviter2 else 0)
            ids.append(inviter.inviter3.id if inviter.inviter3 else 0)
            if user.id not in ids:
                if inviter.is_allow_channel(user):
                    user.channel = inviter.channel
                else:
                    user.channel = 1000
                inviter.on_invite(user)
                user.inviter = inviter
                user.inviter2 = inviter.inviter
                user.inviter3 = inviter.inviter2
                user.save()

                subs = list(um.models.User.objects(inviter=user.id).all())
                for x in subs:
                    x.inviter2 = user.inviter
                    x.inviter3 = user.inviter2
                    x.save()

                subs2 = list(um.models.User.objects(inviter__in=subs).all())
                for x in subs2:
                    x.inviter2 = user
                    x.inviter3 = user.inviter
                    x.save()

        if not inviter and uid < 100000:
            if not user.channel:
                channel = Channel.objects(id=uid).first()
                if channel:
                    user.channel = channel.id
                    user.inviter = um.models.User(id=100000)
                    user.save()
            else:
                user.channel = 1000
                user.inviter = um.models.User(id=100000)
                user.save()


def on_wechat_login(action, next):
    um = current_app.user_manager
    if current_user.is_authenticated() and \
            current_user.is_user() and \
            not current_user.inviter:
        try:
            uid = request.cookies.get('inviter', 0, int) or get_url_arg(next, 'uid') or request.args.get('uid', 0, int)
            um.funcs.on_invite(current_user, int(uid))
        except:
            current_app.logger.error(traceback.format_exc())


def wxauth_required(key=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wxuser = current_user.wechat_user
            if wxuser:
                if not key:
                    auth = current_app.wxauth.puppet
                    if auth and auth.holder:
                        field = 'mp_openid_%s' % auth.key
                        if not getattr(wxuser, field):
                            return auth.auth(auth.ACTION_MP, request.url)
                elif key == 'all':
                    for k, auth in current_app.wxauth.puppets.iteritems():
                        field = 'mp_openid_%s' % k
                        if not getattr(wxuser, field):
                            return auth.auth(auth.ACTION_MP, request.url)
                else:
                    auth = current_app.wxauth.puppets.get(key)
                    if auth:
                        field = 'mp_openid_%s' % key
                        if not getattr(wxuser, field):
                            return auth.auth(auth.ACTION_MP, request.url)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def init_wxauth(app):
    if not hasattr(app, 'wxauth'):
        return

    wxauth = app.wxauth
    um = app.user_manager

    @wxauth.success_handler
    def wxauth_success(action, scope, access, next):
        user = um.funcs.get_wechat_user(access, action)
        if not user:
            if um.config.userinfo:
                if wxauth.SNSAPI_USERINFO not in access['scope'] \
                        and wxauth.SNSAPI_LOGIN not in access['scope']:
                    return wxauth.auth(action, next, wxauth.SNSAPI_USERINFO)

                userinfo = wxauth.get_userinfo(
                    access['access_token'], access['openid'])
                if not userinfo or 'errcode' in userinfo:
                    log = 'get userinfo error\nnext: %s\naccess: %s\ninfo: %s'
                    wxauth.app.logger.error(
                        log % (next, str(access), str(userinfo)))
                    return wxauth.error(
                        wxauth.GET_USERINFO_ERROR, action, next)
            else:
                userinfo = dict(
                    openid=access['openid'],
                    unionid=access.get('unionid', ''),
                )

            user = um.funcs.create_wechat_user(userinfo, action)

            if um.config.allow_redirect:
                uid = int(get_url_arg(next, 'uid') or 0)
                value = Item.get('redirect_rate', 100, name='跳转概率')
                empty = Item.get('redirect_empty_rate', 100, name='空白跳转')
                if uid == 0 and random.randint(1, 100) > empty or \
                        uid != 0 and random.randint(1, 100) > value:
                    user.groupid = 1
                    user.save()

        if um.config.allow_redirect and user.groupid == 1:
            return redirect(Item.data('redirect_url', '', name='跳转链接'))

        um.funcs.wechat_login(user)

        if user.user:
            real_user = um.models.User.objects(id=user.user).first()
            if not real_user:
                user.user = 0
                user.save()
            else:
                user = real_user

        login_user(user, remember=True)

        if user.is_user() and not user.active:
            return error(msg=Item.data(
                'active_alert_text', '您的帐号已被封号处理！', name='封号提示'))

        if current_user.is_authenticated() and current_user.is_user():
            um.models.UserLog.login(user.id, 'web', 'wechat')
            user.login()

        return um.funcs.on_wechat_login(action, next)

    @wxauth.error_handler
    def wxauth_error(err, action, next):
        if is_json():
            abort(WXAUTH_ERROR, wxcode=err, wxmsg=wxauth.MSGS.get(err, '未知错误'))

        return error('微信授权失败')

    db.abstract(um.models.WeChatUser)

    meta = {
        'indexes': [
            'user',
            'unionid',
            'mp_openid',
            'mobile_openid',
            'qrcode_openid',
            '-modified',
            '-created',
        ],
    }
    attrs = dict(meta=meta, __doc__='微信模型')
    for key, auth in wxauth.puppets.iteritems():
        field = 'mp_openid_%s' % key
        attrs[field] = db.StringField(verbose_name='%s公众号' % key)
        meta['indexes'].append(field)

        def success(field, action, scope, access, next, config=None):
            @login_required
            def callback():
                wxuser = current_user.wechat_user
                if wxuser:
                    setattr(wxuser, field, access['openid'])
                    wxuser.save()
            return callback()
        auth.success_handler(functools.partial(success, field))

    WeChatUser = type('WeChatUser', (um.models.WeChatUser, ), attrs)
    um.add_model(WeChatUser)

    if hasattr(app, 'cool_manager'):
        app.cool_manager.add_model(WeChatUser)
