# coding: utf-8
from flask.ext.admin import form
from flask.ext.admin.contrib.mongoengine.form import CustomModelConverter
from flask.ext.admin.model.fields import AjaxSelectField, AjaxSelectMultipleField
from flask.ext.mongoengine.wtf import orm, fields as mongo_fields
from mongoengine import ReferenceField
from ..forms.fields import FileField, ImageField, Base64ImageField
from ..forms.fields import AreaField, ListField, ModelSelectMultipleField


class KModelConverter(CustomModelConverter):

    @orm.converts('XFileField')
    def conv_kfile(self, model, field, kwargs):
        return FileField(max_size=field.max_size, allows=field.allows,
                         place=field.place, **kwargs)

    @orm.converts('XImageField')
    def conv_kimage(self, model, field, kwargs):
        return ImageField(max_size=field.max_size, allows=field.allows,
                          place=field.place, **kwargs)

    @orm.converts('Base64ImageField')
    def conv_base64_image(self, model, field, kwargs):
        return Base64ImageField(max_size=field.max_size, allows=field.allows,
                                place=field.place, **kwargs)

    @orm.converts('AreaField')
    def conv_area(self, model, field, kwargs):
        return AreaField(**kwargs)

    @orm.converts('ListField')
    def conv_list(self, model, field, kwargs):
        if field.field is None:
            raise ValueError('ListField "%s" must have field specified for model %s' % (field.name, model))

        if isinstance(field.field, ReferenceField):
            loader = getattr(self.view, '_form_ajax_refs', {}).get(field.name)
            if loader:
                return AjaxSelectMultipleField(loader, **kwargs)

            kwargs['widget'] = form.Select2Widget(multiple=True)

            doc_type = field.field.document_type
            return ModelSelectMultipleField(model=doc_type, **kwargs)

        field.field.name = '%s__field' % field.name
        if field.field.choices:
            kwargs['multiple'] = True
            return self.convert(model, field.field, kwargs)

        unbound_field = self.convert(model, field.field, {})
        return ListField(unbound_field, min_entries=0, **kwargs)

    @orm.converts('XListField')
    def conv_xlist(self, model, field, kwargs):
        if field.field is None:
            raise ValueError('ListField "%s" must have field specified for model %s' % (field.name, model))

        if isinstance(field.field, ReferenceField):
            loader = getattr(self.view, '_form_ajax_refs', {}).get(field.name)
            if loader:
                return AjaxSelectMultipleField(loader, **kwargs)

            kwargs['widget'] = form.Select2Widget(multiple=True)

            doc_type = field.field.document_type
            return ModelSelectMultipleField(model=doc_type, **kwargs)

        field.field.name = '%s__field' % field.name
        if field.field.choices:
            kwargs['multiple'] = True
            return self.convert(model, field.field, kwargs)

        unbound_field = self.convert(model, field.field, {})
        return ListField(unbound_field, min_entries=0, **kwargs)

    @orm.converts('ReferenceField')
    def conv_Reference(self, model, field, kwargs):
        kwargs['allow_blank'] = not field.required

        loader = getattr(self.view, '_form_ajax_refs', {}).get(field.name)
        if loader:
            return AjaxSelectField(loader, **kwargs)

        kwargs['widget'] = form.Select2Widget()
        queryset = kwargs.get('queryset')
        if callable(queryset):
            kwargs['queryset'] = queryset(field.document_type)
        return orm.ModelConverter.conv_Reference(self, model, field, kwargs)
