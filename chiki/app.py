# coding: utf-8
import os
import redis
import traceback
import logging
from StringIO import StringIO
from flask import Blueprint, current_app, Response, render_template
from flask import request, redirect, url_for, send_file
from flask.ext.babelex import Babel
from flask.ext.login import login_required, current_user
from flask.ext.mail import Mail
from flask.ext.debugtoolbar import DebugToolbarExtension
from flask.ext.session import Session
from chiki.admin.common import _document_registry
from chiki.base import db, cache
from chiki.cool import cm
from chiki.contrib.common import Item, Page, Choices, Menu, TraceLog, ImageItem
from chiki.contrib.common import Complaint
from chiki.contrib.common import bp as common_bp
from chiki.contrib.users import um
from chiki.contrib.admin import admin
from chiki.contrib.admin.models import AdminUser
from chiki.contrib.admin.views import bp as login_bp
from chiki.settings import DATA_ROOT
from chiki.jinja import init_jinja
from chiki.logger import init_logger, DEBUG_LOG_FORMAT
from chiki.media import MediaManager
from chiki.oauth import init_oauth
from chiki.settings import TEMPLATE_ROOT
from chiki.third import init_third
from chiki.upimg import init_upimg
from chiki.web import error as error_msg
from chiki.utils import sign, json_success
from chiki._flask import Flask

__all__ = [
    "init_app", 'init_web', 'init_api', "init_admin", "start_error",
    'register_app', 'register_web', 'register_api', 'register_admin',
    'apps',
]

DEBUG_TB_PANELS = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
    'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel',
    'chiki.debug_toolbar_mongo.panel.MongoDebugPanel',
)


media = MediaManager()
apps = dict()


def init_db(db):
    for name, doc in _document_registry.iteritems():
        if not doc._meta['abstract'] and doc._is_document:
            setattr(db, name, doc)


def init_page(app):

    if app.config.get('PAGE_LOGIN_REQUIRED'):
        @app.route('/page/<int:id>.html')
        @login_required
        def page(id):
            page = Page.objects(id=id).get_or_404()
            return render_template('page.html', page=page)

        @app.route('/page/<key>.html')
        @login_required
        def page2(key):
            page = Page.objects(key=key).get_or_404()
            return render_template('page.html', page=page)

    else:
        @app.route('/page/<int:id>.html')
        def page(id):
            page = Page.objects(id=id).get_or_404()
            return render_template('page.html', page=page)

        @app.route('/page/<key>.html')
        def page2(key):
            page = Page.objects(key=key).get_or_404()
            return render_template('page.html', page=page)


def init_babel(app):
    """ 初始化语言本地化 """

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        return 'zh_Hans_CN'


def init_redis(app):
    if app.config.get('REDIS'):
        conf = app.config.get('REDIS')
        app.redis = redis.StrictRedis(
            host=conf.get('host', '127.0.0.1'),
            port=conf.get('port', 6379),
            password=conf.get('password', ''),
            db=conf.get('db', 0),
        )
        app.config.setdefault('SESSION_TYPE', 'redis')
        app.config.setdefault('SESSION_REDIS', app.redis)
        app.config.setdefault('SESSION_USE_SIGNER', True)
        app.config.setdefault('SESSION_KEY_PREFIX',
                              conf.get('prefix', '') + '_sess_')


