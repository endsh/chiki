# coding: utf-8

try:
    from simple import create_api
    app = create_api()
except Exception, e:
    from chiki import start_error    
    from simple.config import APIConfig
    start_error(config=APIConfig)