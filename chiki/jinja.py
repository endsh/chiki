# coding: utf-8
import re
import json
import traceback
from datetime import datetime
from flask import current_app, get_flashed_messages
from jinja2 import Markup
from xml.sax.saxutils import escape
from .utils import time2best as _time2best, is_ajax, url_with_user

__all__ = [
    'markup', 'markupper', 'first_error', 'text2html',
    'JinjaManager', 'init_jinja',
]

regex = re.compile(
    r'((?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:[a-zA-Z0-9\-\/._~%!$&()*+]+)?'
    r'(?:\?[a-zA-Z0-9&%=.\-!@^*+-_]+)?)', re.IGNORECASE)


def markup(html):
    return Markup(html) if current_app.jinja_env.autoescape else html


def markupper(func):
    def wrapper(*args, **kwargs):
        return markup(func(*args, **kwargs))
    return wrapper


def first_error(form):
    if form:
        for field in form:
            if field.errors:
                return field.errors[0]


def replace_link(link):
    if link.startswith('http://') or link.startswith('https://'):
        return '<a class="link" href="%s">%s</a>' % (escape(link), escape(link))
    return escape(link)


def text2html(text):
    try:
        out = ['']
        for line in text.splitlines():
            if not line.strip():
                out.append('')
                continue
            texts = [replace_link(x) for x in regex.split(line)]
            out[-1] += ''.join(texts) + '<br>'
        return ''.join(u'<p>%s</p>' % x for x in filter(lambda x: x.strip, out))
    except:
        traceback.print_exc()
        return escape(text)


class JinjaManager(object):

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.jinja_env.filters.update(self.filters)
        app.context_processor(self.context_processor)

    @property
    def filters(self):
        return dict(
            time2best=self.time2best,
            time2date=self.time2date,
            line2br=self.line2br_filter,
            text2html=self.text2html_filter,
            kform=self.kform_filter,
            kfield=self.kfield_filter,
            kform_inline=self.kform_inline_filter,
            kfield_inline=self.kfield_inline_filter,
            alert=self.alert_filter,
            rmb=self.rmb_filter,
            rmb2=self.rmb2_filter,
            rmb3=self.rmb3_filter,
            best_num=self.best_num_filter,
            json=json.dumps,
            cdn=self.cdn_filter,
            repr=self.repr,
            url_with_user=url_with_user,
            show_hex=self.show_hex,
        )

    def context_processor(self):
        return dict(
            SITE_NAME=current_app.config.get('SITE_NAME'),
            VERSION=current_app.config.get('VERSION'),
            YEAR=datetime.now().year,
            alert=self.alert_filter,
            is_ajax=is_ajax,
            current_app=current_app,
            str=str,
            repr=self.repr,
            callable=callable,
            len=len,
        )

    def line2br_filter(self, text):
        return markup(escape(text).replace('\n', '<br>'))

    def text2html_filter(self, text):
        return markup(text2html(text))

    def kform_filter(self, form, **kwargs):
        out = []
        for field in form:
            out.append(self.kfield_filter(field, **kwargs))
        return markup(''.join(out))

    def kfield_filter(self, field, **kwargs):
        label = kwargs.pop('label', 3)
        grid = kwargs.pop('grid', 'sm')
        _class = kwargs.pop('_class', 'form-group')
        error = kwargs.pop('error', True)
        label_class = 'control-label col-%s-%d' % (grid, label)
        out = []
        if field.type == 'Label':
            out.append(field(class_='form-title'))
        elif field.type not in['CSRFTokenField', 'HiddenField']:
            out.append('<div class="%s">' % _class)
            out.append(field.label(class_=label_class))
            if field.type == 'KRadioField':
                field_div = '<div class="col-%s-%d radio-line">' % (grid, (12 - label))
                out.append(field_div)
                out.append(field(sub_class='radio-inline', class_="radio-line"))
            elif field.type == 'KCheckboxField':
                field_div = '<div class="col-%s-%d checkbox-line">' % (grid, (12 - label))
                out.append(field_div)
                out.append(field(sub_class='checkbox-inline', class_="checkbox-line"))
            else:
                field_div = '<div class="col-%s-%d">' % (grid, (12 - label))
                out.append(field_div)
                if hasattr(field, 'addon'):
                    out.append('<div class="input-group">')
                    out.append(field(class_='form-control', data_label=field.label.text, placeholder=field.description or ''))
                    out.append('<span class="input-group-addon">%s</span>' % field.addon)
                    out.append('</div>')
                else:
                    out.append(field(class_='form-control', data_label=field.label.text, placeholder=field.description or ''))
            if error and field.errors:
                out.append('<div class="error-msg">%s</div>' % field.errors[0])
            out.append('</div><div class="clearfix"></div></div>')
        else:
            out.append(field())
        return markup(''.join(out))

    def kform_inline_filter(self, form):
        out = []
        for field in form:
            out.append(self.kfield_inline_filter(field))
        return markup(''.join(out))

    def kfield_inline_filter(self, field, **kwargs):
        out = []
        if field.type in ['CSRFTokenField', 'HiddenField']:
            out.append(field(**kwargs))
        else:
            out.append('<div class="form-group">')
            if field.type == 'BooleanField':
                out.append('<div class="checkbox"><label>%s %s</label></div>'
                    % (field(**kwargs), field.label.text))
            else:
                kwargs.setdefault('class_', 'form-control')
                kwargs.setdefault('data_label', field.label.text)
                kwargs.setdefault('placeholder', field.label.text)
                out.append(field(**kwargs))
            out.append('</div>')
        return markup(''.join(out))

    def alert_msg(self, msg, style='danger'):
        return markup('<div class="alert alert-%s"><button class="close" '
            'type="button" data-dismiss="alert" aria-hidden="true">&times;'
            '</button><span>%s</span></div>' % (style, msg))

    def alert_filter(self, form=None, style='danger'):
        error = first_error(form)
        if error:
            return self.alert_msg(error, style)

        messages = get_flashed_messages(with_categories=True)
        if messages and messages[-1][1] != 'Please log in to access this page.':
            return self.alert_msg(messages[-1][1], messages[-1][0] or 'danger')
        return ''

    def rmb_filter(self, money):
        return '%.2f' % money

    def rmb2_filter(self, money):
        return '%.2f' % (money / 100.0)

    def rmb3_filter(self, money):
        d = float('%.2f' % (money / 100.0))
        return str([str(d), int(d)][int(d) == d])

    def best_num_filter(self, num):
        if not num:
            return 0
        if num < 1000:
            return num
        if num < 100000:
            return '%.1fk' % (num / 1000.0)
        if num < 1000000:
            return '%.1fw' % (num / 10000.0)
        return '%dw' % (num / 10000)

    def time2best(self, input):
        return _time2best(input)

    def time2date(self, input):
        return str(input)[:10]

    def cdn_filter(self, url, width, height):
        url = current_app.config.get('LAZY_IMAGE', '')
        return url + ('@%sw_%sh_1e_1c_95Q.png' % (width, height))

    def show_hex(self, input):
        return ''.join(["\\x%s" % i.encode('hex') for i in input])

    def repr(self, text):
        res = repr(unicode(text))
        return unicode(res[2:-1])


def init_jinja(app):
    jinja = JinjaManager()
    jinja.init_app(app)