def init_error_handler(app):
    """ 错误处理 """

    @app.errorhandler(403)
    def error_403(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def error_404(error):
        app.logger.error('404 - %s' % error)
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def error_500(error):
        return render_template('500.html'), 500


# def before_request():
#     """ Admin 权限验证 """

#     auth = request.authorization
#     username = current_app.config.get('ADMIN_USERNAME')
#     password = current_app.config.get('ADMIN_PASSWORD')
#     if username and not (
#             auth and auth.username == username and
#             auth.password == password):
#         return Response(u'请登陆', 401,
#                         {'WWW-Authenticate': 'Basic realm="login"'})


def before_request():
    """ Admin 权限验证 """
    if not current_user.is_authenticated() and request.endpoint and \
            request.endpoint != current_app.login_manager.login_view and \
            not request.endpoint == 'admin.static' and \
            not request.endpoint.endswith('dash_oauth_callback'):
        return current_app.login_manager.unauthorized()


def init_app(init=None, config=None, pyfile=None,
             template_folder='templates', index=False, error=True,
             is_web=False, is_api=False, manager=False):
    """ 创建应用 """
    app = Flask(__name__, template_folder=template_folder)
    if os.environ.get('LOGGER_DEBUG'):
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(DEBUG_LOG_FORMAT))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)

    init_db(db)

    if config:
        app.config.from_object(config)
    if pyfile:
        app.config.from_pyfile(pyfile)

    ENVVAR = app.config.get('ENVVAR')
    if ENVVAR and os.environ.get(ENVVAR):
        env = os.environ.get(ENVVAR)
        for pyfile in env.split('|'):
            if pyfile.startswith('./'):
                pyfile = os.path.join(os.getcwd(), pyfile)
            app.logger.info('load config pyfile: %s' % pyfile)
            app.config.from_pyfile(pyfile)

    if app.debug:
        app.config.setdefault('DEBUG_TB_ENABLED', True)
        app.config.setdefault('DEBUG_TB_PANELS', DEBUG_TB_PANELS)
        app.config.setdefault('DEBUG_TB_INTERCEPT_REDIRECTS', False)

    DebugToolbarExtension(app)

    app.config.setdefault('SESSION_REFRESH_EACH_REQUEST', False)
    app.is_web = is_web
    app.is_api = is_api
    app.is_admin = not is_web and not is_api
    app.is_back = os.environ.get('CHIKI_BACK') == 'true'
    app.static_folder = app.config.get('STATIC_FOLDER')
    app.mail = Mail(app)

    def get_data_path(name):
        return os.path.abspath(
            os.path.join(app.config.get('DATA_FOLDER'), name))

    if app.config.get('USER_AGENT_LIMIT', False):
        @app.before_request
        def before_request():
            if request.path == current_app.config.get('WEROBOT_ROLE'):
                return

            ua = request.headers['User-Agent'].lower()
            if not app.debug and 'micromessenger' not in ua:
                return error_msg('请用微信客户端扫一扫')

    app.get_data_path = get_data_path

    init_babel(app)
    init_redis(app)

    if not app.config.get('CACHE_TYPE'):
        app.config['CACHE_TYPE'] = 'simple'
    cache.init_app(app)

    if app.config.get('SESSION_TYPE'):
        Session(app)

    init_jinja(app)
    init_logger(app)
    init_oauth(app)
    init_third(app)
    init_page(app)

    db.init_app(app)
    media.init_app(app)

    if app.is_admin and not manager:
        with app.app_context():
            cm.init_app(app)
            Choices.init()

    if callable(init):
        init(app)

    @app.context_processor
    def context_processor():
        return dict(Item=Item, Menu=Menu, url_for=url_for, ImageItem=ImageItem)

    if error:
        init_error_handler(app)

    if index:
        @app.route('/')
        def index():
            return redirect(app.config.get('INDEX_REDIRECT'))

    blueprint = Blueprint('chiki', __name__,
                          template_folder=os.path.join(TEMPLATE_ROOT, 'chiki'))
    app.register_blueprint(blueprint)

    if app.is_back:
        @app.route('/chiki_back')
        def chiki_back():
            return 'true'

    if app.is_admin and not manager:
        with app.app_context():
            if hasattr(app, 'user_manager'):
                user = um.models.User.objects(id=100000).first()
                if not user:
                    user = um.models.User(
                        id=100000, phone='13888888888', password='123456',
                        nickname=app.config.get('SITE_NAME'))
                    user.tid = user.create_tid()
                    user.save()
                if not user.avatar and os.path.exists(
                        app.get_data_path('imgs/logo.jpg')):
                    with open(app.get_data_path('imgs/logo.jpg')) as fd:
                        user.avatar = dict(
                            stream=StringIO(fd.read()), format='jpg')
                    user.save()

    @app.route('/1.gif')
    def gif():
        return send_file(
            DATA_ROOT + '/1.gif',
            cache_timeout=0, add_etags=False, mimetype='image/gif')

    @app.route('/test/error')
    def test_error():
        raise ValueError('testing!!!')

    @app.route('/trace/log', methods=['POST'])
    def trace_log():
        user = None
        if current_user.is_authenticated():
            user = current_user.id

        TraceLog(
            user=user,
            key=request.form.get('key', ''),
            tid=request.form.get('tid', ''),
            label=request.form.get('label', ''),
            value=request.form.get('value', ''),
        ).save()
        return json_success()

    @app.route('/complaint/choose')
    @login_required
    def complaint_choose():
        complaint = sorted(
            Complaint.TYPE.DICT.iteritems(), key=lambda x: x[1], reverse=True)
        return render_template('complaint/choose.html', type=complaint)

    @app.route('/complaint/desc/')
    @login_required
    def complaint_desc():
        types = request.args.get('type', '')
        return render_template('complaint/desc.html', types=types)

    @app.route('/complaint/refer', methods=['POST'])
    @login_required
    def complaint_refer():
        types = request.form.get('type', '')
        content = request.form.get('content', '')
        complaints = Complaint(
            user=current_user.id,
            content=content,
            type=types,
            active=True,
        )
        complaints.create()
        complaints.save()
        return json_success(msg='success', num=complaints.id)

    @app.route('/complaint/save/')
    @login_required
    def complaint_save():
        num = request.args.get('num', '')
        return render_template('complaint/refer.html', num=num)

    @app.route('/complaint/active')
    @login_required
    def complaint_active():
        complaints = Complaint.objects(user=current_user.id, active=True).first()
        if complaints:
            complaints.user.complaint = True
            complaints.user.save()
        return ''

    init_db(db)

    return app


