import socket
from OpenSSL import SSL
from construct import Container

from .protocol import packet, packet_stream


class ConnectionBase(object):

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
        print packet.parse(data)
        self.socket.send(data)
        self.local_message_id += 1


class ClientConnection(ConnectionBase):

    def __init__(self, hostname, port):
        self.local_message_id = 1

        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        # ctx.set_verify(SSL.VERIFY_PEER, verify_cb) # Demand a certificate
        ctx.use_privatekey_file('client.key')
        ctx.use_certificate_file('client.crt')

        self.socket = SSL.Connection(
            ctx,
            socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        )
        self.socket.connect((hostname, port))

    def handle_0(self, packet):
        self.send_message(
            0,
            client_name='syncthing',
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
            options={
                "name": "example",
            },
        )

    def handle_4(self, packet):
        self.send_message(5, id=packet['header'].message_id)

    def handle_packet(self, packet):
        print packet
        cb = getattr(self, "handle_%s" % packet.header.message_type, None)
        if not cb:
            return
        return cb(packet)

    def handle(self):
        data = ""
        while True:
            data += self.socket.recv(1024)
            if not data:
                continue

            container = packet_stream.parse(data)
            for p in container.packet:
                self.handle_packet(p)

            data = "".join(chr(x) for x in container.leftovers)

        self.socket.shutdown()
        self.socket.close()
