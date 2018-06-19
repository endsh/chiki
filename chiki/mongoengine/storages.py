# coding: utf-8
import os
import shutil
from flask import current_app


def is_empty_folder(folder):
    for root, dirs, files in os.walk(folder):
        if len(dirs) == 0 and len(files) == 0:
            return True
        return False


def load_file(name):
    if os.path.exists(name):
        with open(name) as fd:
            return fd.read()


def save_file(name, content):
    dirname = os.path.dirname(name)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(name, 'w+') as fd:
        fd.write(content)


def remove_file(name, path):
    if os.path.exists(name):
        os.remove(name)

        folder = os.path.dirname(name)
        while folder != path:
            if is_empty_folder(folder):
                shutil.rmtree(folder)
            folder = os.path.dirname(folder)


class BaseFile(object):

    def __init__(self, conf):
        self.conf = conf

    def get_path(self, name):
        return name

    def get_link(self, name, **kwargs):
        return self.conf['link'] % name


class LocalFile(BaseFile):

    def __init__(self, conf):
        super(LocalFile, self).__init__(conf)
        self.path = self.conf['path']

    def get_path(self, name):
        return os.path.join(self.path, name)

    def get(self, name):
        return load_file(self.get_path(name))

    def put(self, name, content):
        save_file(self.get_path(name), content)
        return name

    def remove(self, name):
        return remove_file(self.get_path(name), self.conf['path'])


class OSSFile(BaseFile):

    def __init__(self, conf):
        super(OSSFile, self).__init__(conf)
        from oss.oss_api import OssAPI
        self.oss = OssAPI(
            conf['host'],
            conf['access_id'],
            conf['secret_access_key'],
        )

    def get_link(self, name, width=0, height=0, ystart=0, yend=0, source=False):
        link = self.conf['link'] % name
        if source:
            return link

        format = name.split('.')[-1]
        if format not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            format = 'jpg'

        attrs = []
        if width != 0:
            attrs.append('w_%d' % width)
        if height != 0:
            attrs.append('h_%d' % height)
        if attrs:
            if width and height:
                attrs.append('m_fill')
            attrs.append('limit_0')
        if attrs:
            return link + '?x-oss-process=image/resize,' + ','.join(attrs) + '/format,' + format
        return link

    def get(self, name):
        res = self.oss.get_object(self.conf['bucket'], name)
        if (res.status / 100) == 2:
            return res.read()
        return ''

    def put(self, name, content, type=None):
        name = '%s.%s' % (name, type) if type is not None else name
        if not name.startswith(self.conf.get('prefix')):
            name = self.conf.get('prefix', '') + name
        res = self.oss.put_object_from_string(self.conf['bucket'], name, content)
        if (res.status / 100) == 2:
            return name
        current_app.logger.error('oss error: \n' + res.read())
        return ''

    def remove(self, name):
        res = self.oss.delete_object(self.conf['bucket'], name)
        return (res.status / 100) == 2


def _get_storage(conf):
    if conf['type'] == 'local':
        return LocalFile(conf)
    elif conf['type'] == 'oss':
        return OSSFile(conf)
    raise ValueError('Cannot support type (%s) of config' % conf['type'])


_storages = {}


def get_storage(key, conf):
    global _storages
    if key not in _storages:
        _storages[key] = _get_storage(conf)
    return _storages[key]
