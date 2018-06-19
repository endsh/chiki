# coding: utf-8
import base64
import hashlib
from flask import current_app
from mongoengine import signals
from mongoengine.fields import ListField, EmbeddedDocument, StringField
from mongoengine.base.fields import BaseField
from werkzeug.datastructures import FileStorage
from .generators import BaseGenerator, RandomGenerator
from .storages import get_storage

__all__ = [
    'XFileField', 'XImageField', 'Base64ImageField', 'XListField',
    'AreaField', 'set_filename_generator', 'FileProxy', 'ImageProxy', 'Base64ImageProxy',
]
DEFAULT_ALLOWS = ['txt', 'bz2', 'gz', 'tar', 'zip', 'rar', 'apk',
                  'jpg', 'jpeg', 'png', 'gif', 'bmp']
DEFAULT_IMAGE_ALLOWS = ['jpg', 'jpeg', 'png', 'gif', 'bmp']


def is_empty(fd):
    fd.seek(0)
    first_char = fd.read(1)
    fd.seek(0)
    return not bool(first_char)


_filename_generators = {}


def set_filename_generator(key, generator):
    global _filename_generators
    _filename_generators[key] = generator


def get_filename_generator(key, local, generator=None):
    global _filename_generators
    if not generator:
        generator = RandomGenerator
    if key not in _filename_generators:
        _filename_generators[key] = generator(local)
    return _filename_generators[key]


class FileProxy(object):

    def __init__(self, instance, value=None):
        self.instance = instance
        self.filename = ''
        self.process(value)

    def __nonzero__(self):
        return True if self.filename else False

    @property
    def path(self):
        return self.instance.get_path(self.filename)

    @property
    def src(self):
        return self.instance.get_link(self.filename, source=True)

    @property
    def link(self):
        return self.instance.get_link(self.filename, source=True)

    def get_link(self, width=0, height=0, ystart=0, yend=0):
        return self.instance.get_link(self.filename, source=True)

    @property
    def content(self):
        return self.instance.get_content(self.filename)

    @property
    def md5(self):
        content = self.content
        if content:
            return hashlib.md5(content).hexdigest()
        return ''

    def process(self, value=None):
        if isinstance(value, FileStorage):
            self._process(stream=value.stream, format=value.filename.split('.')[-1])
        elif isinstance(value, dict):
            self._process(stream=value.get('stream'), format=value.get('format'))
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            self._process(stream=value[0], format=value[1])
        elif isinstance(value, (str, unicode)):
            self._process(filename=value)
        elif hasattr(value, 'read'):
            self._process(stream=value)
        elif not value:
            self._process()
        elif isinstance(value, FileProxy):
            self._process(filename=value.filename)
        else:
            raise ValueError('Can not support type(%s)' % str(value))

    def _process(self, stream=None, format=None, filename=None):
        if stream is not None:
            if not is_empty(stream):
                self.remove()
                if self.instance.rename or not self.filename:
                    self.filename = self.instance.put(stream, format=format)
                else:
                    self.instance.put(stream, filename=self.filename)
        elif filename is not None:
            self.remove()
            self.filename = filename
        else:
            self.remove()
            self.filename = ''

    def remove(self):
        self.instance.remove(self.filename)

    def __unicode__(self):
        return self.filename


