# coding: utf-8
import os
from chiki import init_admin, init_uploads
from chiki.admin import IndexView, ModelView
from chiki.mongoengine import MongoEngine
from flask.ext.admin import Admin

admin = Admin(
    name='Chiki', 
    index_view=IndexView(),
    template_mode='bootstrap3',
)
db = MongoEngine()


class Config(object):
    DEBUG = True
    ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    MONGODB_SETTINGS = dict(host='127.0.0.1', port=27017, db='chiki')
    UPLOADS = dict(type='local', link='/uploads/%s', path=os.path.join(ROOT_FOLDER, 'uploads'))
    INDEX_REDIRECT = '/admin/entry'


class Entry(db.Document):
    fileobj = db.XFileField(verbose_name='文件', rename=False)
    image = db.XImageField(verbose_name='图标', rename=False)


admin.add_view(ModelView(Entry, name='Entry'))


def init(app):
    db.init_app(app)
    admin.init_app(app)
    init_uploads(app)


app = init_admin(init, Config)

if __name__ == '__main__':
    app.run()