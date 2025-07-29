"""
Gunicorn configuration for production deployment
"""
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Application
wsgi_app = "main:app"

# Logging
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "ape_pumps"

# Preload application for better performance
preload_app = True

# Enable auto-restart when code changes (disable in production)
reload = os.environ.get('FLASK_ENV', 'production') == 'development'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190