
import time
import sys
import socket


class AnnounceLocal(object):

    BROADCAST_PORT = 21025

    def run(self):
        sock = self.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while True:
            data = ''
            s.sendto(data, ('<broadcast>', self.BROADCAST_PORT))
            time.sleep(30)


class AnnouceLocalSender(object):

    BROADCAST_PORT = 21025

    def run(self):
        sock = self.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('<broadcast>', self.BROADCAST_PORT))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while True:
            data = s.recv(1024)

