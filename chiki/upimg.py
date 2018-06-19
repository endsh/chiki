# coding: utf-8
from flask import request
from chiki.contrib.common import ImageItem


def init_upimg(app):

    @app.route('/upimg', methods=['POST'])
    def upimg():
        proxy = request.files.get('file')
        image = ImageItem(image=proxy)
        if image.image:
            image.create()
            return image.image.link
        return ''
