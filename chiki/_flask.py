# coding: utf-8
import datetime
from flask import Flask as _Flask, Blueprint, request, render_template
from flask.json import JSONEncoder as _JSONEncoder
from flask.ext.login import login_required, current_user
from flask.ext.restful.representations.json import settings
from werkzeug.datastructures import ImmutableDict
from bson import ObjectId
from .utils import json_success, is_ajax


__all__ = [
    'JSONEncoder', 'Flask',
]


class JSONEncoder(_JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '__getitem__') and hasattr(obj, 'keys'):
            return dict(obj)
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, ObjectId):
            return str(obj)
        return _JSONEncoder.default(self, obj)


settings['cls'] = JSONEncoder


class Flask(_Flask):

    patch_url = False
    json_encoder = JSONEncoder
    jinja_options = ImmutableDict(
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[
            'jinja2.ext.autoescape',
            'jinja2.ext.with_',
            'jinja2.ext.do',
        ],
    )


def bp_list(self, model, url, tpl, endpoint=None, login=False,
        per_page=10, handle=lambda x: x.order_by('-created'), **kwargs):
    endpoint = endpoint or model.__name__.lower()
    wrapper = login_required if login else lambda x: x

    @self.route(url, endpoint=endpoint)
    @wrapper
    def view():
        page = max(1, request.args.get('page', 1, int))
        per = max(1, min(100, request.args.get('per_page', per_page, int)))
        query = dict()
        for key, value in kwargs.iteritems():
            if callable(value):
                query[key] = value()
            elif key == 'user' and value is True:
                query[key] = current_user.id
            else:
                query[key] = value
        pag = handle(model.objects(**query)).paginate(page=page, per_page=per)
        if page > 1 or is_ajax():
            return json_success(
                html=render_template(tpl, pag=pag),
                next=pag.next_link,
            )
        return render_template(tpl, pag=pag)

Blueprint.list = bp_list
