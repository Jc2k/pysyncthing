
class GlobalDiscovery(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_..)
        sock.connect((self.host, self.port))
