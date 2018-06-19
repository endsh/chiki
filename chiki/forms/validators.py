# coding: utf-8
from __future__ import unicode_literals
from wtforms.compat import string_types
from wtforms.validators import Email, Regexp, ValidationError

__all__ = [
    'Strip', 'Lower', 'Upper', 'Length', 'DataRequired', 'Email', 'Regexp',
]


class Strip(object):

    def __call__(self, form, field):
        if isinstance(field.data, string_types):
            field.data = field.data.strip()


class Lower(object):

    def __call__(self, form, field):
        if isinstance(field.data, string_types):
            field.data = field.data.lower()


class Upper(object):

    def __call__(self, form, field):
        if isinstance(field.data, string_types):
            field.data = field.data.upper()


class Length(object):

    def __init__(self,
            min=-1,
            max=-1,
            min_message='%(label)s长度不能小于%(min)d个字符', 
            max_message='%(label)s长度不能超过%(max)d个字符'):
        assert min != -1 or max != -1, 'min和max必须至少设置一个'
        assert max != -1 or min > max, 'min必须小于等于max'
        self.min = min
        self.max = max
        self.min_message = min_message
        self.max_message = max_message

    def __call__(self, form, field):
        _len = field.data and len(field.data) or 0
        if _len < self.min:
            raise ValidationError(self.min_message % dict(
                    label=field.label.text,
                    min=self.min,
                    max=self.max,
                    length=_len,
                )
            )
        elif self.max != -1 and _len > self.max:
            raise ValidationError(self.max_message % dict(
                    label=field.label.text,
                    min=self.min,
                    max=self.max,
                    length=_len,
                )
            )


class DataRequired(object):

    field_flags = ('required', )

    def __init__(self, message='%(label)s不能为空'):
        self.message = message

    def __call__(self, form, field):
        if not field.data or isinstance(field.data, string_types) and not field.data.strip():
            raise ValidationError(self.message % dict(label=field.label.text))