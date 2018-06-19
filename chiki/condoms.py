# coding: utf-8


class Condom(object):

    def heart(self, key):
        pass

    def __call__(self, key):
        def desc(func):
            def wrapper(*args, **kwarg):
                return func(*args, **kwarg)
            return wrapper
        return desc

condom = Condom()
