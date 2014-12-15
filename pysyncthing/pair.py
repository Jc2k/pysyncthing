# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/pair.py: Provides coordinaton between server and client processes. Tries to keep one connection (and one connection only) to a device id.
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

from .certs import get_fingerprint_from_device_id
from .client import ClientConnection


logger = logging.getLogger(__name__)


class Pair(object):

    def __init__(self, engine, device_id):
        self.engine = engine
        self.device_id = device_id
        self.fingerprint = get_fingerprint_from_device_id(device_id)
        self.status = "not-connected"
        self.addresses = []
        self.connection = None

    def found(self, addresses):
        if self.status == "not-connected":
            self.addresses = addresses
            self.connect()

    def incoming_connection(self, connection):
        if self.status != "not-connected":
            return False
        self.connection = connection
        self.status = "connecting"
        return True

    def connect(self):
        logger.debug("Started trying to connect")
        ip, port = self.addresses[0]
        self.status = "connecting"
        self.connection = ClientConnection(self, ip, port)

    def start(self):
        logger.debug("Starting up pair management for %s", self.device_id)
