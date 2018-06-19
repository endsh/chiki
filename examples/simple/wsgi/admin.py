# coding: utf-8

try:
    from simple import create_admin
    app = create_admin()
except Exception, e:
    from chiki import start_error    
    from simple.config import AdminConfig
    start_error(config=AdminConfig)
