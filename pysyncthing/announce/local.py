import socket

from gi.repository import GLib, Gio
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
        self._loop_id = GLib.timeout_add_seconds(30, self._broadcast, None)

    def lookup(self, device_id):
        return None

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
        self.sock.bind(('', 21025))

        self._channel = GLib.IOChannel.unix_new(self.sock.fileno())
        self._channel.add_watch(GLib.IO_IN, self._handle)

    def lookup(self, device_id):
        return self.devices.get(device_id, None)

    def _handle(self, io, flags):
        data, address = self.sock.recvfrom(1024)
        if not len(data):
            return False
        packet = Announcement.parse(data)
        self.devices[packet.id] = packet
        return True
