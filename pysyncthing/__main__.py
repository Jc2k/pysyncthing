from .connection import ClientConnection
from .certs import ensure_certs

ensure_certs()
c = ClientConnection("localhost", 22000)
c.handle()
