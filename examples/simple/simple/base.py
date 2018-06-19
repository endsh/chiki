# coding: utf-8
from chiki.mongoengine import MongoEngine
from chiki.contrib.users import UserManager
from chiki.api import api, wapi
from flask import Blueprint

from simple.config import BaseConfig

db = MongoEngine()
um = UserManager()
page = Blueprint('page', __name__)
