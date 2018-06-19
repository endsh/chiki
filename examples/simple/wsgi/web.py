# coding: utf-8

try:
    from simple import create_web
    app = create_web()
except Exception, e:
    from chiki import start_error    
    from simple.config import WebConfig
    start_error(config=WebConfig)