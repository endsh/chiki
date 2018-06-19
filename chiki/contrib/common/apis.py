# coding: utf-8
from collections import defaultdict
from chiki.utils import get_version, get_os
from chiki.api import success
from flask import current_app, request
from flask.ext.restful import Resource
from chiki.api.const import *
from chiki.utils import parse_spm
from chiki.base import db
from chiki.contrib.common.models import (
    Enable, API, Icon, TPL, AndroidVersion,
    Action, Slide, Option
)


class Global(Resource):

    def get(self):
        res = dict(apis={}, icons={}, tpls={}, actions=defaultdict(list), options={})
        version = get_version()

        for api in API.objects.all():
            if api.key == 'global':
                res['expire'] = api.expire
            res['apis'][api.key] = api.detail

        for icon in Icon.objects.all():
            res['icons'][icon.key] = icon.icon.base64

        for option in Option.objects.all():
            res['options'][option.key] = option.value
        res['options']['uuid'] = '0'
        res['options']['channel'] = '0'

        tpls = TPL.objects(enable__in=Enable.get())
        for tpl in tpls:
            res['tpls'][tpl.key] = dict(
                key=tpl.key,
                name=tpl.name,
                url=tpl.tpl.link,
                modified=str(tpl.modified),
            )

        query = db.Q(enable__in=Enable.get())
        if get_os() == 2:
            query = query & (db.Q(android_start__lte=version) | db.Q(android_start=None)) & \
                (db.Q(android_end__gte=version) | db.Q(android_end=None))
        elif get_os() == 1:
            query = query & (db.Q(ios_start__lte=version) | db.Q(ios_start=None)) & \
                (db.Q(ios_end__gte=version) | db.Q(ios_end=None))

        actions = Action.objects(query).order_by('sort')
        for action in actions:
            if action.module:
                res['actions'][action.module].append(action.detail)

        slides = Slide.objects(query).order_by('sort')
        for slide in slides:
            if slide.module:
                res['actions'][slide.module].append(slide.detail)

        if hasattr(self, 'handle') and callable(self.handle):
            self.handle(res)

        return res


class AndroidLatest(Resource):

    def get(self):
        item = AndroidVersion.objects(enable__in=Enable.get()).order_by('-id').first()
        if item:
            host = current_app.config.get('WEB_HOST')
            spm = parse_spm(request.args.get('spm'))
            url = item.url or 'http://%s/android/latest.html?channel=%d' % (host, spm[2] or 1001)
            return success(
                version=item.version,
                code=item.id,
                log=item.log,
                url=url,
                force=item.force,
                date=str(item.created).split(' ')[0],
            )
        abort(SERVER_ERROR)


def init_common_apis(api):
    api.add_resource(Global, '/global')
    api.add_resource(AndroidLatest, '/android/latest')
