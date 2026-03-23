# gunicorn.conf.py — Production Gunicorn configuration for Muddo Agro

import multiprocessing, os

# Server socket
bind             = "127.0.0.1:5000"
backlog          = 2048

# Worker processes
workers          = multiprocessing.cpu_count() * 2 + 1
worker_class     = "sync"
worker_connections = 1000
timeout          = 60
keepalive        = 5
max_requests     = 1000
max_requests_jitter = 100

# Logging
accesslog        = "/var/log/muddo_agro/access.log"
errorlog         = "/var/log/muddo_agro/error.log"
loglevel         = "info"
capture_output   = True
enable_stdio_inheritance = True

# Process naming
proc_name        = "muddo_agro"

# Server hooks
def on_starting(server):
    os.makedirs("/var/log/muddo_agro", exist_ok=True)
    os.makedirs("/var/www/muddo_agro/static/uploads/products", exist_ok=True)
