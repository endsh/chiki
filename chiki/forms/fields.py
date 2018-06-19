# coding: utf-8
from datetime import datetime
from flask import current_app
from flask.ext.admin.model.fields import InlineFieldList
from flask.ext.mongoengine.wtf.fields import ModelSelectMultipleField as _ModelSelectMultipleField
from wtforms.fields import Field, StringField, SelectField, SelectMultipleField
from wtforms.fields import FileField as _FileField, DateTimeField, TextAreaField
from wtforms.fields import Label as _Label
from wtforms.widgets import RadioInput, CheckboxInput
from wtforms.validators import ValidationError
from wtforms.utils import unset_value
from .widgets import VerifyCode, UEditor, KListWidget, DragSelectWidget
from .widgets import FileInput, ImageInput, Base64ImageInput, AreaInput, WangEditor, DragInput
from ..verify import get_verify_code, validate_code
from ..mongoengine.fields import FileProxy

__all__ = [
    'VerifyCodeField', 'KDateField', 'KRadioField', 'KCheckboxField',
    'DragSelectWidget', 'UEditorField', 'FileField', 'ImageField', 'Base64ImageField',
    'AreaField', 'ListField', 'ModelSelectMultipleField', 'WangEditorField',
    'Label',
]

DEFAULT_ALLOWS = ['txt', 'bz2', 'gz', 'tar', 'zip', 'rar', 'apk', 'jpg', 'jpeg', 'png', 'gif', 'bmp']
DEFAULT_IMAGE_ALLOWS = ['jpg', 'jpeg', 'png', 'gif', 'bmp']


class VerifyCodeField(Field):

    widget = VerifyCode()

    def __init__(self, label=None, key='verify_code',
            hidden=False, invalid_times=1, code_len=0, **kwargs):
        super(VerifyCodeField, self).__init__(label, **kwargs)
        self.key = key
        self.invalid_times = invalid_times
        self.hidden = hidden
        self.code_len = code_len if code_len > 0 else current_app.config.get('VERIFY_CODE_LEN', 4)
        self.code, self.times = get_verify_code(key, code_len=self.code_len)
        self._refresh = False

    def process_data(self, value):
        if self.hidden == True:
            self.data = self.code
        else:
            self.data = ''

    def process_formdata(self, valuelist):
        if not valuelist or not valuelist[0]:
            self.data = ''
        else:
            self.data = valuelist[0]

    def _value(self):
        return self.data

    def need_refresh(self):
        return self._refresh

    def validate(self, field, extra_validators=tuple()):
        self.errors = list(self.process_errors)
        if self.data.lower() != self.code.lower():
            self.times += 1
            validate_code(self.key)
            self.errors.append(u'验证码错误')

        if self.times >= self.invalid_times:
            self._refresh = True
            self.code, self.times = get_verify_code(self.key,
                refresh=True, code_len=self.code_len)
            self.errors.append(u'验证码已失效')

        return len(self.errors) == 0


class KRadioField(SelectField):
    widget = KListWidget(html_tag='div', sub_tag='label', prefix_label=False)
    option_widget = RadioInput()


class KCheckboxField(SelectMultipleField):
    widget = KListWidget(html_tag='div', sub_tag='label', prefix_label=False)
    option_widget = CheckboxInput()


class DragSelectField(SelectMultipleField):
    widget = DragSelectWidget()
    option_widget = DragInput()

    def iter_choices(self):
        if self.choices:
            for value, label in self.choices:
                selected = self.data is not None and self.coerce(value) in self.data
                if not selected:
                    yield (value, label, selected)
            choices = dict(self.choices)
            for value in self.data:
                yield (value, choices.get(value), True)


