# coding: utf-8
from xml.sax.saxutils import escape as _escape, quoteattr
from markupsafe import Markup
from ..iptools import parse_ip
from ..jinja import markup, markupper
from ..utils import datetime2best, time2best
from ..mongoengine.fields import ImageProxy, Base64ImageProxy


def quote(*args):
    return tuple(quoteattr(unicode(x)) for x in args)


def escape(*args):
    return tuple(_escape(unicode(x)) for x in args)


def get_span(text, short, cls=''):
    if text.startswith('http://'):
        return '<a class=%s href=%s title=%s target="_blank">%s</a>' % (
            quote(cls, text, text) + escape(short))
    return '<span class=%s title=%s>%s</span>' % (quote(cls, text) + escape(short))


def get_link(text, link, max_len=20, blank=True, html=False, **kwargs):
    if 'class_' in kwargs:
        kwargs['class'] = kwargs.pop('class_')
    attrs = dict()
    for k, v in kwargs.items():
        attrs[k.replace('_', '-')] = v

    tpl = u'<a %shref=%s title=%s target="_blank">%s</a>'
    if not blank:
        tpl = u'<a %shref=%s title=%s>%s</a>'
    if text or type(text) == int:
        extras = ' '.join('%s=%s' % (x, quoteattr(unicode(y))) for x, y in attrs.iteritems())
        extras = extras + ' ' if extras else ''
        if html:
            short = text
            text = ''
        else:
            short = unicode(text)[:max_len] + '...' if len(unicode(text)) > max_len else unicode(text)
        return tpl % ((extras,) + quote(link, text) + (escape(short) if not html else (short,)))
    return ''


def popover(content, short=None, title=None, placement='right', html=False):
    short = title if short is None else short
    if not html:
        short = escape(short)
    else:
        short = (short,)
    return '<a href="javascript:;" data-container="body" data-toggle="popover" ' \
        'data-trigger="focus" data-placement=%s title=%s data-content=%s data-html="true">%s</a>' % (
            quote(placement, title or '', content) + short)


def formatter(func):
    def wrapper(view, context, model, name):
        if hasattr(model.__class__, name):
            data = getattr(model, name)
            if data:
                return markup(func(data) or '')
        return ''
    return wrapper


def formatter_model(func):
    def wrapper(view, context, model, name):
        return markup(func(model) or '')
    return wrapper


def formatter_len(max_len=20, cls=''):
    @formatter
    def wrapper(data):
        data = unicode(data)
        if len(data) > max_len + 1:
            return get_span(data, data[:max_len] + '...', cls=cls)
        return data
    return wrapper


def formatter_text(func, max_len=20, cls=''):
    @formatter_model
    def span(model):
        xcls = ''
        res = func(model)
        if len(res) == 2:
            short, text = res
        else:
            short, text, xcls = res
        short, text = unicode(short), unicode(text)
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return get_span(text, short, cls=xcls or cls)
    return span


def formatter_popover(func, max_len=20, show_title=True):
    @formatter_model
    def span(model):
        res = func(model)
        if not res:
            return
        if isinstance(res, (tuple, list)):
            if len(res) == 3:
                short, title, content = res
            elif len(res) == 2:
                title, content = res
                short = title
        else:
            short, title, content = res, None, res
        short = short[:max_len] + '...' if len(short) > max_len + 1 else short
        return popover(content, title=title if show_title else None, short=short)
    return span


def formatter_icon(func=None, height=40, **kwargs):
    if 'class_' in kwargs:
        kwargs['class'] = kwargs.pop('class_')
    exts = ' '.join(['%s=%s' % ((k,) + quote(v)) for k, v in kwargs.iteritems()]) + ' '
    tpl = u'''
        <a href=%%s target="_blank" style="text-decoration:none">
            <img %ssrc=%%s style="max-height: %dpx; margin: -6px 0">
        </a>
    ''' % (exts, height)

    def icon(url):
        if url:
            if isinstance(url, list):
                return ''.join([icon(u) for u in url])
            if isinstance(url, tuple):
                if url[0] and url[1]:
                    return tpl % quote(url[1], url[0])
            else:
                return tpl % quote(url, url)
        return ''

    @formatter_model
    def wrapper(model):
        return icon(func(model))

    return wrapper


def formatter_link(func, max_len=20, blank=True, html=False, **kwargs):

    @formatter_model
    def wrapper(model):
        attrs = dict(**kwargs)
        for k, v in attrs.items():
            if callable(v):
                attrs[k] = v(model)

        res = func(model)
        if isinstance(res, list):
            return ','.join([get_link(x[0], x[1], max_len, blank, html, **attrs) for x in res])
        return get_link(res[0], res[1], max_len, blank, html, **attrs)

    return wrapper


