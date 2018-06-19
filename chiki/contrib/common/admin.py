# coding: utf-8
import json
import urllib
import os
import qrcode as _qrcode
import traceback
from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO
from chiki.admin import ModelView, formatter_len, formatter_icon, formatter
from chiki.admin import formatter_popover, formatter_model
from chiki.admin import formatter_text, formatter_link, popover, quote, escape
from chiki.admin import get_span
from chiki.jinja import markup
from chiki.forms.fields import WangEditorField, DragSelectField
from chiki.stat import statistics
from chiki.utils import json_success, json_error
from datetime import datetime
from wtforms.fields import TextAreaField, SelectField
from flask import current_app, url_for, request
from flask.ext.admin import expose
from flask.ext.admin.form import BaseForm
from .models import View, Item
from ...jinja import markupper

FA = '<i class="fa fa-%s"></i>'


@markupper
def type_bool(model):
    FA_CHECK = '<i class="fa fa-check-circle text-success"></i>'
    FA_MINUS = '<i class="fa fa-minus-circle text-danger"></i>'
    view = '/admin/item/dropdowns'
    name = 'value'
    value = model.value
    if value == 'false' or value == 'False' or value is False:
        value = False
    else:
        value = True
    html = """<a class="btn btn-default btn-sm btn-active" target="_blank" data-id="%s" data-name="%s" data-value="%s" data-url="%s">
        %s
        </a>""" % (model.id, name, value, view, FA_CHECK if value else FA_MINUS)
    return html


@formatter_model
def check_bool(model):
    print 'type: ', model.type
    if model.type == 'int':
        return model.value
    tof = ['true', 'false', 'True', 'False', True, False]
    if model.value in tof:
        return type_bool(model)
    else:
        data = unicode(model.value)
        if len(data) > 33:
            return get_span(data, data[:32] + '...')
        return model.value


class ItemView(ModelView):
    can_use = True
    column_default_sort = ('key', True)
    column_list = ('key', 'name',  'value', 'type', 'modified', 'created')
    column_center_list = ('type', 'modified', 'created')
    column_filters = ('key', 'modified', 'created')
    #column_formatters = dict(value=formatter_len(32))
    column_formatters = dict(value=check_bool)
    column_searchable_list = ('key', 'name')
    form_overrides = dict(value=TextAreaField)

    def pre_model_change(self, form, model, create=False):
        if model.type == model.TYPE_INT:
            try:
                self.value = int(form.value.data)
            except:
                self.value = int(model.value or 0)

    def on_model_change(self, form, model, create=False):
        if model.type == model.TYPE_INT:
            model.value = self.value

    def on_field_change(self, model, name, value):
        model[name] = value
        if hasattr(model, 'modified'):
            model['modified'] = datetime.now()

    @expose('/dropdowns')
    def dropdown(self):
        id = request.args.get('id', 0, unicode)
        val = request.args.get('key', '')
        name = request.args.get('name', '', unicode)
        value = request.args.get('value', '', unicode)
        model = self.model

        if not val:
            val = 'false' if value == 'false' or value == 'False' or value is False else 'true'
        if type(val) == int:
            val = int(val)

        obj = model.objects(id=id).first()
        if obj:
            self.on_field_change(obj, name, val)
            obj.save()
            return json_success()

        return json_error(msg='该记录不存在')


class StatLogView(ModelView):
    column_default_sort = ('created', True)
    column_list = ('key', 'tid', 'day', 'hour', 'value', 'modified', 'created')
    column_center_list = ('day', 'hour', 'modified', 'created', 'value')
    column_filters = ('key', 'tid', 'day', 'hour', 'value', 'modified', 'created')
    column_searchable_list = ('key', 'tid', 'day')


class TraceLogView(ModelView):
    column_default_sort = ('created', True)
    column_filters = ('key', 'tid', 'user', 'label', 'created')
    column_searchable_list = ('key', 'tid', 'label')
    column_center_list = ('user', 'created')
    column_formatters = dict(
        value=formatter_len(40),
    )


class ShareLogView(ModelView):
    column_default_sort = ('created', True)
    column_list = ('image', 'user', 'title', 'link', 'status', 'media', 'created')
    column_center_list = ('created', 'user', 'status', 'media', 'image')
    column_searchable_list = ('title', 'desc', 'link', 'image')
    column_filters = ('user', 'pos', 'title', 'desc', 'link', 'image', 'created')
    column_formatters = dict(
        image=formatter_icon(lambda m: m.image),
        title=formatter_text(lambda m: (m.title, m.desc, 'text-success' if m.desc else '')),
        )


