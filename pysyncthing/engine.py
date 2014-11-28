from gi.repository import Gio, GLib
from .certs import ensure_certs, get_device_id, get_fingerprint, get_fingerprint_from_device_id
from .server import SyncServer
from .announce.local import AnnounceLocal, DiscoverLocal


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

        print self.get_device("YNOKRE2-UTJMUDT-BQXMFFC-R5OTPZY-H2LGIMO-XUME4RW-KSA3ZCF-2PVPBQI")

    def get_device(self, device_id):
        if device_id in self.devices:
            return self.devices[device_id]

        fingerprint = get_fingerprint_from_device_id(device_id)
        for agent in self.discovery:
            device = agent.lookup(fingerprint)
            if device:
                self.devices[device_id] = device
                return device

        return None

    def run(self):
        print "Starting pysyncthing"
        print "pysyncthing 0.0.0"
        print "My ID: ", self.device_id

        self.server.start()
        [d.start() for d in self.discovery]
        GLib.MainLoop().run()