def formatter_ip(url=None, blank=True):
    tpl = '<a href=%s title=%s target="_blank">%s</a>'
    if not blank:
        tpl = '<a href=%s title=%s>%s</a>'

    @formatter
    def wrapper(ip):
        if ip:
            text = parse_ip(ip)
            if url:
                href = url(ip) if callable(url) else url % dict(ip=ip)
                return tpl % (quote(href, ip) + escape(text))
            return '<span title=%s>%s</span>' % (quote(ip) + escape(text))
    return wrapper


@formatter
def format_time(t):
    return str(t).split('.')[0]


@formatter
def format_date(t):
    return str(t).split(' ')[0]


@formatter
def format_best(t):
    return get_span(str(t).split('.')[0], datetime2best(t))


@formatter
def format_rmb(m):
    return '￥%.2f' % (m / 100.0)


def format_choices(view, context, model, name):
    if hasattr(model.__class__, name):
        field = getattr(model.__class__, name)
        data = getattr(model, name)
        choices = field.choices
        if choices:
            return dict(choices).get(data, data)


@markupper
def type_best(view, t):
    return get_span(str(t).split('.')[0], datetime2best(t))


@markupper
def type_image(view, image):
    return format_image(image)


def format_image(image, link=True):
    if link:
        tpl = u'''
            <a href=%s target="_blank" style="text-decoration:none">
                <img src=%s style="max-height: 40px; margin: -6px 0">
            </a>
        '''
        if image and image.link:
            return tpl % quote(image.link, image.get_link(40, 40))
        return ''

    tpl = u'''
        <img src=%s style="max-height: 40px; margin: -6px 0">
    '''
    if image and image.link:
        return tpl % quote(image.get_link(40, 40))
    return ''


def format_images(images):
    tpl = u'''
        <a href=%s title=%s target="_blank" style="text-decoration:none; display: inline-block;">
            <img src=%s style="width: 75px; height: 60px; margin: 0 3px 6px 0;border: 1px solid #ddd;">
        </a>
    '''
    html = []
    for image in images:
        html.append(tpl % quote(
            image.get_link(), image.get_link(), image.get_link(75, 60)))
    return ''.join(html)


@markupper
def type_file(view, proxy):
    if isinstance(proxy, ImageProxy) or isinstance(proxy, Base64ImageProxy):
        return type_image(view, proxy)
    return get_link(proxy.filename, proxy.link, max_len=60)


@markupper
def type_images(view, images):
    return popover(format_images(images), '%d张' % len(images))


@markupper
def type_select(view, value, model, name, choices):
    selects = ''
    url = view.get_url('.dropdown')
    id = str(model.id)+str(name)

    for k, v in choices.items():
        select = '<li><a class="btn-formatter" data-key="%s" data-id="%s" data-name="%s" data-url="%s">%s</a></li>' % (k, model.id, name, url, v)
        selects = selects + select

    html = '''<div class="dropdown" style="min-width: 80px">
                <button id=%s class="btn btn-block btn-select" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" s>%s
                    <span class="caret"></span>
                </button>
                <ul class="dropdown-menu" aria-labelledby="dLabel" style="min-width:100px">%s</ul>
            </div>''' % (id, choices.get(str(value) if type(value) is Markup else value), selects)

    return html


@markupper
def type_bool(view, value, model, name):
    FA_CHECK = '<i class="fa fa-check-circle text-success"></i>'
    FA_MINUS = '<i class="fa fa-minus-circle text-danger"></i>'
    url = view.get_url('.dropdown')
    val = str(value)

    html = """<a class="btn btn-default btn-sm btn-active" target="_blank" data-id="%s" data-name="%s" data-value="%s" data-url="%s">
        %s
        </a>""" % (model.id, name, val, url, FA_CHECK if value else FA_MINUS)
    return html


def filter_sort(column_filters, column_list):
    if not column_list or column_list is None:
        return column_filters
    c = dict((y, x) for x, y in enumerate(column_list))
    res = dict()
    for x in column_filters:
        if x in column_list:
            res[x] = c.get(x, 10000)
    e = sorted(res.iteritems(), key=lambda x: x[1])
    new_list = list()
    if 'id' not in column_filters:
        new_list.append('id')
    for x, y in e:
        new_list.append(x)
    return new_list
