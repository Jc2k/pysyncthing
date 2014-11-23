from gi.repository import Gio, GLib

from pysyncthing.connection import ConnectionBase


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
        print "Acceptiong cert..."
        return True

    def _handshake_complete(self, conn, task):
        print "Handshake complete"

        self.inp = self.conn.get_input_stream()
        self.outp = self.conn.get_output_stream()

        self.send_hello(folders=[], options={"name": self.engine.name})
        self._read_packet()

    def handle_1(self, payload):
        # FIXME: Workout name and register with engine...
        pass
