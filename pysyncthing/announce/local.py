
from gi.repository import Gio
import socket
from construct import Container

from ..protocol import Announcement


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

    def _broadcast(self):
        data = Announcement.build(Container(
            device=Container(
                id="public key?",
                addresses=[
                    Container(
                        ip="",
                        port=2200,
                    ),
                ],
            ),
            devices=[],
        ))
        self.sock.send_to(self.address, data)


class DiscoverLocal(object):

    def __init__(self, engine, port=21025):
        self.engine = engine
        self.address = Gio.InetSocketAddress.new(
            Gio.InetAddress.new_any(Gio.SocketFamily.IPV4),
            port,
        )

    def start(self):
        self.sock = Gio.Socket.new(
            Gio.SocketFamily.IPV4,
            Gio.SocketType.DATAGRAM,
            Gio.SocketProtocol.UDP,
        )
        self.sock.bind(self.address, True)
        self.sock.set_option(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # while True:
        #    print self.sock.receive(1)
