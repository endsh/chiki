# coding: utf-8
import re
import sys
import difflib
from chiki.utils import strip
from flask import current_app, request
from flask.signals import got_request_exception
from flask.ext.restful import Api as _Api, Resource as _Resource, reqparse
from flask.ext.restful.utils import error_data
from werkzeug.http import HTTP_STATUS_CODES
from .const import abort

__all__ = [
    'api', 'wapi', 'xapi', 'success', 'Resource',
]


class Api(_Api):

    default_change_400_to_200 = False

    def error_router(self, original_handler, e):
        if self._has_fr_route() or isinstance(getattr(e, 'data', ''), dict):
            try:
                return self.handle_error(e)
            except Exception:
                pass
        return original_handler(e)

    def handle_error(self, e):
        got_request_exception.send(current_app._get_current_object(), exception=e)

        if not hasattr(e, 'code') and current_app.propagate_exceptions:
            exc_type, exc_value, tb = sys.exc_info()
            if exc_value is e:
                raise
            else:
                raise e
        code = getattr(e, 'code', 500)
        data = getattr(e, 'data', error_data(code))
        headers = {}

        if code >= 500:
            if sys.exc_info() == (None, None, None):
                current_app.logger.error("Internal Error")
            else:
                current_app.logger.exception("Internal Error")

        help_on_404 = current_app.config.get("ERROR_404_HELP", True)
        if code == 404 and help_on_404 and ('message' not in data or
                                            data['message'] == HTTP_STATUS_CODES[404]):
            rules = dict([(re.sub('(<.*>)', '', rule.rule), rule.rule)
                          for rule in current_app.url_map.iter_rules()])
            close_matches = difflib.get_close_matches(request.path, rules.keys())
            if close_matches:
                # If we already have a message, add punctuation and continue it.
                if "message" in data:
                    data["message"] += ". "
                else:
                    data["message"] = ""

                data['message'] += 'You have requested this URI [' + request.path + \
                                   '] but did you mean ' + \
                                   ' or '.join((
                                       rules[match] for match in close_matches)
                                   ) + ' ?'

        if code == 405:
            headers['Allow'] = e.valid_methods

        error_cls_name = type(e).__name__
        if error_cls_name in self.errors:
            custom_data = self.errors.get(error_cls_name, {})
            code = custom_data.get('status', 500)
            data.update(custom_data)

        if code == 406 and self.default_mediatype is None:
            supported_mediatypes = list(self.representations.keys())
            fallback_mediatype = supported_mediatypes[0] if supported_mediatypes else "text/plain"
            resp = self.make_response(
                data,
                code,
                headers,
                fallback_mediatype=fallback_mediatype,
            )
        else:
            if code == 400 and current_app.config.get('CHANGE_400_TO_200', self.default_change_400_to_200):
                code = 200
            resp = self.make_response(data, code, headers)

        if code == 401:
            resp = self.unauthorized(resp)
        return resp


class WApi(Api):
    default_change_400_to_200 = True


class Resource(_Resource):

    def __init__(self):
        super(Resource, self).__init__()
        self.not_strips = tuple()
        self.req = reqparse.RequestParser()
        self.add_args()

    def add_args(self):
        pass

    def get_args(self):
        return strip(self.req.parse_args(), *self.not_strips)


api = Api()
wapi = WApi()


def success(_data=None, **kwargs):
    if kwargs.get('__external'):
        kwargs.setdefault('code', 0)
        kwargs.setdefault('key', 'SUCCESS')
        return dict(**kwargs)
    res = dict(code=0, key='SUCCESS')
    if _data is not None:
        res['data'] = _data
    elif kwargs:
        res['data'] = kwargs
    return res
