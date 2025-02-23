import multiprocessing
import os

# Get the PORT from environment variable
port = os.getenv('PORT', '8000')

# Bind to 0.0.0.0:$PORT
bind = f"0.0.0.0:{port}"

# Number of worker processes
# Using the recommended formula: CPU cores * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker type - using Gevent for async support
worker_class = "gevent"

# Maximum number of simultaneous clients
worker_connections = 1000

# Maximum requests before worker restart
max_requests = 2000
max_requests_jitter = 400

# Timeout configs
timeout = 30
keepalive = 2

# Log configs
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info" 