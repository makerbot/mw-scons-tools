# Convenience wrapper for https://github.com/makerbot/mustache

import os
import sys

# append the sibling dir of mustache but we will prefer the installed version

mustache_sibling_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'mustache')
sys.path.insert(0, mustache_sibling_dir)
mustache_install_dir = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, mustache_install_dir)

# Abort initialization of this mustache module and import the real one
del sys.modules['mustache']
import mustache
