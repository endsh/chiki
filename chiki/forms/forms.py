# coding: utf-8
import os
import hmac
import werkzeug.datastructures
from datetime import datetime, timedelta
from flask import current_app, request, session
from hashlib import sha1
from wtforms.compat import with_metaclass
from wtforms.form import Form as _Form
from wtforms.form import FormMeta as _FormMeta
from wtforms.validators import ValidationError
from wtforms.ext.csrf.fields import CSRFTokenField
from .fields import VerifyCodeField


__all__ = [
    'FormMeta', 'BaseForm', 'Form',
]


class FormMeta(_FormMeta):

    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        cls._unbound_fields = None
        cls._wtforms_meta = None

    def __call__(cls, *args, **kwargs):
        if cls._unbound_fields is None:
            fields = []
            for name in dir(cls):
                if not name.startswith('_') or name == '_id':
                    unbound_field = getattr(cls, name)
                    if hasattr(unbound_field, '_formfield'):
                        fields.append((name, unbound_field))
            fields.sort(key=lambda x: (x[1].creation_counter, x[0]))
            cls._unbound_fields = fields

        if cls._wtforms_meta is None:
            bases = []
            for mro_class in cls.__mro__:
                if 'Meta' in mro_class.__dict__:
                    bases.append(mro_class.Meta)
            cls._wtforms_meta = type('Meta', tuple(bases), {})

        obj = type.__call__(cls, *args, **kwargs)
        for name, unbound_field in cls._unbound_fields:
            if hasattr(unbound_field, 'addon'):
                setattr(getattr(obj, name), 'addon', getattr(unbound_field, 'addon'))
        return obj

    def __setattr__(cls, name, value):
        if name == 'Meta':
            cls._wtforms_meta = None
        elif (not name.startswith('_') or name == '_id') \
                and hasattr(value, '_formfield'):
            cls._unbound_fields = None
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name):
        if not name.startswith('_') or name == '_id':
            cls._unbound_fields = None
        type.__delattr__(cls, name)


class FormMixin(object):

    def is_submitted(self):
        return request and request.method in ('PUT', 'POST')

    def validate_on_submit(self):
        return self.is_submitted() and self.validate()


class BaseForm(with_metaclass(FormMeta, _Form), FormMixin):
    pass


class _Auto():
    pass


class Form(with_metaclass(FormMeta, _Form), FormMixin):

    TIME_FORMAT = '%Y%m%d%H%M%S'
    TIME_LIMIT = timedelta(minutes=30)
    csrf_token = CSRFTokenField()

    def __init__(self, formdata=_Auto, obj=None, prefix='', **kwargs):
        if formdata is _Auto:
            if self.is_submitted():
                formdata = request.form
                if request.files:
                    formdata = formdata.copy()
                    formdata.update(request.files)
                elif request.json:
                    formdata = werkzeug.datastructures.MultiDict(request.json)
            else:
                formdata = None
        super(Form, self).__init__(formdata, obj, prefix, **kwargs)
        self.csrf_token.current_token = self.generate_csrf_token()

    def generate_csrf_token(self):
        secret_key = current_app.config.get('SECRET_KEY')
        if secret_key is None:
            raise Exception('must set SECRET_KEY in config for it to work')
        time_limit = current_app.config.get('SECRET_TIME_LIMIT', self.TIME_LIMIT)
        if 'csrf' not in session:
            session['csrf'] = sha1(os.urandom(64)).hexdigest()

        self.csrf_token.csrf_key = session['csrf']
        if time_limit:
            expires = (datetime.now() + time_limit).strftime(self.TIME_FORMAT)
            csrf_build = '%s%s' % (session['csrf'], expires)
        else:
            expires = ''
            csrf_build = session['csrf']

        hmac_csrf = hmac.new(secret_key, csrf_build.encode('utf8'), digestmod=sha1)
        return '%s##%s' % (expires, hmac_csrf.hexdigest())

    def validate_csrf_token(self, field):
        if not field.data or '##' not in field.data:
            raise ValidationError('CSRF token missing')

        secret_key = current_app.config.get('SECRET_KEY')

        expires, hmac_csrf = field.data.split('##')
        check_val = (field.csrf_key + expires).encode('utf8')
        hmac_compare = hmac.new(secret_key, check_val, digestmod=sha1)
        if hmac_compare.hexdigest() != hmac_csrf:
            raise ValidationError('CSRF failed')

        time_limit = current_app.config.get('SECRET_TIME_LIMIT', self.TIME_LIMIT)
        if time_limit:
            now_formatted = datetime.now().strftime(self.TIME_FORMAT)
            if now_formatted > expires:
                raise ValidationError('CSRF token expired')

    @property
    def data(self):
        d = super(Form, self).data
        d.pop('csrf_token')
        return d

    def populate_obj(self, obj):
        for name, field in self._fields.iteritems():
            if field.type != 'Label':
                field.populate_obj(obj, name)
