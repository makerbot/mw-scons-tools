# Convenience wrapper for https://github.com/makerbot/mustache

import imp
import os
import sys

mustache_path = os.path.join(
    os.path.dirname(__file__), os.pardir, 'mustache', 'mustache.py'
)

# Abort initialization of this mustache module and import the real one
del sys.modules['mustache']
imp.load_source('mustache', mustache_path)
