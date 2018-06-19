.. _oauth:

第三方接口
==========

微信网页授权
------------

代码位置：chiki/oauth/wxauth.py
微信文档：https://mp.weixin.qq.com/wiki?t=resource/res_main&id=mp1421140842

网页授权流程分为四步：

    * 引导用户进入授权页面同意授权，获取code
    * 通过code换取网页授权access_token（与基础支持中的access_token不同） 
    * 如果需要，开发者可以刷新网页授权access_token，避免过期 
    * 通过网页授权access_token和openid获取用户基本信息（支持UnionID机制）

框架实现：
    
    * 重定向取授权：

框架用法：

微信登录有三种方式：公众号授权登录(mp)、扫码登录(qrcode)、手机登录(mobile)，
只需相应加上配置，就支持相应的方式::

    WXAUTH = dict(
        mp=dict(
            appid='wx5d4a******b12c76',
            secret='bc1cdd******fd1496f1a8ae751f965b',
        ),
        mobile=dict(appid='', secret=''),
        qrcode=dict(appid='', secret=''),
    )

加上配置后，`app.wxauth` 就可以直接使用，可以在需要的地方调用
 :meth:`~chiki.oauth.wxauth.WXAuth.auth` 发起微信授权登录::

    @bp.route('/mp-login.html')
    def mp_login():
        """ 重定向去公众号登录 """
        return current_app.wxauth.auth(wxauth.ACTION_MP, next)

    @bp.route('/qrcode-login.html')
    def qrcode_login():
        """ 重定向去扫二维码登录 """
        return current_app.wxauth.auth(wxauth.ACTION_QRCODE, next)

授权后，`app.wxauth` 有两个授权结果回调函数，分别是
:meth:`~chiki.oauth.wxauth.WXAuth.success_handler` 与
:meth:`~chiki.oauth.wxauth.WXAuth.error_handler`::

    @app.wxauth.success_handler
    def wxauth_success(action, scope, access, next):
        """
            :param action: mp|qrcode|mobile
            :param scope: snsapi_base|snsapi_userinfo
            :param access: 微信授权成功返回的信息
            :param next: 下一步的链接
            :rtype: None或自定义Response
        """

    @app.wxauth.error_handler
    def wxauth_error(err, action, next):
        """
            :param err: 错误吗
            :param action: mp|qrcode|mobile
            :param next: 下一步的链接
            :rtype: None或自定义Response
        """





微信JSSDK
---------
只要启用微信登录(即加了WXAUTH的配置)，JSSDK也会相应的支持。JSSDK用法比较简单，
主要封装了接口签名配置::

    <!-- 只需要在需要的页面加上 -->
    <script type="text/javascript" 
        src="http://res.wx.qq.com/open/js/jweixin-1.0.0.js">
    <script type="text/javascript" src="/weixin-config.js">

    <!-- 支持调试 -->
    <script type="text/javascript" src="/weixin-config.js?debug=true">

.. admonition:: 注意

    微信JSSDK需要在微信公众号中配置JS接口安全域名：公众号设置->功能设置。

微信支付
--------
微信支付目前只封装了公众号支付的相关功能：支付、发红包、退款、查询退款。
微信支付的配置(WXPAY)，加上即启用::

    WXPAY = dict(
        appid='wx5d4a******b12c76',              # APPID
        mchid='13******01',                      # 商户号
        key='206ef4acf8c2******b43480712cc762',  # 支付key，对应在商户平台设置
        send_name='月光宝石',                     # 发红包的名字(发红包才需要)
        client_ip='127.0.0.1',                   # 服务器的公网IP(发红包才需要)
        cert=(                                   # 发红包、退款用到的密钥
            os.path.join(ETC_FOLDER, 'cert/apiclient_cert.pem'),
            os.path.join(ETC_FOLDER, 'cert/apiclient_key.pem'),
        )
    )

加上配置后，即可使用 `app.wxpay`。微信支付一般流程是:
    - 创建自己的订单
    - prepay创建预付订单
    - JS调起微信支付
    - 支付结果回调

