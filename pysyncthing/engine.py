from gi.repository import Gio, GLib
from .certs import ensure_certs
from .server import SyncServer


class Engine(object):

    CLIENT_NAME = "pysyncthing"
    CLIENT_VERSION = "v0.0.0"

    def __init__(self, name):
        self.name = name
        self.folders = []
        self.devices = {}

        # FIXME: Generate and store certs in GNOME-keyring
        ensure_certs()
        self.certificate = Gio.TlsCertificate.new_from_files("client.crt", "client.key")

        self.server = SyncServer(self)

    def run(self):
        self.server.start()
        GLib.MainLoop().run()