class KDateField(DateTimeField):

    def __init__(self, label=None, validators=None, format='%Y-%m-%d', allow_null=False, **kwargs):
        super(KDateField, self).__init__(label, validators, format, **kwargs)
        self.allow_null = allow_null

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            if self.data and type(self.data) in (str, unicode):
                return self.data
            return self.data and self.data.strftime(self.format) or ''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            if date_str:
                try:
                    self.data = datetime.strptime(date_str, self.format)
                except ValueError:
                    self.data = None
                    raise ValueError(self.gettext('Invalid date/time input'))
            else:
                self.data = None
                if not self.allow_null:
                    raise ValueError(self.gettext('Invalid date/time input'))


class UEditorField(StringField):
    widget = UEditor()


class FileField(_FileField):

    widget = FileInput()

    def __init__(self, label=None, max_size=None, allows=DEFAULT_ALLOWS, place=None, **kwargs):
        self.delete = False
        self.max_size = max_size
        self.allows = allows
        self.place = place
        super(FileField, self).__init__(label=label, **kwargs)

    def pre_validate(self, form, extra_validators=tuple()):
        if not self.data:
            return

        format = self.data.filename.split('.')[-1]
        if self.allows and format.lower() not in self.allows:
            raise ValidationError(u'%s 格式不支持上传' % format)

        if self.max_size and self.data.content_length > self.max_size:
            raise ValidationError(u'文件太大(%d/%d)' % (
                self.max_size, self.data.content_length))

    def process(self, formdata, data=unset_value):
        self.process_errors = []
        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        try:
            self.process_data(data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

        if formdata:
            if self.name in formdata:
                self.raw_data = formdata.getlist(self.name)
            else:
                self.raw_data = []
            self.process_formdata(self.raw_data)

            key = '%s-delete' % self.name
            if formdata.get(key) == 'true':
                self.delete = True

    def is_empty(self):
        if self.data:
            self.data.stream.seek(0)
            first_char = self.data.stream.read(1)
            self.data.stream.seek(0)
            return not bool(first_char)
        return True

    def populate_obj(self, obj, name):
        if self.data and not self.is_empty():
            setattr(obj, name, self.data)
        elif self.delete:
            setattr(obj, name, None)


class ImageField(FileField):

    widget = ImageInput()

    def __init__(self, label=None, max_size=None, allows=DEFAULT_IMAGE_ALLOWS, place=None, **kwargs):
        super(ImageField, self).__init__(label=label, **kwargs)


class Base64ImageField(ImageField):

    widget = Base64ImageInput()


class AreaField(Field):

    widget = AreaInput()
    defaults = dict(province=u'省份', city=u'城市', county=u'县/区')

    def process(self, formdata, data=unset_value):
        self.process_errors = []
        if data is unset_value:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        try:
            self.process_data(data)
        except ValueError as e:
            self.process_errors.append(e.args[0])

        if formdata:
            area = []
            for field in ['province', 'city', 'county']:
                name = '%s_%s' % (self.name, field)
                data = formdata.get(name, '').strip()
                if data.strip() and data != self.defaults.get(field):
                    area.append(data)
            if len(area) == 3:
                self.data = '|'.join(area)


class ListField(InlineFieldList):

    def populate_obj(self, obj, name):
        values = getattr(obj, name, None) or []
        _fake = type(str('_fake'), (object, ), {})

        output = []
        value_len = len(values)
        for field in self.entries:
            if not self.should_delete(field):
                index = int(field.name.split('-')[-1])
                data = values[index] if index < value_len else None
                fake_obj = _fake()
                fake_obj.data = data
                field.populate_obj(fake_obj, 'data')
                if not fake_obj.data and isinstance(data, FileProxy):
                    data.remove()
                output.append(fake_obj.data)
        setattr(obj, name, output)


class ModelSelectMultipleField(_ModelSelectMultipleField):

    def pre_validate(self, form):
        if not self.allow_blank:
            if not self.data:
                raise ValidationError('Not a valid choice')


class WangEditorField(TextAreaField):
    widget = WangEditor()


class Label(_Label, Field):

    def __init__(self, text, field_id='', **kwargs):
        _Label.__init__(self, field_id, text)
        Field.__init__(self, **kwargs)
