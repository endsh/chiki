# coding: utf-8
import os
import hashlib
import random
from .jinja import markup

__all__ = [
    'MediaManager',
]


class MediaManager(object):

    def __init__(self, app=None, **options):
        self.keys = ['css', 'cssx', 'js', 'jsx', 'jsfooter', 'jsfooterx']
        self.file = dict(default=self.default)
        self.hash = {}
        self.ie8 = ['ie8.min.js']
        self.ie8x = [
            'bower_components/html5shiv/dist/html5shiv.js',
            'bower_components/respond/dest/respond.src.js',
            'bower_components/respond/dest/respond.matchmedia.addListener.src.js',
        ]
        self.add(**options)
        if app is not None:
            self.init_app(app)

    @property
    def default(self):
        return dict((x, []) for x in self.keys)

    def add(self, **options):
        for key, value in options.iteritems():
            if key in self.keys:
                self._add(self.file['default'][key], value)
            else:
                self.file[key] = self.default
                for k, v in value.iteritems():
                    if k in self.keys:
                        self._add(self.file[key][k], v)

    def _add(self, instance, obj):
        if isinstance(obj, list):
            instance.extend(obj)
        elif isinstance(obj, str) or isinstance(obj, unicode):
            instance.append(obj)

    def init_app(self, app):
        self.app = app
        app.context_processor(self.context_processor)

    def context_processor(self):
        return dict(
            static_url=self.static_url,
            static_header=self.static_header,
            static_footer=self.static_footer,
            static_ie8=self.static_ie8,
        )

    def get_last(self, name):
        path = os.path.join(self.app.static_folder, name)
        if not os.path.isfile(path):
            return 0
        return os.path.getmtime(path)

    def get_hash(self, name):
        prefix = self.app.config.get('SITE_STATIC_PREFIX', '/static/')
        if type(prefix) == list:
            prefix = random.choice(prefix)

        xname = name.split('?')[0] if '?' in name else name
        path = os.path.join(self.app.static_folder, xname)
        if not os.path.isfile(path):
            xname = os.path.join('dist', xname)
            path = os.path.join(self.app.static_folder, xname)
            if not os.path.isfile(path):
                return prefix + name
            name = os.path.join('dist', name)

        with open(path) as fd:
            md5 = hashlib.md5(fd.read()).hexdigest()

        self.app.logger.info('Generate %s md5sum: %s' % (name, md5))

        tpl = '%s%s&amp;v=%s' if '?' in name else '%s%s?v=%s'
        return tpl % (prefix, name, md5[:4])

    def static_url(self, name):
        if name not in self.hash \
                or self.get_last(name) > self.hash[name]['last']:
            self.hash[name] = dict(
                hash=self.get_hash(name),
                last=self.get_last(name),
            )
        return self.hash[name]['hash']

    def static_css(self, name):
        tpl =  '    <link rel="stylesheet" href="%s">'
        return tpl % self.static_url(name)

    def static_js(self, name):
        tpl = '    <script src="%s"></script>'
        return tpl % self.static_url(name)

    def static_header(self, name='default'):
        instance = self.file[name]
        if self.app.debug:
            htmls = [self.static_css(x) for x in instance['cssx']]
            htmls.extend([self.static_js(x) for x in instance['jsx']])
        else:
            htmls = [self.static_css(x) for x in instance['css']]
            htmls.extend([self.static_js(x) for x in instance['js']])
        return markup('\n'.join(htmls))

    def static_footer(self, name='default'):
        instance = self.file[name]
        if self.app.debug:
            htmls = [self.static_js(x) for x in instance['jsfooterx']]
        else:
            htmls = [self.static_js(x) for x in instance['jsfooter']]
        return markup('\n'.join(htmls))

    def static_ie8(self):
        ie8 = self.ie8x if self.app.debug else self.ie8
        htmls = [self.static_js(x) for x in ie8]
        return markup('    <!--[if lt IE 9]>\n%s\n    <![endif]-->' % '\n'.join(htmls)) 