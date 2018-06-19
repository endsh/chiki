/*
 * users.js - v1.0.0 - 2016-01-10
 * home: http://www.haoku.net/
 * Copyright (c) 2016 XiaoKu Inc. All Rights Reserved.
 */

 + function ($) {

    'use strict'

    var $K = window.$K || {}

    var texts = {
        SEND_PHONE_CODE: '发送验证码',
        SEND_SUCCESS: '发送成功',
        SENDING: '正在发送...',
        ACCESSING: '正在验证...',
        SUBMITING: '正在提交...',
        NEXT: '下一步',
        REGISTER_COMPLETE: '完成注册',
        REGISTER_SUCCESS: '注册成功',
        RESET_PASSWORD_COMPLETE: '设置',
        RESET_PASSWORD_SUCCESS: '设置成功',
        UNKNOWN_ERROR: '未知错误',
        LOGINING: '正在登录...',
        LOGIN_SUCCESS: '登录成功',
        REDIRECTING: '正在跳转...'
    }

    var urls = {
        LOGIN: '/users/login',
        REGISTER_EMAIL: '/users/register/email',
        REGISTER_EMAIL_SEND: '/users/sendcode/email?action=register',
        REGISTER_PHONE: '/users/register/phone',
        REGISTER_PHONE_SEND: '/users/sendcode/phone?action=register',
        REGISTER_PHONE_ACCESS: '/users/authcode/phone?action=register',
        RESET_PASSWORD_EMAIL: '/users/reset_password/email',
        RESET_PASSWORD_EMAIL_SEND: '/users/sendcode/email?action=reset_password',
        RESET_PASSWORD_PHONE: '/users/reset_password/phone',
        RESET_PASSWORD_PHONE_SEND: '/users/sendcode/phone?action=reset_password',
        RESET_PASSWORD_PHONE_ACCESS: '/users/authcode/phone?action=reset_password',
        BIND_EMAIL: '/users/bind/email',
        BIND_EMAIL_SEND: '/users/sendcode/email?action=bind',
        BIND_EMAIL_ACCESS: '/users/authcode/email?action=bind',
        BIND_PHONE: '/users/bind/phone',
        BIND_PHONE_SEND: '/users/sendcode/phone?action=bind',
        BIND_PHONE_ACCESS: '/users/authcode/phone?action=bind',
        BIND_AUTO: '/users/bind/auto'
    }

    var onBtnSubmit = function (form, event, btn, options) {
        form.on(event, function () {
            if (options.before !== undefined) options.before()
            if (options.resetText !== undefined) btn.data('reset-text', options.resetText)
            if (options.loadingText !== undefined) btn.data('loading-text', options.loadingText)
            if (options.completeText !== undefined) btn.data('complete-text', options.completeText)
            btn.button('loading')
            if (options.check === undefined || options.check()) {
                var ajaxOptions = {
                    success: function (data) {
                        if (data.code === 0) {
                            form.off(event)
                            if (options.success !== undefined) {
                                options.success(data)
                            }
                            btn.button('complete')
                        } else {
                            $K.error(data.msg)
                            if (options.error !== undefined) {
                                options.error(data)
                            }
                            btn.button('reset')
                        }
                    },
                    error: function () {
                        $K.error(texts.UNKNOWN_ERROR)
                        if (options.error !== undefined) {
                            options.error()
                        }
                        btn.button('reset')
                    }
                }
                if (options.url !== undefined) ajaxOptions.url = options.url
                if (options.data !== undefined) ajaxOptions.data = options.data
                if (options.type !== undefined) ajaxOptions.type = options.data
                form.ajaxSubmit(ajaxOptions)
            } else {
                if (options.cancel !== undefined) {
                    options.cancel()
                }
                btn.button('reset')
            }
            return false
        })
    }

    var Resend = function (options) {
        this.options = $.extend({}, Resend.DEFAULTS, typeof options === 'object' && options)
    }

    Resend.DEFAULTS = {
        form: '.form',
        resend: '.resend',
        resendText: '重新发送',
        seconds: 60
    }

    Resend.prototype.start = function () {
        var $resend = $(this.options.resend)
        var seconds = this.options.seconds
        this.stop()
        $resend.text(this.options.resendText + ' ' + seconds)
        this.interval = setInterval($.proxy(function () {
            if (seconds === 0) {
                this.stop()
                this.click()
            } else {
                seconds -= 1
                $resend.text(this.options.resendText + ' ' + seconds)
            }
        }, this), 1000)
        $resend.show()
        $resend.addClass('disabled')
        $K.hide()
    }

    Resend.prototype.resend = function () {
        var $form = $(this.options.form)
        var $resend = $(this.options.resend)
        $resend.off('click')
        if (this.options.check === undefined || this.options.check()) {
            var options = {
                success: $.proxy(function (data) {
                    if (data.code === 0) {
                        this.start()
                    } else {
                        this.click()
                        $K.error(data.msg)
                    }
                }, this),
                error: $.proxy(function () {
                    this.click()
                    $K.error(texts.UNKNOWN_ERROR)
                })
            }
            if (this.options.url !== undefined) options.url = this.options.url
            $form.ajaxSubmit(options)
        }
    }

    Resend.prototype.stop = function () {
        var $resend = $(this.options.resend)
        if (this.interval !== undefined) {
            clearInterval(this.interval)
            this.interval = undefined
            $resend.text(this.options.resendText)
            $resend.removeClass('disabled')
            $resend.off('click')
        }
    }

    Resend.prototype.click = function () {
        var $resend = $(this.options.resend)
        $resend.on('click', $.proxy(function () {
            this.resend()
        }, this))
    }

    var Login = function (options) {
        if ($('.login-form').length === 0) return

        var form = $('.login-form')
        var account = form.find('#account')
        var password = form.find('#password')
        var code = form.find('#verify_code')
        var btn = form.find('[type="submit"]')

        options = $.extend({}, typeof options == 'object' && options)
        
        account.check({})
        password.check({strip:false})
        code.check({})

        onBtnSubmit(form, 'submit.account', btn, {
            url: urls.LOGIN,
            loadingText: texts.LOGINING,
            completeText: texts.LOGIN_SUCCESS,
            check: function () { return account.check() && password.check() && code.check() },
            success: function (data) {
                if (options.success !== undefined) {
                    options.success(data)
                } else {
                    window.location.reload()
                }
            },
            error: function (data) {
                if (data !== undefined && data.refresh === true) {
                    var src = $('.login-form #verify_code_img').data('src') + '&t=' + Math.random()
                    $('.login-form #verify_code_img').attr('src', src)
                }
            }
        })

        $K.hide()
    }

    var BindAuto = function (options) {
        if ($('.bind-auto-form').length === 0) return

        var form = $('.bind-auto-form')
        var btn = form.find('[type="submit"]')

        options = $.extend({}, typeof options == 'object' && options)

        onBtnSubmit(form, 'submit.bind.auto', btn, {
            url: urls.BIND_AUTO,
            loadingText: texts.REDIRECTING,
            completeText: texts.REDIRECTING,
            success: function (data) {
                if (options.success !== undefined) {
                    options.success(data)
                } else if (options.next !== undefined) {
                    window.location.href = options.next;
                } else {
                    window.location.reload()
                }
            }
        })

        $K.hide()
    }

    var Action = function (options) {
        this.options = $.extend({}, Action.DEFAULTS, typeof options === 'object' && options)
        this.$box = $(this.options.box)
        this.$form = this.$box.find(this.options.form)
        this.$input = this.$form.find(this.options.input)
        this.$btn = this.$form.find(this.options.btn)
        this.$verify = this.$form.find(this.options.verify)
        this.$access = this.$box.find(this.options.access)
        this.$elements = {
            send: this.$form.find(this.$form.data('send')),
            access: this.$form.find(this.$form.data('access')),
            complete: this.$form.find(this.$form.data('complete')),
            all: $.merge($.merge(this.$form.find(this.$form.data('send')), 
                this.$form.find(this.$form.data('access'))), 
                this.$form.find(this.$form.data('complete')))
        }
        this.$resend = new Resend({
            form: this.$form,
            resend: this.options.resend,
            url: this.options.urls.send,
            check: $.proxy(function () { return this.check(this.$elements.send) }, this)
        })
        this.off()
    }

    Action.DEFAULTS = {
        model: 'email',
        box: undefined,
        form: 'form',
        input: '.input',
        btn: '[type="submit"]',
        verify: '#verify_code_img',
        access: '.access',
        resend: '.resend',
        urls: {
            send: undefined,
            access: undefined,
            complete: undefined 
        },
        texts: {
            send: {
                resetText: undefined,
                loadingText: texts.SENDING,
                completeText: undefined
            },
            access: {
                resetText: undefined,
                loadingText: texts.ACCESSING,
                completeText: undefined
            },
            complete: {
                resetText: undefined,
                loadingText: texts.SUBMITING,
                completeText: undefined
            }
        },
        tmpl: undefined,
        next: '/'
    }

    Action.prototype.off = function () {
        this.$box.hide()
        this.$elements.all.hide()
        this.$form.off('submit.send').off('submit.access').off('submit.complete')
        this.$resend.stop()
        $K.hide()
    }

    Action.prototype.check = function ($elements) {
        var res = true;
        $elements.each(function () {
            if (!$(this).check()) {
                res = false;
                return false;
            }
        })
        return res;
    }

    Action.prototype.send = function () {
        this.$box.show()
        this.$elements.all.hide()
        this.$elements.send.show().check()
        this.$form.off('submit.send').off('submit.access').off('submit.complete')
        onBtnSubmit(this.$form, 'submit.send', this.$btn, {
            url: this.options.urls.send,
            resetText: this.options.texts.send.resetText,
            loadingText: this.options.texts.send.loadingText,
            completeText: this.options.texts.send.completeText,
            check: $.proxy(function () { return this.check(this.$elements.send) }, this),
            success: $.proxy(function (data) { this.access(data) }, this),
            error: $.proxy(function (data) {
                if (data !== undefined && data.refresh === true) {
                    this.$verify.attr('src', this.$verify.data('src') + '&t=' + Math.random())
                }
            }, this)
        })
        $K.hide()
    }

    Action.prototype.access = function (data) {
        this.$box.show()
        if (this.options.model === 'email') {
            this.$form.hide()
            this.$access.html('')
            $(this.options.tmpl).tmpl({
                email: this.$input.val(),
                url: data.data.email_url
            }).appendTo(this.$access)
        } else {
            this.$elements.all.hide()
            this.$elements.access.show().check()
            this.$form.off('submit.send').off('submit.access').off('submit.complete')
            onBtnSubmit(this.$form, 'submit.access', this.$btn, {
                url: this.options.urls.access,
                resetText: this.options.texts.access.resetText,
                loadingText: this.options.texts.access.loadingText,
                completeText: this.options.texts.access.completeText,
                check: $.proxy(function () { return this.check(this.$elements.access) }, this),
                success: $.proxy(function (data) { this.complete(data) }, this),
                error: $.proxy(function (data) {
                    if (data !== undefined && data.refresh === true) {
                        this.$verify.attr('src', this.$verify.data('src') + '&t=' + Math.random())
                    }
                }, this)
            })
        }
        this.$box.find(this.options.resend).show()
        this.$resend.start()
        $K.hide()
    }

    Action.prototype.complete = function () {
        this.$box.show()
        this.$box.find(this.options.resend).hide()
        this.$resend.stop()
        this.$input.attr('readonly', true)
        this.$elements.all.hide()
        this.$elements.complete.show().check()
        this.$form.off('submit.send').off('submit.access').off('submit.complete')
        onBtnSubmit(this.$form, 'submit.complete', this.$btn, {
            url: this.options.urls.complete,
            resetText: this.options.texts.complete.resetText,
            loadingText: this.options.texts.complete.loadingText,
            completeText: this.options.texts.complete.completeText,
            check: $.proxy(function () { return this.check(this.$elements.complete) }, this),
            success: $.proxy(function (data) { this.success(data) }, this)
        })
        $K.hide()
    }

    Action.prototype.success = function () {
        setTimeout($.proxy(function () {
            if (this.$form.data('next') !== undefined) {
                window.location.href = this.$form.data('next')
            } else {
                window.location.href = this.options.next
            }
        }, this), 100)
    }

    var Auth = function (options) {
        this.options = $.extend({}, Auth.DEFAULTS, typeof options === 'object' && options)
        $($.proxy(function () {
            if (this.options.email !== undefined && $(this.options.email.box).length > 0) {
                this.main = this.email = new Action(this.options.email)
                $(this.email.$box).find(this.options.usePhone).click($.proxy(function () {
                    this.email.off()
                    this.phone.off()
                    this.phone.send()
                }, this))
            }
            if (this.options.phone !== undefined && $(this.options.phone.box).length > 0) {
                this.main = this.phone = new Action(this.options.phone)
                $(this.phone.$box).find(this.options.useEmail).click($.proxy(function () {
                    this.phone.off()
                    this.email.off()
                    this.email.send()
                }, this))
            }
            if (!!this.email && !!this.phone) {
                this.main = this.options.model === 'phone' ? this.phone : this.email
            }
            if (this.options.init === true ) {
                this.init()
            }
        }, this))
    }

    Auth.DEFAULTS = {
        email: undefined,
        phone: undefined,
        useEmail: '.use-email',
        usePhone: '.use-phone',
        model: 'phone',
        action: 'send',
        init: true
    }

    Auth.prototype.init = function () {
        if (!!this.main) {
            switch (this.options.action) {
                case 'send': this.main.send(); break;
                case 'access': this.main.access(); break;
                case 'complete': this.main.complete(); break;
            }
        }
    }

    var users = {
        login: Login,
        register: new Auth({
            email: {
                model: 'email',
                box: '.register-email',
                input: '#email',
                urls: {
                    send: urls.REGISTER_EMAIL_SEND
                },
                texts: {
                    send: { resetText: '注册', loadingText: '正在发送...', completeText: '发送成功' }
                },
                tmpl: '<div><p>验证邮件已发送, 请<a href="${ url }" target="_blank">点击查收邮件</a>激活账号。</p>' +
                      '没有收到邮件？请耐心等待，或者<a class="resend" href="javascript:;">重新发送</a></div>'
            },
            phone: {
                model: 'phone',
                box: '.register-phone',
                input: '#phone',
                urls: {
                    send: urls.REGISTER_PHONE_SEND,
                    access: urls.REGISTER_PHONE_ACCESS,
                    complete: urls.REGISTER_PHONE
                },
                texts: {
                    send: { resetText: '发送验证码', loadingText: '正在发送...', completeText: '下一步' },
                    access: { resetText: '下一步', loadingText: '正在提交...', completeText: '完成注册' },
                    complete: { resetText: '完成注册', loadingText: '正在提交...', completeText: '注册成功' }
                }
            }
        }),
        registerEmailAccess: new Auth({
            email: {
                model: 'access',
                box: '.register-email-access',
                input: '#email',
                urls: {
                    complete: urls.REGISTER_EMAIL
                },
                texts: {
                    complete: { resetText: '完成注册', loadingText: '正在提交...', completeText: '注册成功' }
                }
            },
            action: 'complete'
        }),
        resetPassword: new Auth({
            email: {
                model: 'email',
                box: '.reset-password-email',
                input: '#email',
                urls: {
                    send: urls.RESET_PASSWORD_EMAIL_SEND
                },
                texts: {
                    send: { resetText: '找回密码', loadingText: '正在发送...', completeText: '发送成功' }
                },
                tmpl: '<div><p>验证邮件已发送, 请<a href="${ url }" target="_blank">点击查收邮件</a>激活账号。</p>' +
                      '没有收到邮件？请耐心等待，或者<a class="resend" href="javascript:;">重新发送</a></div>'
            },
            phone: {
                model: 'phone',
                box: '.reset-password-phone',
                input: '#phone',
                urls: {
                    send: urls.RESET_PASSWORD_PHONE_SEND,
                    access: urls.RESET_PASSWORD_PHONE_ACCESS,
                    complete: urls.RESET_PASSWORD_PHONE
                },
                texts: {
                    send: { resetText: '发送验证码', loadingText: '正在发送...', completeText: '下一步' },
                    access: { resetText: '下一步', loadingText: '正在提交...', completeText: '设置' },
                    complete: { resetText: '设置', loadingText: '正在提交...', completeText: '设置成功' }
                }
            }
        }),
        resetPasswordEmailAccess: new Auth({
            email: {
                model: 'access',
                box: '.reset-password-email-access',
                input: '#email',
                urls: {
                    complete: urls.RESET_PASSWORD_EMAIL
                },
                texts: {
                    complete: { resetText: '设置', loadingText: '正在提交...', completeText: '设置成功' }
                }
            },
            action: 'complete'
        }),
        bind: new Auth({
            email: {
                model: 'phone',
                box: '.bind-email',
                input: '#email',
                urls: {
                    send: urls.BIND_EMAIL_SEND,
                    access: urls.BIND_EMAIL_ACCESS,
                    complete: urls.BIND_EMAIL
                },
                texts: {
                    send: { resetText: '发送验证码', loadingText: '正在发送...', completeText: '下一步' },
                    access: { resetText: '下一步', loadingText: '正在提交...', completeText: '绑定' },
                    complete: { resetText: '绑定', loadingText: '正在提交...', completeText: '绑定成功' }
                }
            },
            phone: {
                model: 'phone',
                box: '.bind-phone',
                input: '#phone',
                urls: {
                    send: urls.BIND_PHONE_SEND,
                    access: urls.BIND_PHONE_ACCESS,
                    complete: urls.BIND_PHONE
                },
                texts: {
                    send: { resetText: '发送验证码', loadingText: '正在发送...', completeText: '下一步' },
                    access: { resetText: '下一步', loadingText: '正在提交...', completeText: '绑定' },
                    complete: { resetText: '绑定', loadingText: '正在提交...', completeText: '绑定成功' }
                }
            }
        }),
        bindAuto: BindAuto
    }

    $K.users = users
    window.$K = $K

    if (typeof(window.define) !== 'undefined') {
        window.define('users', ['jquery', 'cool'], function () {
            return users
        })
    } else {
        $(function () {
            users.login()
            users.bindAuto()
        })
    }

 } (jQuery)
