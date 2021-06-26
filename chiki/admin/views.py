# coding: utf-8
import os
import gc
import traceback
from datetime import datetime
from flask import current_app, redirect, flash, request
from flask_login import current_user
from flask_admin import AdminIndexView as _AdminIndexView, expose
from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.base import BaseView as _BaseView
from flask_admin.contrib.mongoengine import ModelView as _ModelView
from flask_admin.contrib.mongoengine.helpers import format_error
from flask_admin.contrib.sqla import ModelView as _SModelView
from flask_admin.model.base import BaseModelView
from flask_admin._compat import string_types, with_metaclass
from mongoengine.fields import IntField, LongField, DecimalField, FloatField
from mongoengine.fields import StringField, ReferenceField, ObjectIdField, ListField
from mongoengine.fields import BooleanField, DateTimeField
from bson.objectid import ObjectId
from jinja2 import contextfunction
from .convert import KModelConverter
from .filters import KFilterConverter, ObjectIdEqualFilter
from .formatters import type_best, type_image, type_file, type_select
from .formatters import type_bool, type_images
from .formatters import formatter_len, formatter_link, filter_sort
from .metaclass import CoolAdminMeta
from .ajax import create_ajax_loader, process_ajax_references
from ..mongoengine.fields import FileProxy, ImageProxy, Base64ImageProxy
from ..utils import json_success, json_error
from blinker import signal
from chiki.contrib.admin.models import AdminChangeLog


__all__ = [
    "ModelView", "SModelView", "IndexView", "AdminIndexView", "BaseView",
]

old_create_blueprint = _BaseView.create_blueprint
model_signals = signal('change')


# def model_operating(model, type, **kwargs):
#     before = after = dict(id=model.id)
#     if kwargs.get('form'):
#         for k, v in kwargs.get('form').data.items():
#             if v != model[k]:
#                 before[k] = model[k]
#                 after[k] = v
#     else:
#         before = model.to_mongo()
#     AdminChangeLog.log(
#         user=current_user.id,
#         model=model.__class__.__name__,
#         before_data=str(before),
#         after_data=str(after),
#         type=type,
#     )

def model_operating(lable, model, **kwargs):
    user = current_user.id
    if lable == 'update':
        AdminChangeLog.modify_data(user, model=model, **kwargs)
    elif lable == 'dropdown':
        AdminChangeLog.dropdown_modify(user, model=model, **kwargs)

model_signals.connect(model_operating)


def create_blueprint(self, admin):
    if self.static_folder == 'static':
        root = os.path.dirname(os.path.dirname(__file__))
        self.static_folder = os.path.abspath(os.path.join(root, 'static'))
        self.static_url_path = '/static/admin'
    return old_create_blueprint(self, admin)


_BaseView.create_blueprint = create_blueprint


