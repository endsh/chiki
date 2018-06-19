# coding: utf-8
import os
import json
from flask import current_app
from flask.ext.admin import Admin as _Admin, AdminIndexView
from flask.ext.admin.menu import MenuView, MenuCategory, MenuLink
from .formatters import *
from .static import *
from .views import *
from .tools import *

MENUS_JSON = """[{"id":"UserView"},{"id":"运营","children":[{"id":"QRCodeView"},{"id":"WeChatUserView"}]},{"id":"日志","children":[{"id":"UserLogView"},{"id":"LogView"},{"id":"TraceLogView"},{"id":"StatLogView"},{"id":"AdminUserLoginLogView"},{"id":"AdminChangeLogView"}]},{"id":"工具","children":[{"id":"WebStaticAdmin"},{"id":"ItemView"},{"id":"ViewView"},{"id":"AdminUserView"},{"id":"GroupView"}]}]"""


class Admin(_Admin):

    def __init__(self, app=None, name=None,
                 url=None, subdomain=None,
                 index_view=None,
                 translations_path=None,
                 endpoint=None,
                 static_url_path=None,
                 base_template=None,
                 template_mode='chiki',
                 category_icon_classes=None):
        super(Admin, self).__init__(
            app=app, name=name,
            url=url, subdomain=subdomain,
            index_view=index_view,
            translations_path=translations_path,
            endpoint=endpoint,
            static_url_path=static_url_path,
            base_template=base_template,
            template_mode=template_mode,
            category_icon_classes=category_icon_classes,
        )

    def _set_admin_index_view(self, index_view=None,
                              endpoint=None, url=None):
        self.index_view = (index_view or self.index_view or 
                           AdminIndexView(endpoint=endpoint, url=url))
        self.endpoint = endpoint or self.index_view.endpoint
        self.url = url or self.index_view.url

        # Add predefined index view
        # assume index view is always the first element of views.
        if len(self._views) > 0:
            self._views[0] = self.index_view
        else:
            self.add_view(self.index_view)

    def _refresh(self):
        from chiki.contrib.common import Item, View
        menus = json.loads(Item.data('admin_menus', '[]', name='管理菜单'))

        if not menus:
            filename = self.app.get_data_path('admin.menus.json')
            if os.path.isfile(filename):
                try:
                    with open(filename) as fd:
                        menus = json.loads(fd.read())
                except:
                    pass

            if not menus:
                menus = json.loads(MENUS_JSON)

        if menus:
            views = dict()
            for view in View.objects.all():
                if view.type == view.TYPE_CATE:
                    views[view.name] = dict(id=view.name, name=view.label, icon=view.icon, children=[])
                else:
                    views[view.name] = dict(id=view.name, name=view.label, icon=view.icon)
            right = []
            for menu in menus:
                if menu['id'] in views:
                    item = views[menu['id']]
                    if 'children' in item and 'children' in menu:
                        for child in menu['children']:
                            if child['id'] in views:
                                item['children'].append(views[child['id']])
                    right.append(item)

            subs = dict()
            for menu in self._menu:
                if isinstance(item, MenuView):
                    subs[item._view.__class__.__name__] = menu
                elif isinstance(item, MenuCategory):
                    for child in menu._children:
                        subs[child._view.__class__.__name__] = child

            views = dict((x.__class__.__name__, x) for x in self._views)
            menus = []
            for menu in right:
                if 'children' not in menu:
                    if menu['id'] in subs:
                        item = subs[menu['id']]
                        item.name = menu['name']
                        item.menu_icon_value = menu['icon']
                        menus.append(item)
                    elif menu['id'] in views:
                        view = views[menu['id']]
                        item = MenuView(menu['name'], view)
                        item.menu_icon_value = menu['icon']
                        menus.append(item)
                else:
                    cate = MenuCategory(menu['name'], icon_value=menu['icon'])
                    for child in menu['children']:
                        if child['id'] in subs:
                            item = subs[child['id']]
                            item.name = child['name']
                            item.menu_icon_value = child['icon']
                            cate._children.append(item)
                        elif child['id'] in views:
                            view = views[child['id']]
                            item = MenuView(child['name'], view)
                            item.menu_icon_value = child['icon']
                            cate._children.append(item)
                    menus.append(cate)
            self._menu = menus
