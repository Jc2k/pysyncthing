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

    def __init__(self, engine):
        self.local_message_id = 0
        self.engine = engine
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

    def send_hello(self, folders, options):
        self.send_message(
            0,
            client_name=self.engine.CLIENT_NAME,
            client_version=self.engine.CLIENT_VERSION,
            folders=[
                Container(
                    id='default',
                    devices=[
                        Container(
                            id='\x05\x13\x1d8\x8a\xc3\xd5\xe1\xd5\xcd\xe1\xb7\xa7j\xff\xbfq\xaf/\x1fX\xf4\x86J\\\xd2\xc6p\x91\xed\x85\xa2',
                            flags=Container(
                                priority=0,
                                introducer=False,
                                read_only=False,
                                trusted=True,
                            ),
                            max_local_version=0,
                        ),
                        Container(
                            id='\xcd\xb4\xc3MP\xa9%\xa8\x08Y\x10C)O\xe91q\x9d\xf1,\xb8\x94\x81\xc5\xb0\xecim+o\xd6\xb9',
                            flags=Container(
                                priority=0,
                                introducer=False,
                                read_only=False,
                                trusted=True,
                            ),
                            max_local_version=0,
                        )
                    ]
                )
            ],
            options=options or {},
        )

    def handle_packet(self, packet):
        logger.debug("RECV: %s", packet)
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
