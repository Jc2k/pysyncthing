# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/client.py: Connection handling code for client connections
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

from gi.repository import Gio
# from construct import Container
from .protocol import packet
from .connection import ConnectionBase


class ClientConnection(ConnectionBase):

    def __init__(self, engine, hostname, port):
        super(ClientConnection, self).__init__(engine)

        client = Gio.SocketClient()
        connection = client.connect_to_host(hostname, port, None)

        self.conn = Gio.TlsClientConnection.new(connection, None)
        self.conn.set_certificate(self.engine.certificate)
        self.conn.connect("accept-certificate", self._accept_certificate)

        self.inp = self.conn.get_input_stream()
        self.outp = self.conn.get_output_stream()
        self._read_packet()

    def _accept_certificate(self, connection, cert, flags):
        return True

    def handle_0(self, payload):
        self.send_hello()

    def handle_1(self, payload):
        self.send_message(
            1,
            folder="default",
            files=[],
        )
        return
        for file in payload.payload.files:
            offset = 0
            for block in file.blocks:
                self.send_message(
                    2,
                    folder=payload.payload.folder,
                    name=file.name,
                    offset=offset,
                    size=block.size,
                )
                # FIXME: Verify hash
                offset += block.size

    def handle_4(self, payload):
        self.send_message(5, id=payload.header.message_id)
