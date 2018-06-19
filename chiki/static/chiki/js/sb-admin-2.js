$(function() {

    $('#side-menu').metisMenu();

});

function setCookie(name, value, expired) {
    var date = new Date();
    date.setTime(date.getTime() + expired * 1000);
    document.cookie = name + "=" + value + "; " + expired + "; path=/";
}

function getCookie(name) {
    var prefix = name + "=",
        cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; ++i) {
        var cookie = cookies[i].trim();
        if (cookie.indexOf(prefix) == 0) {
            return cookie.substring(prefix.length, cookie.length);
        }
    }
    return ""
}

function toggleBar(sm) {
    if (sm) {
        $('.wrapper').removeClass('sm');
        $('.side-toggle li a').html('<i class="glyphicon glyphicon-chevron-left"></i>');
        setCookie('sidebar.sm', 'false', 30 * 86400);
    } else {
        $('.wrapper').addClass('sm');
        $('.side-toggle li a').html('<i class="glyphicon glyphicon-chevron-right"></i>');
        setCookie('sidebar.sm', 'true', 30 * 86400);
    }
}

//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
// Sets the min-height of #page-wrapper to window size
$(function() {
    $(window).bind("load resize", function() {
        topOffset = 50;
        width = (this.window.innerWidth > 0) ? this.window.innerWidth : this.screen.width;
        if (width < 768) {
            $('div.navbar-collapse').addClass('collapse');
            topOffset = 100; // 2-row-menu
        } else {
            $('div.navbar-collapse').removeClass('collapse');
        }

        height = ((this.window.innerHeight > 0) ? this.window.innerHeight : this.screen.height) - 1;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $("#page-wrapper").css("min-height", (height) + "px");
        }

        setTimeout(function () {
            $('.nicescroll').getNiceScroll().resize();
        }, 500);
    });

    var url = window.location;
    var element = $('ul.nav a').filter(function() {
        return this.href == url || url.href.indexOf(this.href) == 0;
    }).addClass('active').parent().parent().addClass('in').parent();
    if (element.is('li')) {
        element.addClass('active');
    }

    $('.nicescroll').niceScroll({
        cursorcolor: "rgba(0, 0, 0, 0.5)",
        cursoropacitymax: 1,
        touchbehavior: false,
        cursorwidth: "5px",
        cursorborder: "0",
        cursorborderradius: "4px"
    });

    $('.sidebar li a').click(function () {
        setTimeout(function () {
            $('.nicescroll').getNiceScroll().resize();
        }, 500);
    });

    $('.side-toggle li a').click(function () {
        toggleBar($('.wrapper').hasClass('sm'));
    });

    $(".search-input").focus(function(){
        $(".search-input").animate({width:'250px'}, 200);
    });
    $(".search-input").blur(function(){
        $(".search-input").animate({width:'197px'}, 200);
    });
});