class ModelView(with_metaclass(CoolAdminMeta, _ModelView)):

    page_size = 50
    can_view_details = True
    details_modal = True
    edit_modal = True
    model_form_converter = KModelConverter
    filter_converter = KFilterConverter()

    column_type_formatters = _ModelView.column_type_formatters or dict()
    column_type_formatters[datetime] = type_best
    column_type_formatters[FileProxy] = type_file

    show_popover = False
    robot_filters = False

    def __init__(
            self, model, name=None,
            category=None, endpoint=None, url=None, static_folder=None,
            menu_class_name=None, menu_icon_type=None, menu_icon_value=None):

        self.column_formatters = dict(self.column_formatters or dict())

        # 初始化标识
        self.column_labels = self.column_labels or dict()
        self.column_labels.setdefault('id', 'ID')
        for field in model._fields:
            if field not in self.column_labels:
                attr = getattr(model, field)
                if hasattr(attr, 'verbose_name'):
                    verbose_name = attr.verbose_name
                    if verbose_name:
                        self.column_labels[field] = verbose_name

        #初始化筛选器
        types = (IntField, ReferenceField, StringField, BooleanField, DateTimeField) if self.robot_filters else (ReferenceField,)
        self.column_filters = list(self.column_filters or [])

        primary = False
        for field in model._fields:
            attr = getattr(model, field)
            if hasattr(attr, 'primary_key') and attr.primary_key is True:
                self.column_filters = [field] + self.column_filters
                primary = True
            elif type(attr) in types and attr.name not in self.column_filters:
                self.column_filters.append(attr.name)
        if not primary:
            self.column_filters = ['id'] + self.column_filters

        if self.robot_filters:
            columns = self.column_list or [x[0] for x in self._get_model_fields(model)]
            self.column_filters = filter_sort(self.column_filters, columns)

        #初始化类型格式化
        for field in model._fields:
            attr = getattr(model, field)
            if type(attr) == StringField:
                self.column_formatters.setdefault(attr.name, formatter_len(40))

        self.form_ajax_refs = self.form_ajax_refs or dict()
        for field in model._fields:
            attr = getattr(model, field)
            if type(attr) == ReferenceField:
                if field not in self.form_ajax_refs and hasattr(attr.document_type, 'ajax_ref'):
                    self.form_ajax_refs[field] = dict(fields=attr.document_type.ajax_ref, page_size=20)

        if not self.column_default_sort and 'created' in model._fields:
            self.column_default_sort = ('-created', )

        self._init_referenced = False

        super(ModelView, self).__init__(model, name, category, endpoint, url, static_folder,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)

    def _refresh_cache(self):
        self.column_choices = self.column_choices or dict()
        for field in self.model._fields:
            choices = getattr(self.model, field).choices
            if choices:
                self.column_choices[field] = choices
        super(ModelView, self)._refresh_cache()

    def _process_ajax_references(self):
        references = BaseModelView._process_ajax_references(self)
        return process_ajax_references(references, self)

    def create_model(self, form):
        try:
            model = self.model()
            self.pre_model_change(form, model, True)
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save()
        except Exception as ex:
            current_app.logger.error(traceback.format_exc())
            if not self.handle_view_exception(ex):
                flash('Failed to create record. %(error)s' % dict(error=format_error(ex)), 'error')
            return False
        else:
            self.after_model_change(form, model, True)

        return True

    def update_model(self, form, model):
        try:
            self.pre_model_change(form, model, False)
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            model.save()
        except Exception as ex:
            current_app.logger.error(traceback.format_exc())
            if not self.handle_view_exception(ex):
                flash('Failed to update record. %(error)s' % dict(error=format_error(ex)), 'error')
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def pre_model_change(self, form, model, created=False):
        model_signals.send(
            'update', model=model, type='created' if created else 'edit',
            form=form)

    def on_model_change(self, form, model, created=False):
        if created is True and hasattr(model, 'create'):
            if callable(model.create):
                model.create()
        elif hasattr(model, 'modified'):
            model.modified = datetime.now()

    def on_model_delete(self, model):
        model_signals.send('update', model=model, type='delete')

    # @expose('/')
    # def index_view(self):
    #     res = super(ModelView, self).index_view()
    #     gc.collect()
    #     return res

    def get_ref_type(self, attr):
        document, ref_type = attr.document_type, None
        if hasattr(document, 'id'):
            xattr = document._fields.get('id')
            if isinstance(xattr, IntField) or isinstance(xattr, LongField):
                ref_type = int
            elif isinstance(xattr, DecimalField) or isinstance(xattr, FloatField):
                ref_type = float
            elif isinstance(xattr, ObjectIdField):
                ref_type = ObjectId
        return ref_type

    def scaffold_filters(self, name):
        if isinstance(name, string_types):
            attr = self.model._fields.get(name)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Find name
        visible_name = None

        if not isinstance(name, string_types):
            visible_name = self.get_column_name(attr.name)

        if not visible_name:
            visible_name = self.get_column_name(name)

        # Convert filter
        type_name = type(attr).__name__
        if isinstance(attr, ReferenceField):
            ref_type = self.get_ref_type(attr)
            flt = self.filter_converter.convert(type_name, attr, visible_name, ref_type)
        elif isinstance(attr, ListField) and isinstance(attr.field, ReferenceField):
            ref_type = self.get_ref_type(attr.field)
            flt = self.filter_converter.convert(type_name, attr, visible_name, ref_type)
        elif isinstance(attr, ObjectIdField):
            flt = self.filter_converter.convert(type_name, attr, visible_name, ObjectId)
        else:
            flt = self.filter_converter.convert(type_name, attr, visible_name)

        return flt

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):
        query = self.get_query()
        if self._filters:
            for flt, flt_name, value in filters:
                f = self._filters[flt]
                query = f.apply(query, f.clean(value))

        if self._search_supported and search:
            query = self._search(query, search)

        count = query.count() if not self.simple_list_pager else None

        if sort_column:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort_column))
        else:
            order = self._get_default_order()
            if order:
                if type(order) == list and len(order) == 1:
                    order = order[0]

                if len(order) <= 1 or order[1] not in [True, False]:
                    query = query.order_by(*order)
                else:
                    query = query.order_by('%s%s' % ('-' if order[1] else '', order[0]))

        if page_size is None:
            page_size = self.page_size

        if page_size:
            query = query.limit(page_size)

        if page and page_size:
            query = query.skip(page * page_size)

        if execute:
            query = query.all()

        return count, query

    def get_filter_tpl(self, attr):
        for view in self.admin._views:
            if hasattr(view, 'model') and attr.document_type == view.model and view._filter_args:
                for idx, flt in view._filter_args.itervalues():
                    if type(flt) == ObjectIdEqualFilter:
                        return ('/admin/%s/?flt0_' % view.model.__name__.lower()) + str(idx) + '=%s'
                    if flt.column.primary_key:
                        cls = type(flt).__name__
                        if 'EqualFilter' in cls and 'Not' not in cls:
                            return ('/admin/%s/?flt0_' % view.model.__name__.lower()) + str(idx) + '=%s'

    def set_filter_formatter(self, attr):

        def formatter(tpl, name):
            return lambda m: (getattr(m, name), tpl % str(getattr(m, name).id if getattr(m, name) else ''))

        tpl = self.get_filter_tpl(attr)
        if tpl:
            f = formatter_link(formatter(tpl, attr.name))
            self.column_formatters.setdefault(attr.name, f)

    def init_referenced(self):
        #初始化类型格式化
        for field in self.model._fields:
            attr = getattr(self.model, field)
            if type(attr) == ReferenceField:
                self.set_filter_formatter(attr)

    @contextfunction
    def get_list_value(self, context, model, name):
        if not self._init_referenced:
            self._init_referenced = True
            self.init_referenced()

        column_fmt = self.column_formatters.get(name)
        if column_fmt is not None:
            try:
                value = column_fmt(self, context, model, name)
            except:
                current_app.logger.error(traceback.format_exc())
                value = '该对象被删了'
        else:
            value = self._get_field_value(model, name)

        #获取choice
        choices_map = self._column_choices_map.get(name, {})
        if choices_map:
            return type_select(self, value, model, name, choices_map) or value

        if isinstance(value, bool):
            return type_bool(self, value, model, name)

        if value and isinstance(value, list) and isinstance(value[0], ImageProxy):
            self.show_popover = True
            return type_images(self, value)

        type_fmt = None
        for typeobj, formatter in self.column_type_formatters.items():
            if isinstance(value, typeobj):
                type_fmt = formatter
                break
        if type_fmt is not None:
            try:
                value = type_fmt(self, value)
            except:
                current_app.logger.error(traceback.format_exc())
                value = '该对象被删了'

        return value

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_delete(self, ids):
        try:
            count = 0

            id = self.model._meta['id_field']
            if id in self.model._fields:
                if isinstance(self.model._fields[id], IntField):
                    all_ids = [int(pk) for pk in ids]
                elif isinstance(self.model._fields[id], StringField):
                    all_ids = ids
                else:
                    all_ids = [self.object_id_converter(pk) for pk in ids]
            else:
                all_ids = [self.object_id_converter(pk) for pk in ids]

            for obj in self.get_query().in_bulk(all_ids).values():
                count += self.delete_model(obj)

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete records. %(error)s', error=str(ex)),
                      'error')

    def on_field_change(self, model, name, value):
        if self.get_field_type(name) == 'IntField':
            value = int(value)

        model[name] = value
        if hasattr(model, 'modified'):
            model['modified'] = datetime.now()

    @expose('/dropdown')
    def dropdown(self):
        id = request.args.get('id', 0, str)
        val = request.args.get('key', '')
        name = request.args.get('name', '', str)
        value = request.args.get('value', '', str)
        model = self.model

        group = current_user.group
        m_name = self.__class__.__name__
        if not current_user.is_authenticated() \
                or not (current_user.root is True
                        or getattr(self, 'can_use', False) is True
                        or group and m_name in group.power_list
                        and m_name in group.can_edit_list):
            return json_error()

        if not val:
            val = False if value == 'False' else True
        if type(val) == int:
            val = int(val)

        obj = model.objects(id=id).first()
        if obj:
            before_data = obj[name]
            self.on_field_change(obj, name, val)
            obj.save()
            model_signals.send(
                'dropdown', model=model, key=name,
                before_data=before_data, after_data=val, id=id)
            return json_success()

        return json_error(msg='该记录不存在')

    def get_field_type(self, field):
        if hasattr(self.model, field):
            return type(getattr(self.model, field)).__name__
        return 'LabelField'

    def _create_ajax_loader(self, name, opts):
        return create_ajax_loader(self.model, name, name, opts)

    def is_accessible(self):
        if current_app.is_admin:
            if current_user.root is True:
                return current_user.root
            if current_user.group:
                return self.__class__.__name__ in current_user.group.power_list
            return False
        return True

    def inaccessible_callback(self, name, **kwargs):
        flash('暂无操作权限！')
        return self.render('admin/power.html')