class ImageItemView(ModelView):
    column_center_list = ('name', 'image', 'created')
    column_filters = ('created',)


def create_qrcode(url):
    A, B, C = 480, 124, 108
    qr = _qrcode.QRCode(
        version=2, box_size=10, border=1,
        error_correction=_qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    im = qr.make_image()
    im = im.convert("RGBA")
    im = im.resize((A, A), Image.BILINEAR)

    em = Image.new("RGBA", (B, B), "white")
    im.paste(em, ((A - B) / 2, (A - B) / 2), em)

    path = current_app.get_data_path('logo.jpg')
    if os.path.exists(path):
        with open(path) as fd:
            icon = Image.open(StringIO(fd.read()))
        icon = icon.resize((C, C), Image.ANTIALIAS)
        icon = icon.convert("RGBA")
        im.paste(icon, ((A - C) / 2, (A - C) / 2), icon)

    stream = StringIO()
    im.save(stream, format='png')
    return dict(stream=stream, format='png')


# def create_mini_code(model, content):
#     try:
#         conf = current_app.config.get("MINI_CODE_BG", {})
#         path = current_app.get_data_path(conf.get('path'))
#         with open(path) as fd:
#             bg = Image.open(StringIO(fd.read()))
#         im = Image.open(StringIO(content))
#         im = im.resize((conf.get('width'), conf.get('width')), Image.ANTIALIAS)
#         bg.paste(im, (conf.get('x'), conf.get('y')))

#         draw = ImageDraw.Draw(bg)
#         default = current_app.get_data_path('fonts/yh.ttf')
#         size = 18
#         font = ImageFont.truetype(default, size)
#         x = 10
#         y = 10
#         draw.text((x, y), 'ID: ' + str(model.id), font=font, fill='0xffffff')
#         del draw

#         stream = StringIO()
#         bg.save(stream, format='png')
#         return dict(stream=stream, format='png')
#     except:
#         current_app.logger.error(traceback.format_exc())


@statistics(modal=True)
class ChannelView(ModelView):
    column_labels = dict(stat='统计')
    column_list = ['id', 'name', 'password', 'url', 'image', 'modified', 'created', 'stat']
    column_center_list = ['id', 'image', 'modified', 'created', 'stat']
    form_excluded_columns = ('id',)
    column_searchable_list = ('name', 'url')

    column_formatters = dict(
        stat=formatter_link(lambda m: (
            '<i class="fa fa-line-chart"></i>',
            '/admin/channel/stat?%s' % urllib.urlencode(dict(id=str(m.id)))),
            html=True, class_='btn btn-default btn-sm',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
        url=formatter_link(lambda m: (
            'http://%s/outer/login/%d' % (current_app.config.get('WEB_HOST'), m.id),
            'http://%s/outer/login/%d' % (current_app.config.get('WEB_HOST'), m.id))
        ),
    )

    datas = dict(
        stat=[
            dict(title='注册用户', suffix='人', series=[
                dict(name='汇总', key='channel_user_new'),
            ]),
            dict(title='活跃用户', suffix='人', series=[
                dict(name='汇总', key='channel_user_active'),
            ]),
        ],
    )

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()
        model.create_image()


class QRCodeView(ModelView):
    column_list = ['user', 'image', 'url', 'scene', 'modified', 'created']
    column_center_list = ['user', 'image', 'scene', 'modified', 'created']
    column_filters = ['user', 'url', 'scene', 'modified', 'created']
    column_searchable_list = ('url',)

    def on_model_change(self, form, model, created=False):
        if model.user:
            model.get(model.user)


class AndroidVersionView(ModelView):
    column_default_sort = ('created', True)
    column_formatters = dict(
        log=formatter_len(),
        url=formatter_len(),
    )
    column_searchable_list = ('version',)
    column_filters = ('id', 'version', 'enable', 'created')
    column_center_list = ('enable', 'id', 'version', 'modified', 'created')
    column_searchable_list = ('version',)
    form_excluded_columns = ('id',)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class IOSVersionView(ModelView):
    column_default_sort = ('created', True)
    column_formatters = dict(
        log=formatter_len(),
        url=formatter_len(),
    )
    column_searchable_list = ('version',)
    column_filters = ('id', 'version', 'enable', 'created')
    column_center_list = ('enable', 'id', 'version', 'modified', 'created',)
    form_excluded_columns = ('id',)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class APIView(ModelView):
    page_size = 200
    column_default_sort = ('created', True)
    column_searchable_list = ('key', 'name')
    column_filters = ('key', 'url', 'modified', 'created')
    column_center_list = ('modified', 'created', 'expire', 'cache')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class UserImageView(ModelView):

    column_default_sort = ('created', True)
    column_filters = ('source', 'modified', 'created')
    column_center_list = ('modified', 'created')

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


@formatter
def formatter_share(share):
    if share.title and share.url:
        return popover(
            '<img src=%s style="width:100px; height: auto;"></br><a href=%s>%s</a>' % (
                quote(share.image.get_link(), share.url) + escape(share.url)),
            '查看',
            share.title,
        )


@formatter_model
def formatter_A(model):
    icon = '<div class="A"><img src=%s style="height: 40px; width: auto;"></div>' % model.icon.link if model.icon else ''
    active = '<div class="B"><img src=%s style="height: 40px; width: auto;"></div>' % model.active_icon.link if model.active_icon else ''
    html = '<div class="C">%s%s</div>' % (icon, active)
    return html


@formatter_model
def format_android(model):
    if model.android_start and model.android_end:
        return '%s ~ %s' % (model.android_start.version, model.android_end.version)

    if model.android_start:
        return '%s' % model.android_start.version

    if model.android_end:
        return '%s' % model.android_end.version
    return ''


@formatter_model
def format_ios(model):
    if model.ios_start and model.ios_end:
        return '%s ~ %s' % (model.ios_start.version, model.android_end.version)

    if model.ios_start:
        return '%s' % model.ios_start.version

    if model.ios_end:
        return '%s' % model.ios_end.version
    return ''


class ActionView(ModelView):
    page_size = 200
    show_popover = True
    column_default_sort = ('module', 'sort')
    column_labels = dict(modified='修改', created='创建', android='安卓版本', ios='IOS版本')
    column_searchable_list = ('key', 'name')
    column_filters = (
        'id', 'name', 'module', 'login', 'sort', 'enable', 'modified', 'created'
    )
    column_list = (
        'icon', 'key', 'name', 'target', 'share', 'module', 'android', 'ios', 'login',
        'login_show', 'debug', 'sort', 'enable', 'modified', 'created'
    )
    column_center_list = (
        'icon', 'module', 'sort', 'enable', 'login', 'share', 'modified',
        'created', 'login_show', 'debug', 'android', 'ios'
    )
    column_hidden_list = ('debug', 'android', 'ios', 'login_show', 'target')
    column_formatters = dict(
        # icon=formatter_icon(lambda m: (m.icon.get_link(height=40), m.icon.link)),
        name=formatter_text(lambda m: (m.name, m.data, 'text-success' if m.data else ''), max_len=7),
        icon=formatter_A,
        share=formatter_share,
        android=format_android,
        ios=format_ios,
        )
    html = """
   <style type="text/css">
        .col-icon{
            background-color: #B2DFEE;
        }
        .column-header{background-color: #FFFFFF;}
        .C {position: relative; }
        .B {
            display: none;
            position: absolute;
            top: -9px;
            right: -68px;
            padding: 9px;
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
        }
        .A:hover + .B {
            display: block;
        }
    </style>
    """


class SlideView(ModelView):
    page_size = 200
    show_popover = True
    column_labels = dict(modified='修改', created='创建', android='安卓版本', ios='IOS版本')
    column_default_sort = ('module', 'sort')
    column_searchable_list = ('name', 'key')
    column_filters = ('module', 'modified', 'created')
    column_list = (
        'icon', 'key', 'name', 'target', 'share', 'module', 'android', 'ios', 'login',
        'login_show', 'debug', 'sort', 'enable', 'modified', 'created'
    )
    column_center_list = (
        'icon', 'key', 'name', 'module', 'sort', 'share',
        'android', 'ios', 'login', 'login_show', 'debug',
        'enable', 'modified', 'created'
    )
    column_hidden_list = ('debug', 'android', 'ios', 'login_show', 'target')
    column_formatters = dict(
        image=formatter_icon(lambda m: (m.image.get_link(height=40), m.image.link)),
        share=formatter_share,
        android=format_android,
        ios=format_ios,
    )

    def on_model_change(self, form, model, created=False):
        model.modified = datetime.now()


class ImageView(ModelView):
    pass


class TPLView(ModelView):
    page_size = 200
    column_center_list = ('name', 'key', 'enable', 'modified', 'created')
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')


class OptionView(ModelView):
    page_size = 200
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')


def get_link(key):
    url = url_for('page2', key=key)
    if current_app.config.get('WEB_HOST'):
        return 'http://%s%s' % (current_app.config.get('WEB_HOST'), url)
    return url


class PageView(ModelView):
    column_default_sort = ('-created', )
    column_list = ('id', 'key', 'name', 'content', 'modified', 'created')
    column_center_list = ('id', 'modified', 'created')
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')
    column_formatters = dict(
        id=formatter_link(lambda m: (m.id, get_link(str(m.id)))),
        key=formatter_link(lambda m: (m.key, get_link(str(m.key)))),
    )
    form_excluded_columns = ('id', )
    form_overrides = dict(content=WangEditorField)

    def on_model_change(self, form, model, created=False):
        model.create()
        model.modified = datetime.now()


class ChoicesView(ModelView):
    column_searchable_list = ('name', 'key')
    column_filters = ('key', 'name')
    column_center_list = ('modified', 'created', 'enable', 'default')
    column_hidden_list = ('default',)


class MenuView(ModelView):
    pass


class ModelAdminView(ModelView):
    pass


class Form(BaseForm):

    def __init__(self, formdata=None, obj=None, prefix=u'', **kwargs):
        self._obj = obj
        super(BaseForm, self).__init__(formdata=formdata, obj=obj, prefix=prefix, **kwargs)
        if self._obj and self._obj.model:
            choices = []
            model = current_app.cool_manager.models.get(self._obj.model.name)
            if current_app.cool_manager and not current_app.cool_manager.loading:
                for admin in current_app.extensions.get('admin', []):
                    for view in admin._views:
                        if hasattr(view, 'model') and view.model is self._obj.__class__:
                            for x in model._fields:
                                attr = getattr(model, x)
                                choices.append((x, view.column_labels.get(x) or attr.verbose_name))
                            break
            if current_app.cool_manager and not current_app.cool_manager.loading:
                for admin in current_app.extensions.get('admin', []):
                    for view in admin._views:
                        if hasattr(view, 'model') and view.model is model:
                            for x in view.column_formatters.iterkeys():
                                if x not in model._fields:
                                    choices.append((x, view.column_labels.get(x, x)))
                            break
            for field in self:
                if type(field) == DragSelectField:
                    field.choices = choices

            if hasattr(model, '_meta'):
                indexes = model._meta.get('indexes', [])
                attr = getattr(self, 'column_default_sort')
                choices = [(json.dumps(x), json.dumps(x)) for x in indexes]
                if not choices and hasattr(model, 'created'):
                    choices.append(('"-created"', '"-created"'))
                choices.append(('""', '空'))
                attr.choices = choices


MENUS_JSON = """[{"id":"UserView"},{"id":"运营","children":[{"id":"QRCodeView"},{"id":"WeChatUserView"}]},{"id":"日志","children":[{"id":"UserLogView"},{"id":"LogView"},{"id":"TraceLogView"},{"id":"StatLogView"},{"id":"AdminUserLoginLogView"},{"id":"AdminChangeLogView"}]},{"id":"工具","children":[{"id":"WebStaticAdmin"},{"id":"ItemView"},{"id":"ViewView"},{"id":"AdminUserView"},{"id":"GroupView"}]}]"""


class ViewView(ModelView):
    tabs = [
        dict(endpoint='.set_menu', title='菜单', text='菜单'),
    ]
    form_overrides = dict(
        column_default_sort=SelectField,
        column_list=DragSelectField,
        column_center_list=DragSelectField,
        column_hidden_list=DragSelectField,
        column_filters=DragSelectField,
        column_sortable_list=DragSelectField,
        column_searchable_list=DragSelectField,
        form_excluded_columns=DragSelectField,
    )
    form_args = dict(column_default_sort=dict(choices=[]))
    form_base_class = Form

    column_list = ["name", "label", "type", "page_size", "can_create", "can_edit", "can_delete", "icon", "modified", "created", "code"]
    column_center_list = ["type", "page_size", "can_delete", "can_edit", "can_create", "icon", "code", "modified", "created"]
    column_hidden_list = ["modified"]
    column_filters = ["id", "model", "type", "can_create", "can_edit", "can_delete", "modified", "created"]
    column_hidden_list = ["code",  "can_create", "can_edit", "can_delete"]
    column_searchable_list = ["name", "label"]
    form_excluded_columns = ["model"]
    column_formatters = dict(
        icon=formatter_link(lambda m: (
            FA % (m.icon or 'file-o'), '/admin/view/get_icon?id=%s' % m.id),
            html=True,
            id=lambda m: str(m.id) + '-icon',
            class_='btn btn-default btn-sm btn-icon',
            data_id=lambda m: m.id,
            data_key='icon',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
        code=formatter_link(lambda m: (
            FA % 'code',
            '/admin/view/get_code?id=%s' % m.id) if m.code_text else ('', ''),
            html=True,
            id=lambda m: str(m.id) + '-icon',
            class_='btn btn-default btn-sm btn-code',
            data_id=lambda m: m.id,
            data_key='code',
            data_toggle="modal",
            data_target="#simple-modal",
            data_refresh="true",
        ),
    )

    @expose('/get_icon')
    def get_icon(self):
        obj = self.model.objects(id=request.args.get('id')).get_or_404()
        return self.render('common/icon-modal.html', obj=obj)

    @expose('/get_code')
    def get_code(self):
        obj = self.model.objects(id=request.args.get('id')).get_or_404()
        return self.render('common/code-modal.html', obj=obj)

    @expose('/set_menu')
    def set_menu(self):
        menus = json.loads(Item.data('admin_menus', '[]', name='管理菜单'))

        if not menus:
            filename = current_app.get_data_path('admin.menus.json')
            if os.path.isfile(filename):
                try:
                    with open(filename) as fd:
                        menus = json.loads(fd.read())
                except:
                    pass

            if not menus:
                menus = json.loads(MENUS_JSON)

        views = dict()
        cates = dict()
        for view in View.objects.all():
            if view.type == view.TYPE_CATE:
                cates[view.name] = dict(id=view.name, name=view.label, icon=view.icon, children=[])
            else:
                views[view.name] = dict(id=view.name, name=view.label, icon=view.icon)
        if menus:
            right = []
            for menu in menus:
                if menu['id'] in views:
                    item = views[menu['id']]
                    right.append(item)
                    del views[menu['id']]
                elif menu['id'] in cates:
                    item = cates[menu['id']]
                    if 'children' in item and 'children' in menu:
                        for child in menu['children']:
                            if child['id'] in views:
                                item['children'].append(views[child['id']])
                                del views[child['id']]
                    right.append(item)
                    del cates[menu['id']]
        else:
            right = [dict(name='仪表盘', icon='diamond')]
        return self.render('common/menu.html', cates=cates, views=views, right=right)

    @expose('/save_menu', methods=['POST'])
    def save_menu(self):
        menus = request.form.get('menus')
        Item.set_data('admin_menus', menus, name='管理菜单')

        filename = current_app.get_data_path('admin.menus.json')
        with open(filename, 'w+') as fd:
            fd.write(menus)

        for admin in current_app.extensions.get('admin', []):
            admin._refresh()
        return json_success(msg='保存成功')


class LogView(ModelView):

    show_popover = True
    column_list = ['message', 'levelname', 'module', 'funcName', 'lineno', 'url', 'created']
    column_center_list = ['levelname', 'module', 'funcName', 'lineno', 'created']
    column_filters = ['levelname', 'module', 'funcName', 'lineno', 'created']
    column_searchable_list = ['message', 'url', 'user_agent']
    column_formatters = dict(
        message=formatter_popover(lambda m: (
            m.message, '<pre>%s</pre>' % markup(m.exc or ''))),
    )

    html = """<style>.popover {max-width: 800px;}</style>"""


@formatter_model
def get_handle(m):
    html_one = ''
    html_two = ''
    html_three = ''
    if not m.active:
        html_one = """
        <div class="nav-item btn-box" style='display:inline;'>
            <a style="color:#fff" class="btn btn-primary btn-active-true"
            data-id="true_%s" id="%s">封号</a>
        </div>
        """ % (m.user.id, m.user.id)
    if m.active:
        html_two = """
        <div class="nav-item btn-box" style='display:inline;'>
            <a style="color:#fff" class="btn btn-info btn-active-false"
            data-id="false_%s" id="%s">解封</a>
        </div>
        """ % (m.user.id, m.user.id)
    if m.result:
        html_three = """
            <div class="nav-item btn-box">
                <a style="color:#fff" data-refresh="true" data-target="#simple-modal"
                class="btn btn-success btn-sm" data-toggle="modal"
                href="/admin/complaint/result?id=%s" target="_blank"
                id="%s">结果</a>
            </div>
            """ % (m.id, m.id)
    return html_one + html_two + html_three


class ComplaintView(ModelView):

    show_popover = True
    column_labels = dict(handled='操作')
    column_list = (
        'user', 'id', 'type', 'content', 'active', 'handle',
        'modified', 'created', 'handled')
    column_center_list = column_list
    column_filters = (
        'user', 'id', 'type', 'content', 'active', 'result', 'handle',
        'modified', 'created')
    column_searchable_list = ('id', 'type', 'content', 'result')
    column_formatters = dict(
        content=formatter_popover(lambda m: m.content, max_len=10),
        handled=get_handle,
    )

    script = """
        $(function(){
        var successAlert = '<div class="alert alert-success alert-dismissible fade in"　role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">×</span></button>'
        var errorAlert = '<div class="alert alert-danger alert-dismissible fade in" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">×</span></button>'

            $('.btn-active-true').click(function() {
                var id = $(this).data('id')
                console.log(id)
                $.post('/admin/complaint/handled', {id: id}, function(data){
                    if(data.code==0) {
                        $('#filter_form').before(successAlert + data.msg + '</div>')
                        if(!!!data.hidden){
                            $(data.id).hide()
                        }
                    }else {
                        $('#filter_form').before(errorAlert + data.msg + '</div>')
                        }
                })
            })
            $('.btn-active-false').click(function() {
                var id = $(this).data('id')
                console.log(id)
                $.post('/admin/complaint/handled', {id: id}, function(data){
                    if(data.code==0) {
                        $('#filter_form').before(successAlert + data.msg + '</div>')
                        if(!!!data.hidden){
                            $(data.id).hide()
                        }
                    }else {
                        $('#filter_form').before(errorAlert + data.msg + '</div>')
                        }
                })
            })

        })
        """

    @expose('/handled', methods=['POST'])
    def handled(self):
        id = request.form.get('id')
        if id.split('_')[0] == 'true':
            complaints = self.model.objects(
                user=id.split('_')[1], active=False).first()
            if complaints and complaints.user.complaint:
                complaints.active = True
                complaints.save()
                return json_error(msg='该用户之前已被封')

            if complaints and not complaints.user.complaint:
                complaints.user.complaint = True
                complaints.active = True
                complaints.result = '%s\n%s' % (
                    dict(
                        result='complaint success',
                        num='%d' % len(complaints.result.split(
                            '\n')) if complaints.result else '1'),
                    complaints.result if complaints.result else '')
                complaints.save()
                complaints.user.save()
            return json_success(msg='封号成功', id='#%s' % id.split('_')[1])

        if id.split('_')[0] == 'false':
            complaints = self.model.objects(
                user=id.split('_')[1], active=True).first()
            if complaints and not complaints.user.complaint:
                complaints.active = False
                complaints.save()
                return json_error(msg='该用户未被封')

            if complaints and complaints.user.complaint:
                complaints.user.complaint = False
                complaints.active = False
                complaints.result = '%s\n%s' % (
                    dict(
                        result='complaint release',
                        num='%d' % len(complaints.result.split(
                            '\n')) if complaints.result else '1'),
                    complaints.result if complaints.result else '')
                complaints.save()
                complaints.user.save()
            return json_success(msg='解封成功', id='#%s' % id.split('_')[1])
        return ''

    @expose('/result')
    def btnremark(self):
        _id = request.args.get('id', None)
        model = self.model.objects(id=_id).first()
        result = model.result if model else ''
        remark = model.remark if model else ''
        return self.render(
            'admin/result.html', result=result or '', id=_id,
            remark=remark or '')

    @expose('/saveresult', methods=['POST'])
    def saveresult(self):
        _id = request.form.get('id', None)
        model = self.model.objects(id=_id).first()
        if not model:
            json_error(msg='无该记录')

        result = request.form.get('result')
        remark = request.form.get('remark')
        model.result = result
        model.remark = remark
        model.save()
        return json_success(msg='保存成功')
