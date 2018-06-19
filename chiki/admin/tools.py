# coding: utf-8
import os
import shutil
import zipfile
from chiki.contrib.common import Channel, AndroidVersion
from flask import flash, redirect, current_app
from flask.ext.admin import expose
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField
from wtforms import SelectField
from wtforms.validators import DataRequired
from .views import BaseView


class PkgForm(Form):
    version = SelectField('版本', validators=[DataRequired()])
    apk = FileField('应用包')

    def validate_apk(form, field):
        if not field.data:
            raise ValueError('请上传应用文件')
        if not field.data.filename.endswith('.apk'):
            raise ValueError('请上传APK文件')


def pack(src, path, channel):
    name = '.'.join(os.path.basename(src).split('.')[:-1])
    out = os.path.join(path, '{name}_{channel}.apk'.format(name=name, channel=channel))
    shutil.copy(src, out)
    zipped = zipfile.ZipFile(out, 'a', zipfile.ZIP_DEFLATED)
    empty_file = 'META-INF/CHANNEL_{channel}'.format(channel=channel)
    zipped.writestr(empty_file, "")
    zipped.close()
    return out


def packs(src, path):
    channels = [x.id for x in Channel.objects.all()] or [1001]
    for channel in channels:
        pack(src, path, channel)


class ToolsView(BaseView):
    """ 工具 """

    MENU_ICON = 'cogs'

    tabs = [
        dict(endpoint='.index_view', title='安卓打包', text='打包'),
    ]

    @expose('/', methods=['GET', 'POST'])
    def index_view(self):
        form = PkgForm()
        versions = list(AndroidVersion.objects.all())
        form.version.choices = reversed([(x.version, x.version) for x in versions])
        if form.validate_on_submit():
            version = form.version.data
            static_folder = current_app.config.get('WEB_STATIC_FOLDER')
            name = current_app.config.get('NAME')
            path = os.path.join(static_folder, 'android', version)
            src = os.path.join(path, '%s_%s.apk' % (name, version))
            if not os.path.exists(path):
                os.makedirs(path)
            form.apk.data.save(src)
            packs(src, path)
            flash("打包成功！", 'success')
            return redirect('/admin/webstaticadmin/b/android/%s' % version)
        return self.render('tools/pkg.html', form=form)
