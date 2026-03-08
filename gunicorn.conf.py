# Gunicorn configuration for Bizify production deployment

bind = "0.0.0.0:8000"
workers = 2          # Adjusted based on load (typically 2 * num_cores + 1)
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
keepalive = 5

# Logging
accesslog = "-"      # Log to stdout
errorlog = "-"       # Log to stderr
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
