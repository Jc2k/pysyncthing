

class ClientFactory(object):

    def __init__(self):
        self.discoverers = [
        ]

    def connect_by_id(self, id):
        hostname = None

        for backend in self.discoverers:
            hostname = backend.lookup(id)
            if hostname:
                break
 
        if not hostname:
            raise ValueError("Unable to find ID" % id)

        return self.connect(*hostname.split(":"))

    def connect(self, hostname, port):
        pass
