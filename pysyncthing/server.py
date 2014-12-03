# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/server.py: Incoming network connections.
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

from gi.repository import Gio

from pysyncthing.connection import ConnectionBase


logger = logging.getLogger(__name__)


class SyncServer(object):

    def __init__(self, engine):
        self.engine = engine
        self.pending_connections = []

    def start(self):
        self.service = Gio.SocketService.new()

        # Listen on localhost..
        address = Gio.InetSocketAddress.new(Gio.InetAddress.new_from_string("127.0.0.1"), 2200)
        self.service.add_address(address, Gio.SocketType.STREAM, Gio.SocketProtocol.TCP, self.service)

        # Setup dispatcher to deal with incoming connections
        self.service.connect("incoming", self._incoming)

    def stop(self):
        self.service.stop()

    def _incoming(self, socket_service, connection, source_object):
        # self.active_connections.append(connection)
        conn = IncomingConnection(self.engine, connection)
        self.pending_connections.append(conn)


class IncomingConnection(ConnectionBase):

    def __init__(self, engine, connection):
        super(IncomingConnection, self).__init__(engine)
        self.conn = Gio.TlsServerConnection.new(connection, engine.certificate)
        # self.conn.set_property("authentication-mode", Gio.TlsAuthenticationMode.REQUIRED)
        self.conn.connect("accept-certificate", self._accept_certificate)
        self.conn.handshake_async(0, None, self._handshake_complete)

    def _accept_certificate(self, conn, peer_cert, errors):
        logger.debug("Accepting certificate")
        return True

    def _handshake_complete(self, conn, task):
        logger.debug("Handshake complete")

        self.inp = self.conn.get_input_stream()
        self.outp = self.conn.get_output_stream()

        self.send_hello(folders=[], options={"name": self.engine.name})
        self._read_packet()

    def handle_1(self, payload):
        # FIXME: Workout name and register with engine...
        pass
