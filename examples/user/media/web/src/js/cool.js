
+ function ($) {

    "use strict"

    var $K = {
        timeout: null,
        message: function (type, text, selector, close) {
            var tmpl = '<div><div class="alert alert-' + type + '">'
            if (close !== false) {
                tmpl += '<button class="close" type="button" data-dismiss="alert"><span aria-hidden="true">&times;</span></button>'
            }
            tmpl += '<span>${ text }</span></div></div>'
            if (typeof selector === 'undefined') {
                selector = '.message'
            }
            $(selector).html($(tmpl).tmpl({ text: text }))
            this.timeout = setTimeout(function () {
                $K.hide(selector)
            }, 3000)
        },

        success: function (text, selector, close) {
            return this.message('success', text, selector, close)
        },

        error: function (text, selector, close) {
            return this.message('danger', text, selector, close)
        },

        hide: function (selector) {
            if (typeof selector === 'undefined') {
                $('.message').html('')
            } else {
                $(selector).html('')
            }
            if (this.timeout != null) {
                clearTimeout(this.timeout)
                this.timeout = null
            }
        }
    }

    window.$K = $K

} (jQuery)
