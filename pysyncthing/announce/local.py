# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/announce/local.py: Local discovery of other syncthing devices
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

import socket
import logging

from gi.repository import GLib, Gio
from construct import Container

from ..protocol import Announcement
from ..certs import get_device_id_from_fingerprint


logger = logging.getLogger(__name__)


class AnnounceLocal(object):

    def __init__(self, engine, port=21025):
        self.engine = engine
        self.address = Gio.InetSocketAddress.new_from_string("255.255.255.255", port)

    def start(self):
        self.sock = Gio.Socket.new(
            Gio.SocketFamily.IPV4,
            Gio.SocketType.DATAGRAM,
            Gio.SocketProtocol.UDP,
        )
        self.sock.broadcast = True

        self.sock.set_option(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # self.sock.set_option(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._broadcast()
        self._loop_id = GLib.timeout_add_seconds(30, self._broadcast, None)

    def _broadcast(self, *args):
        data = Announcement.build(Container(
            device=Container(
                id=self.engine.device_fingerprint,
                addresses=[
                    Container(
                        ip="",
                        port=2200,
                    ),
                ],
            ),
            devices=[],
        ))
        self.sock.send_to(self.address, data, None)


class DiscoverLocal(object):

    def __init__(self, engine, port=21025):
        self.engine = engine
        self.address = Gio.InetSocketAddress.new(
            Gio.InetAddress.new_any(Gio.SocketFamily.IPV4),
            port,
        )
        self.devices = {}

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(('', 21025))
        except socket.error:
            logger.warning("Local discovery not available")
            return
        self._channel = GLib.IOChannel.unix_new(self.sock.fileno())
        self._channel.add_watch(GLib.IO_IN, self._handle)

    def _handle_device(self, payload, socket_address):
        device_id = get_device_id_from_fingerprint(payload.id)
        addresses = []
        for address in payload.addresses:
            if address.ip == "":
                addresses.append((socket_address[0], address.port))
            else:
                addresses.append((address.ip, address.port))
        self.engine.found_device(device_id, addresses)

    def _handle(self, io, flags):
        data, address = self.sock.recvfrom(1024)
        if not len(data):
            return False
        packet = Announcement.parse(data)
        logger.debug("%s %s", packet, address)
        self._handle_device(packet.device, address)
        [self._handle_device(d, address) for d in packet.devices]
        return True
