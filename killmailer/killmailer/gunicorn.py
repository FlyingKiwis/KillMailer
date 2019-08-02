import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

bind='unix:{}'.format(os.path.join(BASE_DIR, 'run', 'gunicorn.sock'))
pid=os.path.join(BASE_DIR, 'run', 'gunicorn.pid')
backlog = 2048

workers = 3
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

spew = False

group= 'www-data'

errorlog = os.path.join(BASE_DIR, 'log', 'gunicorn-error.log')
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'