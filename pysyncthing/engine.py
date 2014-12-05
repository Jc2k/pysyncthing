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

import os
import json
import logging

from gi.repository import Gio, GLib
from .certs import ensure_certs, get_device_id, get_fingerprint
from .server import SyncServer
from .announce.local import AnnounceLocal, DiscoverLocal
from .pair import Pair


logger = logging.getLogger(__name__)


class Engine(object):

    CLIENT_NAME = "pysyncthing"
    CLIENT_VERSION = "v0.0.0"

    def __init__(self, name):
        self.name = name

        conf = {}
        conf_dir = os.path.join(GLib.get_user_config_dir(), "pysyncthing")
        conf_path = os.path.join(conf_dir, "conf.json")

        logger.debug("Looking for config in %s", conf_path)
        if os.path.exists(conf_path):
            with open(conf_path) as fp:
                conf = json.load(fp)

        self.folders = []

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

        self.devices = {}
        for device in conf.get("devices", []):
             self.add_pair(device["id"])

    def add_pair(self, device_id):
        self.devices[device_id] = Pair(self, device_id)

    def found_device(self, device_id, addresses):
        if device_id == self.device_id:
            return
        logger.debug("Found addresses %s for device %s", addresses, device_id)
        if device_id not in self.devices:
            return
        self.devices[device_id].found(addresses)

    def incoming_connection(self, device_id, connection):
        if device_id not in self.devices:
            logger.debug("Unexpected connection from %s", device_id)
            return False
        return self.devices[device_id].incoming_connection(connection)

    def run(self):
        logger.info("Starting pysyncthing")
        logger.info("pysyncthing 0.0.0")
        logger.info("My ID: %s", self.device_id)

        self.server.start()
        [p.start() for p in self.devices.values()]
        [d.start() for d in self.discovery]

        GLib.MainLoop().run()
