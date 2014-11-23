from construct import Container
from .protocol import packet, packet_stream


class ConnectionBase(object):

    def __init__(self, engine):
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
        print "SEND", packet.parse(data)
        self.outp.write(data)
        self.local_message_id += 1

    def send_hello(self, client_name, client_version, folders, options):
        self.send_message(
            0,
            client_name=client_name,
            client_version='v0.10.5',
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
        print "RECV", packet
        cb = getattr(self, "handle_%s" % packet.header.message_type, None)
        if not cb:
            return
        return cb(packet)

    def _read_packet(self):
        self.inp.read_async(1024, self._read_packet_finish)

    def _read_packet_finish(self, conn, result, user_data):
        results = conn.read_async_finish(result)
        print results
        return

        self._read_buffer += data
        container = packet_stream.parse(self._read_buffer)
        for p in container.packet:
            self.handle_packet(p)
        self._read_buffer = "".join(chr(x) for x in container.leftovers)
