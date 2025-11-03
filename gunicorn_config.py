"""
🚀 Gunicorn Configuration for NodeFlow Production Deployment
"""
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes - Optimized for Render free tier
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Limit workers for free tier
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increase timeout for complex routes
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "notionflow"

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in the future)
# keyfile = None
# certfile = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190