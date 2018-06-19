+ function ($) {

    'use strict'

    var $K = window.$K || {}

    var Check = function (element, options) {
        var check = $.proxy(this.check, this)
        var error = $.proxy(this.error, this)
        this.$element = $(element)
        this.$form = this.$element.parents('form')
        this.label = typeof options.label !== 'undefined' ? options.label : this.$element.data('label')
        if (this.$element.data('strip') === 'false') {
            options.strip = false
        }
        this.options = $.extend({}, Check.DEFAULTS, options)
        if (typeof this.options.empty === 'undefined' && this.$element.data('empty') === 'true') {
            this.options.empty = true
        }
        if (typeof this.options.min === 'undefined' && !!this.$element.data('min')) {
            this.options.min = parseInt(this.$element.data('min'), 10)
        }
        if (typeof this.options.max === 'undefined' && !!this.$element.data('max')) {
            this.options.max = parseInt(this.$element.data('max'), 10)
        }
        if (typeof this.options.equal === 'undefined' && !!this.$element.data('equal')) {
            this.options.equal = {
                element: this.$element.data('equal'),
                message: this.$element.data('equal_message')
            }
        }
        if (typeof this.options.regx === 'undefined' && !!this.$element.data('regx')) {
            this.options.regx = {
                re: this.$element.data('regx'),
                message: this.$element.data('regx_message')
            }
        }
        if (typeof options.ajax === 'undefined') {
            this.$element.on('change', check)
        } else {
            var that = this
            this.$element.on('change', function () {
                if (check() !== false) {
                    var args = {}
                    args[options.ajax.key] = that.$element.val()
                    $.get(options.ajax.url, args, function (data) {
                        if (data.code !== 0) {
                            error(data.msg)
                        } else {
                            $K.hide()
                        }
                    }, 'json')
                }
            })
        }
    }

    Check.DEFAULTS = {
        strip: true,
        empty: true
    }

    Check.prototype.check = function () {
        if (typeof this.label === 'undefined') {
            return;
        }
        if (this.options.strip) {
            this.$element.val($.trim(this.$element.val()))
        }
        var val = this.$element.val()
        if (this.options.empty) {
            if (val.length === 0) {
                return this.error(this.label + '不能为空')
            }
        }
        if (typeof this.options.min !== 'undefined') {
            if (val.length < this.options.min) {
                return this.error(this.label + '长度不能小于' + this.options.min + '个字符')
            }
        }
        if (typeof this.options.max !== 'undefined') {
            if (val.length > this.options.max) {
                return this.error(this.label + '长度不能大于' + this.options.max + '个字符')
            }
        }
        if (typeof this.options.equal == 'object') {
            if (val != $(this.options.equal.element).val()) {
                return this.error(this.options.equal.message)
            }
        }
        if (typeof this.options.regx == 'object') {
            if (!val.match(this.options.regx.re)) {
                if (this.options.regx.message) {
                    return this.error(this.options.regx.message)
                } else {
                    return this.error(this.label + '格式不正确')
                }
            }
        }
    }

    Check.prototype.error = function (message) {
        if (typeof this.options.error !== 'undefined') {
            if (typeof this.options.error === 'string') {
                $K.error(message, this.options.error)
            } else {
                this.options.error(message)
            }           
        } else {
            $K.error(message)
        }
        return false
    }

    function Plugin(option) {
        var res = true
        this.each(function () {
            var $this = $(this)
            var data = $this.data('hk.check')
            var options = $.extend({}, Check.DEFAULTS, typeof option == 'object' && option)

            if (!data) {
                $this.data('hk.check', (data = new Check(this, options)))
            } else {
                if (option === undefined && data.check() === false) {
                    res = false
                    return false
                }
            }
        })
        return res
    }

    var old = $.fn.check

    $.fn.check = Plugin
    $.fn.check.Constructor = Check

    $.fn.check.noConflict = function () {
        $.fn.check = old
        return this
    }

} (jQuery)