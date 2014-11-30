import logging

from gi.repository import Gio, GLib
from .certs import ensure_certs, get_device_id, get_fingerprint
from .server import SyncServer
from .announce.local import AnnounceLocal, DiscoverLocal


logger = logging.getLogger(__name__)


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

        pem = self.certificate.get_property("certificate-pem")
        self.device_fingerprint = get_fingerprint(pem)
        pem = self.certificate.get_property("certificate-pem")
        self.device_id = get_device_id(pem)

        self.server = SyncServer(self)

        self.discovery = [
            AnnounceLocal(self),
            DiscoverLocal(self),
        ]

    def run(self):
        logger.info("Starting pysyncthing")
        logger.info("pysyncthing 0.0.0")
        logger.info("My ID: %s", self.device_id)

        self.server.start()
        [d.start() for d in self.discovery]
        GLib.MainLoop().run()