def init_web(init=None, config=None, pyfile=None,
             template_folder='templates', index=False, error=True):
    app = init_app(init, config, pyfile, template_folder,
                   index, error, is_web=True)
    app.register_blueprint(common_bp)
    return app


def init_api(init=None, config=None, pyfile=None,
             template_folder='templates', index=False, error=False):
    app = init_app(init, config, pyfile, template_folder,
                   index, error, is_api=True)
    return app


def init_admin(init=None, config=None, pyfile=None,
               template_folder='templates', index=True,
               error=True, manager=False):
    """ 创建后台管理应用 """

    app = init_app(init, config, pyfile, template_folder, index,
                   error, manager=manager)
    app.register_blueprint(login_bp)
    app.login_manager.login_view = 'admin_users.admin_login'
    init_upimg(app)

    @app.login_manager.user_loader
    def load_user(id):
        try:
            uid, s = id.rsplit(u'|', 1)
            user = AdminUser.objects(id=uid).first()
            if user:
                key = current_app.config.get('SECRET_KEY')
                if s == sign(key, password=user.password):
                    return user
        except:
            pass

    with app.app_context():
        user = AdminUser.objects(root=True).first()
        if not user:
            AdminUser(
                username=current_app.config.get('ADMIN_USERNAME'),
                password=current_app.config.get('ADMIN_PASSWORD') or '123456',
                root=True,
            ).save()

    @app.before_request
    def _before_request():
        return before_request()

    return app


def register_app(name, config, init_app, manager=False):
    def wrapper(init):
        global apps

        class Wsgi(object):
            def __init__(self):
                self.app = None

            def __call__(self, environ, start_response):
                if not self.app:
                    self.app = init_app(
                        init=init,
                        config=config,
                        template_folder=config.TEMPLATE_FOLDER,
                    )
                return self.app(environ, start_response)

        def run():
            kwargs = dict(
                init=init,
                config=config,
                template_folder=config.TEMPLATE_FOLDER,
            )
            return init_app(**kwargs)

        apps[name] = dict(
            name=name,
            config=config,
            init=init,
            init_app=init_app,
            manager=False,
            run=run,
            wsgi=Wsgi(),
        )
        if config and hasattr(config, 'PROJECT'):
            try:
                module = __import__(config.PROJECT)
                setattr(module, 'wsgi_%s' % name, apps[name]['wsgi'])
            except Exception:
                start_error(config=config)

        if manager is True:
            def run():
                return init_app(
                    init=init,
                    config=config,
                    template_folder=config.TEMPLATE_FOLDER,
                    manager=True,
                )

            apps['manager'] = dict(
                name='manager',
                config=config,
                init=init,
                init_app=init_app,
                manager=True,
                run=run,
            )
        return init
    return wrapper


def register_admin(name='admin', config=None, manager=True):
    return register_app(name, config, init_admin, manager=manager)


def register_api(name='api', config=None):
    return register_app(name, config, init_api)


def register_web(name='web', config=None):
    return register_app(name, config, init_web)


def start_error(init=None, config=None):
    app = init_app(config=config)
    app.logger.error(traceback.format_exc())
    exit()
