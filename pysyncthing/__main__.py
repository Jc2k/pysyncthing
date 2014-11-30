try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass

import logging

from .engine import Engine

logging.basicConfig(level=logging.DEBUG)
Engine("example").run()
