#coding: utf-8
from chiki.admin import ModelView
from chiki.admin.formatters import formatter_len
from flask.ext.admin import expose
from .models import WXMenu, Message
from ..utils import json_error, json_success
from flask import current_app, request
from chiki.base import db


class WXMenuView(ModelView):
    robot_filters = True
    column_list = ('name', 'second', 'url', 'make', 'sort', 'created')
    column_center_list = ('name', 'created', 'sort', 'make')
    column_searchable_list = ('name', 'url')
    column_formatters = dict(
        second=formatter_len(100),
    )

    script = """
$(function(){
    $(document).ready(function(){
        var html = '<li class="this_go" style="float:right;"><div class="btn btn-primary">更新菜单</div></li>';
        $(".nav-tabs").append(html);
        $(".this_go").click(function(){
            var result = confirm('是否更新菜单')
            if(result==true){
                $.get('/admin/wxmenu/create_menu', function(data){
                    if(data.code==0){
                        console.log('let is go!')
                    } else if(data.code==1){
                        console.log('oh, my god!')
                    }
                })
            }else{
                console.log('退出更新！')
            }
        })
    })
})
"""

    @expose('/create_menu')
    def create(self):
        wxmenus = WXMenu.objects(make=True).order_by('sort').limit(3)
        buttons = list()
        if not wxmenus:
            return json_error()
        for wxmenu in wxmenus:
            if wxmenu.second:
                button_two = dict(name=wxmenu.name)
                two_list = list()
                for second in wxmenu.second:
                    this_dict = dict(type='view', name=second.name, url=second.url)
                    two_list.append(this_dict)
                button_two['sub_button'] = two_list
                buttons.append(button_two)
            else:
                this_dict = dict(type='view', name=wxmenu.name, url=wxmenu.url)
                buttons.append(this_dict)

        current_app.wxclient.create_menu(dict(button=buttons))
        return json_success()


class MessageView(ModelView):
    robot_filters = True
    column_center_list = ('default', 'follow', 'keyword', 'type', 'enable', 'created')
    column_searchable_list = ('content',)

    script = """
$(function(){
    function change(elem){
        var $elem = $(elem),
            id = $elem.data('id'),
            name = $elem.data('name'),
            value = $elem.data('value');
        $.get("/admin/message/wxmessage", {id: id, name: name, value: value}, function(data){
            if (data.code == 0){
                $(data.name).find(".btn-default").each(function(index, e) {
                    $(e).data("value", "False")
                })
                $(data.name).find("i").removeClass("fa-check-circle text-success")
                $(data.name).find("i").addClass("fa-minus-circle text-danger")
                $elem.find("i").removeClass("fa-minus-circle text-danger")
                $elem.find("i").addClass("fa-check-circle text-success")
                console.log(data.msg)
            }else if (data.code == 1){
                console.log(data.msg)
            }else{
                console.log(data.msg)
            }
        })
    }

    $(".col-default .btn-default").click(function(){
        change(this)
    })

    $(".col-follow .btn-default").click(function() {
        change(this)
    })
})
"""

    @expose('/wxmessage')
    def wxmessage(self):
        id = request.args.get('id', None)
        name = request.args.get('name', None)
        value = request.args.get('value', None)
        if not id or not name or not value:
            return json_error(msg='未知错误')

        if name == 'default':
            if value == 'False':
                Message.objects(default=True).update(__raw__={'$set': dict(default=False)})
                message = Message.objects(id=id).get_or_404()
                message.default = True
                message.save()
                return json_success(name='.col-%s' % name, msg='完成了！')

        if name == 'follow':
            if value == 'False':
                Message.objects(follow=True).update(__raw__={'$set': dict(follow=False)})
                message = Message.objects(id=id).get_or_404()
                message.follow = True
                message.save()
                return json_success(name='.col-%s' % name, msg='完成了！')
        return json_error(msg='无动作')

    def on_model_change(self, form, model, created=False):
        if model.default and model.follow:
            Message.objects(db.Q(default=True) | db.Q(follow=True)).update(
                __raw__={'$set': dict(default=False, follow=False)}
            )
        elif model.follow:
            Message.objects(follow=True).update(__raw__={'$set': dict(follow=False)})
        else:
            Message.objects(default=True).update(__raw__={'$set': dict(default=False)})
