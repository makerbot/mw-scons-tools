# Convenience wrapper for https://github.com/makerbot/mustache

import os
import sys

mustache_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'mustache')
sys.path.insert(0, mustache_dir)

# Abort initialization of this mustache module and import the real one
del sys.modules['mustache']
import mustache
