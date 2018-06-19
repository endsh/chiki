# coding: utf-8
from flask import url_for
from wtforms.widgets import html_params, HTMLString, TextArea, Input
from wtforms.compat import text_type
from cgi import escape

__all__ = [
    'VerifyCode', 'UEditor', 'KListWidget', 'FileInput',
    'ImageInput', 'AreaInput', 'WangEditor', 'DragInput',
    'Base64ImageInput',
]


class VerifyCode(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        if field.hidden:
            html = '<input %s>' % self.html_params(
                id=field.id,
                type='hidden',
                name=field.name,
                value=field._value(),
            )
        else:
            html = '<div class="input-group">'
            html += '<input %s>' % self.html_params(
                id=field.id,
                type='text',
                name=field.name,
                value=field._value(),
                maxlength=field.code_len,
                **kwargs
            )
            html += '<span class="input-group-addon" style=padding:0;"><img %s><span>' % self.html_params(
                id='%s_img' % field.id,
                src=url_for('verify_code', key=field.key),
                data_src=url_for('verify_code', key=field.key),
                style="cursor:pointer",
                onclick="$(this).attr('src', '" + url_for('verify_code', key=field.key) + "&t=' + Math.random());",
            )
            html += '</div>'
        return HTMLString(html)


class UEditor(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'text/plain')
        kwargs.setdefault('style', 'margin-right:-10px;height:360px;')
        kwargs['class'] = ''
        return HTMLString(
            '<script %s>%s</script><script>var ue = UE.getEditor("%s");</script>' % (
                self.html_params(name=field.name, **kwargs),
                text_type(field._value()),
                field.name,
            )
        )


class MDEditor(object):

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        return HTMLString(
            '<script %s>%s</script><script>var um = UM.getEditor("%s");</script>' % (
                self.html_params(name=field.name, **kwargs),
                text_type(field._value()),
                field.name,
            )
        )


class KListWidget(object):

    def __init__(self, html_tag='ul', sub_tag='li', sub_startswith='sub_', prefix_label=True):
        self.html_tag = html_tag
        self.sub_tag = sub_tag
        self.sub_startswith = sub_startswith
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        sub_kwargs = dict((k[4:], v) for k, v in kwargs.iteritems() if k.startswith(self.sub_startswith))
        kwargs = dict(filter(lambda x: not x[0].startswith(self.sub_startswith), kwargs.iteritems()))
        sub_html = '%s %s' % (self.sub_tag, html_params(**sub_kwargs))
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<%s>%s %s</%s>' % (sub_html, subfield.label, subfield(), self.sub_tag))
            else:
                html.append('<%s>%s %s</%s>' % (sub_html, subfield(), subfield.label, self.sub_tag))
        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))


class DragInput(Input):
    input_type = 'checkbox'

    def __call__(self, field, **kwargs):
        if getattr(field, 'checked', field.data):
            kwargs['checked'] = True
        return super(DragInput, self).__call__(field, **kwargs)


class DragSelectWidget(object):

    def __init__(self, html_tag='div', sub_tag='div', sub_startswith='sub_'):
        self.html_tag = html_tag
        self.sub_tag = sub_tag
        self.sub_startswith = sub_startswith

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        sub_kwargs = dict((k[4:], v) for k, v in kwargs.iteritems() if k.startswith(self.sub_startswith))
        kwargs = dict(filter(lambda x: not x[0].startswith(self.sub_startswith), kwargs.iteritems()))
        sub_html = '%s %s' % (self.sub_tag, html_params(**sub_kwargs))
        left = ['<%s %s>' % (self.html_tag, html_params(id='%s-left' % field.id, class_='drag-left drag-part'))]
        right = ['<%s %s>' % (self.html_tag, html_params(id='%s-right' % field.id, class_='drag-right drag-part'))]
        for subfield in field:
            if subfield.checked:
                right.append('<%s>%s %s</%s>' % (sub_html, subfield.label, subfield(), self.sub_tag))
            else:
                left.append('<%s>%s %s</%s>' % (sub_html, subfield(), subfield.label, self.sub_tag))
        left.append('</%s>' % self.html_tag)
        right.append('</%s>' % self.html_tag)
        html = """<div class="drag-select">%s%s</div><script type="text/javascript">
            $(function() {

                function initClick(id) {
                    $('#' + id + '-left > div, #' + id + 'right > div').click(function () {})
                    $('#' + id + '-left > div').unbind('click').click(function () {
                        $(this).find('input[type="checkbox"]').get(0).checked = true;
                        $('#' + id + '-right').append($(this).clone())
                        $(this).remove()
                        initClick(id);
                    })
                    $('#' + id + '-right > div').unbind('click').click(function () {
                        $(this).find('input[type="checkbox"]').removeAttr('checked');
                        $('#' + id + '-left').append($(this).clone())
                        $(this).remove()
                        initClick(id);
                    })
                }

                function init(id) {
                    dragula([document.getElementById(id + '-left'), document.getElementById(id + '-right')])
                        .on('drop', function (el, target) {
                            if (target === document.getElementById(id + '-left')) {
                                $(el).find('input[type="checkbox"]').removeAttr('checked');
                            } else {
                                $(el).find('input[type="checkbox"]').get(0).checked = true;
                            }
                            initClick(id)
                        })
                    initClick(id);
                }
                init('%s')
            });
        </script>""" % (''.join(left), ''.join(right), field.id)
        return HTMLString(html)


