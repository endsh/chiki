# coding: utf-8
import os
from StringIO import StringIO
from PIL import Image, ImageDraw, ImageFont
from flask import current_app
from .settings import FONT_ROOT


def create_avatar(name=None, width=640, bg=(51, 170, 255)):
    name = name[0] if name else u'酷'
    size = (width, width)
    img = Image.new('RGB', size, bg)
    draw = ImageDraw.Draw(img)
    font_type = current_app.config.get('FONT')
    font = ImageFont.truetype(font_type, width / 2)
    w, h = font.getsize(name)
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), name, font=font, fill=(255, 255, 255))
    stream = StringIO()
    img.save(stream, format='png')
    return dict(stream=stream, format='png')
