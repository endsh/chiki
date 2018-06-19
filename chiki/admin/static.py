# coding: utf-8# coding: utf-8
import os
import os.path as op
from datetime import datetime
from operator import itemgetter
from flask import redirect
from flask.ext.admin import expose
from flask.ext.admin.contrib.fileadmin import FileAdmin
from flask.ext.admin._compat import with_metaclass
from .metaclass import CoolAdminMeta

__all__ = [
    'get_static_admin',
]


def get_static_admin(name):
    class StaticFileAdmin(with_metaclass(CoolAdminMeta, FileAdmin)):
        MENU_ICON = 'folder-o'
        list_template = 'admin/file/list2.html'

        def fileType(self, file_name):
            l = file_name.lower().split('.')
            if len(l) < 2:
                return None
            else:
                return l[-1]

        @expose('/unzip')
        def unzip(self):
            pass

        @expose('/')
        @expose('/b/<path:path>')
        def index(self, path=None):
            if self.can_delete:
                delete_form = self.delete_form()
            else:
                delete_form = None

            base_path, directory, path = self._normalize_path(path)

            if not self.is_accessible_path(path):
                flash(gettext('Permission denied.'), 'error')
                return redirect(self._get_dir_url('.index'))

            items = []
            if directory != base_path:
                parent_path = op.normpath(op.join(path, '..'))
                if parent_path == '.':
                    parent_path = None

                items.append(('..', parent_path, True, 0, 0))

            for f in os.listdir(directory):
                fp = op.join(directory, f)
                rel_path = op.join(path, f)

                if self.is_accessible_path(rel_path):
                    items.append((f, rel_path, op.isdir(fp), op.getsize(fp), op.getmtime(fp)))

            items.sort(key=itemgetter(0))
            items.sort(key=itemgetter(2), reverse=True)
            items.sort(key=lambda values: (values[0], values[1], values[2], values[3], datetime.fromtimestamp(values[4])), reverse=True)

            accumulator = []
            breadcrumbs = []
            for n in path.split(os.sep):
                accumulator.append(n)
                breadcrumbs.append((n, op.join(*accumulator)))

            actions, actions_confirmation = self.get_actions_list()

            base_static_url = self.base_url
            return self.render(self.list_template,
                               dir_path=path,
                               breadcrumbs=breadcrumbs,
                               get_dir_url=self._get_dir_url,
                               get_file_url=self._get_file_url,
                               items=items,
                               actions=actions,
                               actions_confirmation=actions_confirmation,
                               delete_form=delete_form,
                               base_static_url=base_static_url,
                               fileType=self.fileType)
    return type(name, (StaticFileAdmin,), {"__doc__":"文件"})
