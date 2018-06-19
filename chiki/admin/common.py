# coding: utf-8
from mongoengine.base.common import _document_registry

_admin_registry = {}

documents = _document_registry
admin_views = _admin_registry