class FileInput(object):

    template = """
        <div class="input-group">
            <span class="input-group-btn">
                <div id="btn-image" autocomplete="off" class="btn btn-default" style="width:80px;padding:0;">
                    <span style="padding: 6px 12px;display:inline-block;">选择文件</span>
                    %(input)s
                </div>
            </span>
            <input autocomplete="off" type="text" class="col-sm-5 form-control input-insert-image"
                placeholder='%(place)s' disabled="disabled" />
        </div>
        <div class="clearfix"></div>
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.pop('class', None)
        kwargs.setdefault('autocomplete', 'off')
        kwargs.setdefault('style', 'width:100%;height:34px;margin-top:-34px;opacity:0;cursor:pointer;')
        kwargs.setdefault('onchange', "$(this).parents('.input-group').find('.input-insert-image').val($(this).val())")
        input = '<input %s>' % html_params(name=field.name, type='file', **kwargs)
        html = self.template % dict(place=field.place or field.label.text, input=input)
        return HTMLString(html)


class ImageInput(object):

    template = """
        <a href="%(thumb)s" target="_blank">
            <div class="image-thumbnail">
                <img src="%(thumb)s">
            </div>
        </a>
        <div class="checkbox" style="margin-bottom:10px;">
            <label>
                <input name="%(name)s-delete" type="checkbox" value="true"> 删除 %(filename)s
            </label>
        </div>
    """

    input_tpl = """
        <div class="input-group">
            <span class="input-group-btn">
                <div id="btn-image" autocomplete="off" class="btn btn-default" style="width:80px;padding:0;">
                    <span style="padding: 6px 12px;display:inline-block;">选择图片</span>
                    %(input)s
                </div>
            </span>
            <input autocomplete="off" type="text" class="col-sm-5 form-control input-insert-image"
                placeholder='%(place)s' disabled="disabled" />
        </div>
        <div class="clearfix"></div>
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.pop('class', None)
        kwargs.setdefault('autocomplete', 'off')
        kwargs.setdefault('style', 'width:100%;height:34px;margin-top:-34px;opacity:0;cursor:pointer;')
        kwargs.setdefault('onchange', "$(this).parents('.input-group').find('.input-insert-image').val($(this).val())")

        input = '<input %s>' % html_params(name=field.name, type='file', **kwargs)
        html = self.input_tpl % dict(place=field.place or field.label.text, input=input)
        if field.data and hasattr(field.data, 'link') and field.data.link:
            html = self.template % dict(
                thumb=field.data.link,
                name=field.name,
                filename=field.data.filename,
            ) + html

        return HTMLString(html)


class Base64ImageInput(object):

    template = """
        <a href="%(thumb)s" target="_blank">
            <div class="image-thumbnail">
                <img src="%(thumb)s">
            </div>
        </a>
        <div class="checkbox" style="margin-bottom:10px;">
            <label>
                <input name="%(name)s-delete" type="checkbox" value="true"> 删除
            </label>
        </div>
    """

    input_tpl = """
        <div class="input-group">
            <span class="input-group-btn">
                <div id="btn-image" autocomplete="off" class="btn btn-default" style="width:80px;padding:0;">
                    <span style="padding: 6px 12px;display:inline-block;">选择图片</span>
                    %(input)s
                </div>
            </span>
            <input autocomplete="off" type="text" class="col-sm-5 form-control input-insert-image"
                placeholder='%(place)s' disabled="disabled" />
        </div>
        <div class="clearfix"></div>
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.pop('class', None)
        kwargs.setdefault('autocomplete', 'off')
        kwargs.setdefault('style', 'width:100%;height:34px;margin-top:-34px;opacity:0;cursor:pointer;')
        kwargs.setdefault('onchange', "$(this).parents('.input-group').find('.input-insert-image').val($(this).val())")

        input = '<input %s>' % html_params(name=field.name, type='file', **kwargs)
        html = self.input_tpl % dict(place=field.place or field.label.text, input=input)
        if field.data and hasattr(field.data, 'link') and field.data.link:
            html = self.template % dict(
                thumb=field.data.link,
                name=field.name,
            ) + html

        return HTMLString(html)


class AreaInput(object):

    template = (
        '<div %s><div class="col-xs-4" style="padding: 0 8px 0 0;"><select %s></select></div>'
        '<div class="col-xs-4" style="padding: 0 8px"><select %s></select></div>'
        '<div class="col-xs-4" style="padding: 0 0 0 8px;"><select %s></select></div>'
        '<script type="text/javascript">area.init("%s", "%s", "%s", "%s")</script>'
        '<div class="clearfix"></div></div>'
    )

    def __call__(self, field, **kwargs):
        datas = (field.data or '').split('|')
        if len(datas) == 3:
            province, city, county = datas
        else:
            province, city, county = '', '', ''
        province_name = '%s_province' % field.name
        city_name = '%s_city' % field.name
        county_name = '%s_county' % field.name
        return HTMLString(self.template % (
            html_params(id=field.name),
            html_params(id=province_name, name=province_name, **kwargs),
            html_params(id=city_name, name=city_name, **kwargs),
            html_params(id=county_name, name=county_name, **kwargs),
            field.name, province, city, county,
        ))


class WangEditor(TextArea):

    def __call__(self, field, **kwargs):
        kwargs.setdefault('style', 'height:480px;')
        script = """<script type="text/javascript">
            $(function() {
                var clone = $('#uploadContainer').clone();
                initUploader(clone);
                var editor = $('#%s').wangEditor({
                    uploadImgComponent: clone,
                });
                clone.WEditor = editor;
            });
        </script>""" % field.name
        return super(WangEditor, self).__call__(field, **kwargs) + script
