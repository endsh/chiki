# coding: utf-8
from flask.ext.admin.model.filters import convert as _convert
from flask.ext.admin.contrib.mongoengine.filters import (
    BaseMongoEngineFilter, FilterEqual, FilterNotEqual, FilterConverter,
)
from bson.objectid import ObjectId


class BaseReferenceFilter(BaseMongoEngineFilter):

    def __init__(self, column, name, ref_type=None, options=None, data_type=None):
        super(BaseReferenceFilter, self).__init__(column, name, options, data_type)
        self.ref_type = ref_type
    
    def clean(self, value):
        if self.ref_type == int:
            return int(float(value))
        elif self.ref_type == float:
            return float(value)
        elif self.ref_type == ObjectId:
            if len(str(value)) != 24:
                return '0'*24
        return value


class ReferenceEqualFilter(FilterEqual, BaseReferenceFilter):
    pass


class ReferenceNotEqualFilter(FilterNotEqual, BaseReferenceFilter):
    pass


class BaseObjectIdFilter(BaseMongoEngineFilter):

    def __init__(self, column, name, ref_type=None, options=None, data_type=None):
        super(BaseObjectIdFilter, self).__init__(column, name, options, data_type)
        self.ref_type = ref_type
    
    def clean(self, value):
        if self.ref_type == int:
            return int(float(value))
        elif self.ref_type == float:
            return float(value)
        elif self.ref_type == ObjectId:
            if len(str(value)) != 24:
                return '0'*24
        return value


class ObjectIdEqualFilter(FilterEqual, BaseObjectIdFilter):
    pass


class ObjectIdNotEqualFilter(FilterNotEqual, BaseObjectIdFilter):
    pass


class BaseListFilter(BaseMongoEngineFilter):

    def __init__(self, column, name, ref_type=None, options=None, data_type=None):
        super(BaseListFilter, self).__init__(column, name, options, data_type)
        self.ref_type = ref_type
    
    def clean(self, value):
        if self.ref_type == int:
            return int(float(value))
        elif self.ref_type == float:
            return float(value)
        elif self.ref_type == ObjectId:
            if len(str(value)) != 24:
                return '0'*24
        return value


class ListContainFilter(BaseListFilter):

    def apply(self, query, value):
        flt = {'%s' % self.column.name: value}
        return query.filter(**flt)

    def operation(self):
        return '包含'


class KFilterConverter(FilterConverter):

    reference_filters = (ReferenceEqualFilter, ReferenceNotEqualFilter)
    object_id_filters = (ObjectIdEqualFilter, ObjectIdNotEqualFilter)
    list_filters = (ListContainFilter,)

    def convert(self, type_name, column, name, ref_type=None):
        filter_name = type_name.lower()

        if filter_name in self.converters:
            if ref_type:
                return self.converters[filter_name](column, name, ref_type)
            else:
                return self.converters[filter_name](column, name)

        return None

    @_convert('ReferenceField')
    def conv_reference(self, column, name, ref_type=None):
        return [f(column, name, ref_type) for f in self.reference_filters]

    @_convert('ObjectIdField')
    def conv_object_id(self, column, name, ref_type=None):
        return [f(column, name, ref_type) for f in self.object_id_filters]

    @_convert('ListField')
    def conv_list(self, column, name, ref_type=None):
        return [f(column, name, ref_type) for f in self.list_filters]


def get_options(self, view):
    options = self.options or self.column.choices
    if options:
        if callable(options):
            options = options()
        return options
    return None


BaseMongoEngineFilter.get_options = get_options
