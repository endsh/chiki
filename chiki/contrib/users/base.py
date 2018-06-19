# coding: utf-8
from flask import current_app
from werkzeug.local import LocalProxy

__all__ = [
    'user_manager',
]

user_manager = LocalProxy(lambda: _get_manager())


def _get_manager():
    return current_app.user_manager
