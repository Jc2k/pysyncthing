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
            folders=[],
            options={
                "name": "curiosity",
            },
        )

    def handle_4(self, packet):
        self.send_message(5, id=packet['header'].message_id)

    def handle_packet(self, packet):
        cb = getattr(self, "handle_%s" % packet.header.message_type, None)
        if not cb:
            return
        print packet
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
