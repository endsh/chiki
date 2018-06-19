# coding: utf-8
from flask import Blueprint, current_app
from flask.ext.login import LoginManager
from ..mongoengine import MongoEngine
from flask.ext.cache import Cache

db = MongoEngine()
login = LoginManager()
cache = Cache()
page = Blueprint('page', __name__)


class Base(object):

    @classmethod
    def init(cls, app, key=None):
        key = key or cls.__name__.upper()
        if key in app.config:
            return cls(app, key)

    def __init__(self, app=None, key=None, config=None, holder=None,
                 name=None):
        self.name = name or self.__class__.__name__.lower()
        self.key = key
        self.config = config
        self.holder = holder
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        name = self.__class__.__name__
        if self.config is None:
            self.config = app.config.get(self.key or name.upper())

        self.puppets = dict()
        for key, config in self.config.get('puppets', dict()).iteritems():
            self.puppets[key] = self.__class__(
                app=app, key=key, config=config, holder=self)

        if not hasattr(app, name.lower()) and not self.holder:
            setattr(app, name.lower(), self)

    def get_key(self):
        return self.key if self.holder else 'default'

    def get_config(self, key, default=None, repalce=True, config=None):
        if config and key in config:
            return config.get(key)

        if self.holder:
            value = self.config.get(
                key, self.holder.get_config(key, default, False))
        else:
            value = self.config.get(key, default)

        if repalce and isinstance(value, (str, unicode)):
            return value.replace('[key]', self.get_key())
        return value

    def get_puppet(self, key):
        if self.holder:
            return self.holder.get_puppet(key)
        return self if key in ['default', ''] else self.puppets.get(key)

    @property
    def item(self):
        item = self.get_config('item', dict())
        Item = current_app.cool_manager.models.get('Item')
        return Item.choice(item.get('key'), item.get('value', 'default'),
                           item.get('name', ''))
    @property
    def puppet(self):
        return self.get_puppet(self.item)
