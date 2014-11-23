from gi.repository import Gio
# from construct import Container
from .protocol import packet
from .connection import ConnectionBase


class ClientConnection(ConnectionBase):

    def __init__(self, engine, hostname, port):
        super(ClientConnection, self).__init__()

        self.engine = engine

        client = Gio.SocketClient()
        connection = client.connect_to_host(hostname, port, None)

        self.conn = Gio.TlsClientConnection(connection, None)
        self.conn.set_certificate(self.engine.certificate)

        self.inp = self.conn.get_input_stream()
        self.outp = self.conn.get_output_stream()
        self._read_packet()

    def handle_0(self, payload):
        self.send_hello([], {"name": self.engine.name})

    def handle_1(self, payload):
        self.send_message(
            1,
            folder="default",
            files=[],
        )

        for file in packet.payload.files:
            offset = 0
            for block in file.blocks:
                self.send_message(
                    2,
                    folder=packet.payload.folder,
                    name=file.name,
                    offset=offset,
                    size=block.size,
                )
                # FIXME: Verify hash
                offset += 0

    def handle_4(self, payload):
        self.send_message(5, id=packet['header'].message_id)
