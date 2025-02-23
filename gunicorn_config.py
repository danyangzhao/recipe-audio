import os

# Get the PORT from environment variable
port = os.getenv('PORT', '8000')

# Bind to 0.0.0.0:$PORT
bind = f"0.0.0.0:{port}"

# Absolute minimum configuration for Basic dyno (512MB)
workers = 1  # Single worker only
threads = 2  # Minimal threads
worker_class = "gthread"  # Thread-based worker for memory efficiency

# Increase timeout but keep it reasonable for Basic dyno
timeout = 60  # Reduced from 120 to be more memory efficient
keepalive = 2

# Aggressive memory management
max_requests = 25  # Restart worker more frequently
max_requests_jitter = 5
worker_tmp_dir = "/dev/shm"
preload_app = True

# Log configs
accesslog = "-"
errorlog = "-"
loglevel = "warning"  # Reduce logging to save memory 