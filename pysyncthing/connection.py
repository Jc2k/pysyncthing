# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/connection.py: Connection related code that is shared between clients and servers.
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

from construct import Container
from .protocol import packet, packet_stream


logger = logging.getLogger(__name__)


class ConnectionBase(object):

    def __init__(self, pair):
        self.local_message_id = 0
        self.pair = pair
        self.engine = pair.engine
        self._read_buffer = ""

    def send_message(self, type, id=None, **kwargs):
        data = packet.build(Container(
            header=Container(
                message_version=0,
                message_id=id or self.local_message_id,
                message_type=type,
                compressed=False,
            ),
            payload=Container(**kwargs),
        ))
        logger.debug("SEND: %s", packet.parse(data))
        self.outp.write(data)
        self.local_message_id += 1

    def send_hello(self, **kwargs):
        fs = []
        for folder in self.engine.folders:
            ds = []
            for device in folder.devices:
                ds.append(Container(
                    id=device.fingerprint,
                    flags=Container(
                        priority=0,
                        introducer=False,
                        read_only=False,
                        trusted=True,
                    )
                    max_local_version=0,
                ))

            fs.append(Container(
                name=folder.name,
                devices=ds,
            ))

        options = {"name": self.engine.name}
        options.update(kwargs)

        self.send_message(
            0,
            client_name=self.engine.CLIENT_NAME,
            client_version=self.engine.CLIENT_VERSION,
            folders=fs,
            options=options,
        )

    def close(self):
        self.conn.close()
        self.pair.status = "not-connected"
        self.pair.connection = None

    def handle_1(self, packet):
        """ Remote sent us folder structure """

    def handle_2(self, packet):
        """ Remote asked for some data """
        try:
            folder = self.engine.folders[packet.payload.folder]
        except KeyError:
            logger.error("Remote asked folder folder %r, but we don't have that folder", packet.payload.folder)
            # FIXME: How do we stop normal occurences of this? Terminate all active connections on folder addition/removal?
            return

        data = folder.requested_file_block(
            self,
            packet.payload.name,
            packet.payload.offset,
            packet.payload.size,
        )

        self.send_message(
            3,
            data=data,
            id=payload.header.message_id,
        )

    def handle_3(self, packet):
        """ Remote answered a request for data """

    def handle_4(self, packet):
        """ Remote pinged us """
        self.send_message(5, id=payload.header.message_id)

    def handle_7(self, packet):
        """ Remote is closing connection with us """
        logger.debug("Remote is closing connection: %s", packet.payload.close_message)
        self.close()

    def handle_packet(self, packet):
        logger.debug("RECV: %s", packet.header.message_type)
        # logger.debug("RECV: %s", packet)
        cb = getattr(self, "handle_%s" % packet.header.message_type, None)
        if not cb:
            return
        return cb(packet)

    def _read_packet(self):
        self.inp.read_bytes_async(1024, 0, None, self._read_packet_finish)

    def _read_packet_finish(self, conn, result):
        data = self.inp.read_bytes_finish(result).get_data()
        self._read_buffer += data

        container = packet_stream.parse(self._read_buffer)
        for p in container.packet:
            self.handle_packet(p)
        self._read_buffer = "".join(chr(x) for x in container.leftovers)

        self._read_packet()
