# coding: utf-8
from chiki import MediaManager, init_uploads
from simple import index, articles
from simple.base import db, um, wapi

media = MediaManager(
    css=['css/web.min.css'],
    cssx=[
        'libs/bootstrap/css/bootstrap.css',
        'dist/css/web.css'
    ],
    js=['js/web.min.js'],
    jsx=[
        'bower_components/jquery/dist/jquery.js',
        'bower_components/jquery-form/jquery.form.js',
        'bower_components/jquery-tmpl/jquery.tmpl.js',
        'libs/bootstrap/js/bootstrap.js',
        'libs/area.js',
        'dist/js/web.js'
    ],
)


def init_routes(app):
    app.register_blueprint(index.bp)
    app.register_blueprint(articles.bp, url_prefix='/articles')


def init_um(app):
    um.init_app(app)
    um.init_wapis(wapi)
    um.init_web()


def init(app):
    db.init_app(app)
    media.init_app(app)
    wapi.init_app(app)

    init_um(app)
    init_routes(app)
    init_uploads(app)