class XFileField(BaseField):

    proxy_class = FileProxy
    default_allows = DEFAULT_ALLOWS

    def __init__(self, max_size=2*1024*1024, auto_remove=None,
            rename=True, allows=None, config='UPLOADS',
            filename_generator=None, place='', **kwargs):
        self.max_size = max_size
        self.auto_remove = auto_remove
        self.rename = rename
        self.allows = allows or self.default_allows
        self.config = config
        self._filename_generator = filename_generator
        self.place = place
        super(XFileField, self).__init__(**kwargs)

    @property
    def storage(self):
        if not hasattr(self, '_storage'):
            config = current_app.config.get(self.config)
            if not config:
                raise ValueError('Please set %s in config.' % self.config)
            self._storage = get_storage(self.config, config)
        return self._storage

    @property
    def filename_generator(self):
        if not self._filename_generator or isinstance(self._filename_generator, type):
            config = current_app.config.get(self.config)
            if not config:
                raise ValueError('Please set %s in config.' % self.config)
            self._filename_generator = get_filename_generator(self.config, 
                config['type'] == 'local', generator=self._filename_generator)
        return self._filename_generator

    @property
    def is_auto_remove(self):
        if self.auto_remove is not None:
            return self.auto_remove
        return current_app.config.get(self.config).get('auto_remove', True)

    def get_path(self, filename):
        if filename:
            return self.storage.get_path(filename)
        return ''

    def get_link(self, filename, **kwargs):
        if filename:
            if filename.startswith('http://'):
                return filename
            return self.storage.get_link(filename, **kwargs)
        return ''

    def get_content(self, filename):
        if filename:
            return self.storage.get(filename)

    def put(self, stream, format=None, filename=None):
        if not filename:
            filename = self.filename_generator()
            if format:
                filename = '%s.%s' % (filename, format)
        filename = self.storage.put(filename, stream.read())
        return filename

    def remove(self, filename):
        if filename and self.is_auto_remove:
            self.storage.remove(filename)

    def register_signals(self, instance):
        if not hasattr(self, '_instance') and instance is not None:
            self._instance = instance
            signals.pre_delete.connect(self.pre_delete, sender=self._instance.__class__)

    def pre_delete(self, sender, document, **kwargs):
        obj = document._data.get(self.name)
        if isinstance(obj, self.proxy_class) and self.is_auto_remove:
            obj.remove()

    def _get(self, instance):
        key = self.name
        obj = instance._data.get(key)
        if not isinstance(obj, self.proxy_class) or obj is None:
            obj = self.proxy_class(self, obj)
            instance._data[key] = obj
        return instance._data[key]

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get(instance)

    def __set__(self, instance, value):
        self.register_signals(instance)

        key = self.name
        obj = instance._data.get(key)
        if isinstance(value, self.proxy_class) and value.instance == self:
            if obj and id(obj) != value and str(value) != str(value):
                self._get(instance).remove()
            instance._data[key] = value
        elif not isinstance(obj, self.proxy_class):
            obj = self.proxy_class(self, obj)
            obj.process(value)
            instance._data[key] = obj
        else:
            obj.process(value)
        instance._mark_as_changed(key)

    def to_mongo(self, value):
        if isinstance(value, self.proxy_class):
            return value.filename
        return value

    def to_python(self, value):
        if not isinstance(value, self.proxy_class):
            return self.proxy_class(self, value)
        return value


class ImageProxy(FileProxy):

    @property
    def link(self):
        return self.instance.get_link(self.filename)

    def get_link(self, width=0, height=0, ystart=0, yend=0):
        return self.instance.get_link(
            self.filename, width=width, height=height, ystart=ystart, yend=yend)


class XImageField(XFileField):
    proxy_class = ImageProxy
    default_allows = DEFAULT_IMAGE_ALLOWS


class Base64ImageProxy(FileProxy):

    @property
    def link(self):
        return self.filename

    @property
    def base64(self):
        return ('base://' + self.filename) if self.filename else ''

    def get_link(self, width=0, height=0, ystart=0, yend=0):
        return self.filename


class Base64ImageField(XImageField):
    """ Base64图片字段 """

    proxy_class = Base64ImageProxy

    def get_path(self, filename):
        return filename

    def get_link(self, filename, **kwargs):
        return filename

    def get_content(self, filename):
        if filename and filename.find('base64,') != -1:
            return filename[filename.index('base64,'):].decode('base64')

    def put(self, stream, format='png', filename=None):
        filename = 'data:image/%s;base64,' % format
        filename += base64.b64encode(stream.read())
        return filename

    def remove(self, filename):
        pass

    def to_mongo(self, value):
        if isinstance(value, self.proxy_class):
            return value.filename
        return value

    def to_python(self, value):
        if not isinstance(value, self.proxy_class):
            return self.proxy_class(self, value)
        return value


class XListField(ListField):

    def register_signals(self, instance):
        if not hasattr(self, '_instance') and instance is not None:
            self._instance = instance
            signals.pre_delete.connect(self.pre_delete, sender=self._instance.__class__)

    def pre_delete(self, sender, document, **kwargs):
        values = document._data.get(self.name) or []
        for obj in values:
            if isinstance(obj, EmbeddedDocument):
                for field in obj._fields:
                    attr = getattr(type(obj), field)
                    value = getattr(obj, field)
                    if hasattr(value, 'remove') \
                            and isinstance(value, attr.proxy_class) \
                            and attr.is_auto_remove:
                        value.remove()
            elif isinstance(self.field, XFileField) \
                    and isinstance(obj, self.field.proxy_class) \
                    and self.field.is_auto_remove:
                obj.remove()

    def __set__(self, instance, value):
        self.register_signals(instance)

        value = [self.field.to_python(x) for x in value] if value else []
        data = getattr(instance, self.name)
        if data:
            for item in data:
                if item not in value:
                    if isinstance(item, EmbeddedDocument):
                        for field in item._fields:
                            attr = getattr(item, field)
                            if hasattr(attr, 'remove'):
                                attr.remove()
                    elif hasattr(item, 'remove'):
                        item.remove()
        super(XListField, self).__set__(instance, value)


class AreaField(StringField):
    pass
