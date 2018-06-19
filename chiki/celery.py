# coding: utf-8
# from chiki.base import Base
# from celery import Celery as _Celery


# class Celery(Base):

#     def __init__(self, app=None, key=None, config=None, holder=None):
#         super(Celery, self).__init__(app, key, config, holder)

#     def init_app(self, app):
#         super(Celery, self).init_app(app)
#         self.celery = _Celery(app.name, broker=self.get_config('broker'))

#     def task(self, func):
#         pass
