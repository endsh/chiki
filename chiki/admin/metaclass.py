# coding: utf-8
from flask.ext.admin.base import AdminViewMeta
from .common import _admin_registry


class CoolAdminMeta(AdminViewMeta):
    """ Metaclass for all ModelView. """

    def __new__(cls, name, bases, attrs):
        _new_class = super(CoolAdminMeta, cls).__new__(cls, name, bases, attrs)
        _admin_registry[name] = _new_class
        return _new_class
