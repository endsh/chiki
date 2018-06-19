# coding: utf-8
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate

sql = SQLAlchemy()
migrate = Migrate()


class SessionMixin(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def to_dict(self, *columns, **kwargs):
        dct = {}
        if not columns:
            columns = self.columns

        if kwargs.pop('skip', None) == True:
            columns = [x for x in self.columns if x not in columns]

        for col in columns:
            value = getattr(self, col)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            dct[col] = value
        return dct

    @property
    def columns(self):
        return [x.name for x in self.__table__.columns]

    def save(self):
        sql.session.add(self)
        sql.session.commit()
        return self

    def update(self, **kwargs):
        for key,value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise KeyError("Object '%s' has no field '%s'." % (type(object), key))
        sql.session.commit()
        return self

    def delete(self):
        sql.session.delete(self)
        sql.session.commit()
        return self
