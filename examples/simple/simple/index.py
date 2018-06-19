# coding: utf-8
from flask import Blueprint

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    return 'hello chiki.'
