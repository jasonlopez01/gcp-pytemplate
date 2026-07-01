import os

# app_config.py reads APP_CONFIG_FILE at import time; default tests to local.env
# so they don't depend on how pytest is invoked. An explicit value still wins.
os.environ.setdefault("APP_CONFIG_FILE", "local.env")
