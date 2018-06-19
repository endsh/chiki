# coding: utf-8
from .admin import ModelView
from .admin.common import _admin_registry, _document_registry
from .contrib.common import Model, View


class CoolManager(object):

    def __init__(self):
        self.admin = dict()
        self.models = dict()
        self.cates = {
            '运营': 'hdd-o',
            '数据': 'gift',
            '日志': 'database',
            '工具': 'gears',
        }

    def init_app(self, app):
        self.app = app
        app.cool_manager = self
        self.load()

    def load(self):
        self.loading = True
        for name, view in _admin_registry.iteritems():
            self.admin[name] = view
        for name, doc in _document_registry.iteritems():
            if not doc._meta['abstract'] and doc._is_document:
                self.models[name] = doc

        for name, model in self.models.iteritems():
            self.init_model(name, model)

        for name, icon in self.cates.iteritems():
            data_view = View.objects(name=name, type=View.TYPE_CATE).first()
            if not data_view:
                data_view = View(name=name, type=View.TYPE_CATE, label=name, icon=icon)
                data_view.save()

        self.loading = False

    def add_model(self, model, name=None):
        self.models[name or model.__name__] = model
        self.init_model(name or model.__name__, model)
        return model

    def init_model(self, name, model):
        data_model = Model.objects(name=name).first()
        if not data_model:
            data_model = Model(name=name, desc=(model.__doc__ or name).replace('模型', ''))
            data_model.save()
        view = self.get_view(name, model)
        data_view = View.objects(name=view.__name__).first()
        if not data_view:
            data_view = View(name=view.__name__, type=View.TYPE_MODEL,
                model=data_model, label=data_model.desc)
            data_view.save()
        if not data_view.icon and hasattr(model, 'MENU_ICON'):
            data_view.icon = model.MENU_ICON
            data_view.save()
        model._admin_view_cls = view
        model._admin_view_data = data_view

    def init_admin(self, admin):
        uses = []
        for name, model in self.models.iteritems():
            view = model._admin_view_cls(model)
            model._admin_view_data.setup(admin, view)
            admin.add_view(view)
            uses.append(model._admin_view_cls)

        for name, view in self.admin.iteritems():
            if view not in uses:
                for xview in admin._views:
                    if type(xview) == view:
                        data_view = View.objects(name=view.__name__).first()
                        if not data_view:
                            data_view = View(name=view.__name__, type=View.TYPE_VIEW,
                                label=view.__doc__ or view.__name__)
                            data_view.save()
                        if not data_view.icon and hasattr(xview, 'MENU_ICON'):
                            data_view.icon = xview.MENU_ICON
                            data_view.save()
                        data_view.setup(admin, xview)

    def get_view(self, name, model):
        view = self.admin.get('%sView' % name)
        if name == 'Model':
            view = self.admin.get('ModelAdminView')
        if not view:
            view = type('%sView' % name, (ModelView,), {})
        return view


cm = CoolManager()
