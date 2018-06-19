# coding: utf-8
from chiki import init_admin, init_api, init_web
from simple import admin, api, web
from simple.config import AdminConfig, APIConfig, WebConfig


def create_admin(pyfile=None):
    return init_admin(admin.init, AdminConfig, pyfile=pyfile,
        template_folder=AdminConfig.TEMPLATE_FOLDER)


def create_api(pyfile=None):
    return init_api(api.init, APIConfig, pyfile=pyfile,
        template_folder=APIConfig.TEMPLATE_FOLDER)


def create_web(pyfile=None):
    return init_web(web.init, WebConfig, pyfile=pyfile,
        template_folder=WebConfig.TEMPLATE_FOLDER)