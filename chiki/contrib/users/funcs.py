# coding: utf-8
import re
import urllib
from flask import current_app, url_for, render_template_string
from flask.ext.mail import Message
from chiki.sms import send_rong_sms, send_ihuyi_sms, send_jisu_sms


__all__ = [
    'send_sms', 'send_mail',
]

access_email_html = u"""
<div>
    <p>您好：</p>
    <p><a href="mailto:{{ email }}">{{ email }}</a> 在 {{ site_name }} 创建了账号, 所以我们发送这封邮件进行确认.</p>
    <p>您的验证码为: <span style="font-weight:bold">{{ code }}</span> , 复制或直接通过以下链接验证你的邮箱:</p>
    <p><a href="{{ url }}" target="_blank">{{ url }}</a></p>
    <p></p>
    <p>(这是一封自动产生的email，请勿回复)</p>
</div>
"""

reset_email_html = u"""
<div>
    <p><a href="mailto:{{ email }}">{{ email }}</a>, 你好！</p>
    <p>您的验证码为: <span style="font-weight:bold">{{ code }}</span> , 复制或直接通过以下链接重置密码：</p>
    <p></p>
    <p><a href="{{ url }}" target="_blank">{{ url }}</a></p>
    <p></p>
    <p>(这是一封由 {{ site_name }} 自动产生的email，请勿回复)</p>
</div>
"""

bind_email_html = u"""
<div>
    <p><a href="mailto:{{ email }}">{{ email }}</a>, 你好！</p>
    <p>您的验证码为: <span style="font-weight:bold">{{ code }}</span> , 复制或直接通过以下链接绑定邮箱：</p>
    <p></p>
    <p><a href="{{ url }}" target="_blank">{{ url }}</a></p>
    <p></p>
    <p>(这是一封由 {{ site_name }} 自动产生的email，请勿回复)</p>
</div>
"""


def send_sms(code):
    if current_app.debug:
        print '验证码：', code.phone, code.code
        return

    tpl = current_app.config.get('SMS_TPL')
    if current_app.config.get('SMS_IHUYI'):
        res = send_ihuyi_sms(code.phone, tpl % code.code)
    elif current_app.config.get('SMS_JISU'):
        res = send_jisu_sms(code.phone, tpl % code.code)
    else:
        res = send_rong_sms(code.phone, [str(code.code)], tpl)
    return res


def send_mail(code):
    if code.action == code.ACTION_REGISTER:
        tpl, title, endpoint = access_email_html, u'%s - 邮箱验证', 'users.register_email'
    elif code.action == code.ACTION_RESET_PASSWORD:
        tpl, title, endpoint = reset_email_html, u'%s - 重置密码', 'users.reset_password_email'
    else:
        tpl, title, endpoint = bind_email_html, u'%s - 绑定邮箱', 'users.bind'

    msg = Message(
        title % current_app.config.get('SITE_NAME'),
        sender=current_app.config.get('SERVICE_EMAIL'),
        recipients=[code.email])
    url = url_for(endpoint, token=code.token, _external=True)
    msg.html = render_template_string(
        tpl,
        email=code.email,
        site_name=current_app.config.get('SITE_NAME'),
        url=url,
        code=code.code,
    ).encode('utf-8')

    if current_app.debug:
        current_app.logger.info(msg.html)
        return

    current_app.mail.send(msg)
