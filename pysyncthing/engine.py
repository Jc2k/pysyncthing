# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/engine.py: Main management for device to device comms
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see <http://www.gnu.org/licenses/>.

import logging

from gi.repository import Gio, GLib
from .certs import ensure_certs, get_device_id, get_fingerprint, get_fingerprint_from_device_id
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
        logger.info("Starting pysyncthing")
        logger.info("pysyncthing 0.0.0")
        logger.info("My ID: %s", self.device_id)

        self.server.start()
        [d.start() for d in self.discovery]
        GLib.MainLoop().run()