prepay创建预付订单::

    @bp.route('/shop/order/<id>/pay', methods=['POST'])
    @login_required
    def order_pay(id):
        # 创建订单
        order = GoodOrder.objects(id=id, user=current_user.id).first()

        if not order.prepay:
            openid = current_user.wechat_user.mp_openid
            # prepay预支付
            res = current_app.wxpay.prepay(
                body='商品订单: %s' % order.id,
                detail='共 %d 件商品' % order.goods_count,
                out_trade_no=str(order.id),
                total_fee=str(order.price),
                openid=openid,
                type='shop', # 支持订单分类
            )
            if res.get('return_code') != 'SUCCESS' \
                    or res.get('result_code') != 'SUCCESS':
                # 预支付失败
                return json_error(msg='微信支付失败：%s' % res.get('return_msg'))
            else:
                order.prepay = res.get('prepay_id')
                order.modified = datetime.now()
                order.save()

        # 发起JS支付所需要的配置
        conf = current_app.wxpay.get_conf(order.prepay)
        return render_template('home/shop/pay.html', order=order, conf=conf)

JS调起微信支付::

    <script type="text/javascript">
    $(function () {
        function onBridgeReady(){
            WeixinJSBridge.invoke(
                'getBrandWCPayRequest', {{ conf | safe }},
                function (res) {
                    if (res.err_msg == "get_brand_wcpay_request:ok" ) {
                        alert('success')
                    } else {
                        alert('error')
                    }
                }
            )
        }
    })
    </script>

微信支付结果回调::

    def wxpay_vip(res):
        order = VipOrder.objects(id=res.get('out_trade_no')).first()
        if order:
            if res.get('result_code') == 'SUCCESS' \
                    and res.get('return_code') == 'SUCCESS':
                # 支付成功
                if order.payment != order.PAYMENT_DONE:
                    order.payment = order.PAYMENT_DONE
                    order.modified = datetime.now()
                    order.save()

    @wxpay.wxpay_handler
    def wxpay_handler(res, type):
        res['type'] = type
        if type == 'vip':
            wxpay_vip(res)

下面给出发红包
:meth:`~chiki.oauth.wxpay.WXPay.send_red_pack`
、退款 :meth:`~chiki.oauth.wxpay.WXPay.refund` 
及退款查询 :meth:`~chiki.oauth.wxpay.WXPay.refund_query`
的例子(具体参数请看微信支付相应的接口文档)::

    # 发红包
    res = current_app.wxpay.send_red_pack(
        mch_billno=billno,
        re_openid=current_user.wechat_user.mp_openid,
        total_amount=money,
        total_num=1,
        wishing='感谢使用月光宝石！',
        act_name='宝石提现',
        remark='月光宝石，优惠多多！',
    )
    if res.get('return_code') == 'SUCCESS' \
            and res.get('result_code') == 'SUCCESS':
        # 发红包成功

    # 退款
    res = current_app.wxpay.refund(
        out_trade_no=order.id,
        out_refund_no=log.id,
        total_fee=order.price,
        refund_fee=price,
    )
    if res.get('return_code') != 'SUCCESS' \
            or res.get('result_code') != 'SUCCESS':
        # 申请退款成功

    # 查询退款
    res = current_app.wxpay.refund_query(out_trade_no=id)

.. admonition:: 注意

    微信支付需要在微信公众号中配置支付授权目录：微信支付->开发配置。另外，
    密钥需要手动上传到相应目录，配置中的key需要自己随机生成，并到商户平台
    进行设置。


WeRobot支持
-----------
主要封装了模板消息的功能::

    from chiki import tpl_data

    # tpl_data 生成带颜色的字段，具体看微信文档

    def send_flow_msg(first, order, status):
        tpl = '流量模板ID'
        openid = order.user.wechat_user.mp_openid
        client = current_app.wxclient
        kefu = '13798195099'
        data = tpl_data(
            first=first,
            keyword1=order.phone,
            keyword2=order.flow.name,
            keyword3=status,
            keyword4=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            remark='谢谢你的充值，如有疑问，请联系客服：%s' % kefu,
        )
        url = url_for('home.profile', _external=True)
        client.send_tpl(openid, tpl, data=data, url=url)

werobot 一般需要配置::

    WEROBOT_TOKEN = 'wechat'
    WEROBOT_ROLE = '/wechat'

.. admonition:: 注意

    Werobot需要在微信公众号中配置接口，开启开发模式：基本配置->服务器配置。

QQ/微博登录
------------
暂不支持。