class SModelView(_SModelView):

    def __init__(
            self, model, session,
            name=None, category=None, endpoint=None, url=None, static_folder=None,
            menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        if hasattr(model, 'LABELS'):
            self.column_labels = model.LABELS
        super(SModelView, self).__init__(
            model, session, name=name, category=category,
            endpoint=endpoint, url=url, static_folder=static_folder, menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type, menu_icon_value=menu_icon_value)


class AdminIndexView(with_metaclass(CoolAdminMeta, _AdminIndexView)):
    """ 仪表盘 """

    MENU_ICON = 'diamond'

    def is_accessible(self):
        if current_user.root is True:
            return current_user.root
        if current_user.group:
            return self.__class__.__name__ in current_user.group.power_list
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/admin/user')


class BaseView(with_metaclass(CoolAdminMeta, _BaseView)):
    """ 基础视图 """

    def is_accessible(self):
        if current_user.root is True:
            return current_user.root
        if current_user.group:
            return self.__class__.__name__ in current_user.group.power_list
        return False

    def inaccessible_callback(self, name, **kwargs):
        flash('暂无操作权限！')
        return self.render('admin/power.html')


class IndexView(AdminIndexView):
    """ 仪表盘 """

    @expose('/')
    def index(self):
        if current_app.config.get('INDEX_REDIRECT') != '/admin/':
            return redirect(current_app.config.get('INDEX_REDIRECT'))
        return self.render('base.html')
