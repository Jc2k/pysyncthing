try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass

from .engine import Engine

Engine("example").run()
