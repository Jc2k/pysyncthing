import lz4
from construct import \
    ExprAdapter, Struct, BitStruct, Flag, Padding, Bit, PascalString, MetaArray, UBInt64, UBInt32, UBInt16, Adapter, BitField, Switch, TunnelAdapter, LengthValueAdapter, Sequence, Field, OptionalGreedyRange, UBInt8, Aligned, StringAdapter, Container, ConstAdapter


class Lz4Adapter(Adapter):

    def _encode(self, obj, context):
        return lz4.dumps(obj)

    def _decode(self, obj, context):
        return lz4.loads(obj)


def Lz4Blob(name, length_field=UBInt32("length")):
    return Lz4Adapter(
        LengthValueAdapter(
            Sequence(name,
                length_field,
                Field("data", lambda ctx: ctx[length_field.name]),
            )
        ),
    )


def String(name):
    return StringAdapter(
        LengthValueAdapter(
            Sequence(name,
                UBInt32("length"),
                Field("data", lambda ctx: ctx["length"]),
                Padding(lambda ctx: (4 - ctx['length'] % 4) % 4),
            )
        ),
    )


def Array(name, array_of):
    return LengthValueAdapter(
        Sequence(name,
            UBInt32("length"),
            MetaArray(lambda c: c["length"], array_of),
        ),
    )


def Dict(name, key, value):
    return LengthValueAdapter(
        Sequence(name,
            UBInt32("length"),
            ExprAdapter(
                MetaArray(lambda c: c["length"], Sequence("dict", key, value)),
                encoder=lambda obj, ctx: obj.items(),
                decoder=lambda obj, ctx: dict(obj),
            )
        ),
    )


Device = Struct(
    "device",
    String("id"),
    BitStruct("flags",
        Padding(15),
        BitField("priority", 2),
        Padding(12),
        Flag("introducer"),
        Flag("read-only"),
        Flag("trusted")
    ),
    UBInt64("max_local_version"),
)

BlockInfo = Struct(
    "block_info",
    UBInt64("blocksize"),
    String("hash"),
)

FileInfo = Struct(
    "file_info",
    String("name"),
    BitStruct(
        "flags",
        Padding(17),
        Flag("no_permission"),
        Flag("invalid"),
        Flag("deleted"),
        Padding(12),
    ),
    UBInt64("modified"),
    UBInt64("version"),
    UBInt64("local_version"),
)

Folder = Struct(
    "folder",
    String("id"),
    Array("files", FileInfo),
)

Option = Struct(
    "option",
    String("key"),
    String("value"),
)

ClusterConfigMessage = Struct(
    "cluster_config",
    String("client_name"),
    String("client_version"),
    Array("folders", Folder),
    Dict("options", String("key"), String("value")),
)

IndexMessage = Struct(
    "index_message",
    String("folder"),
    Array("files", FileInfo),
)

RequestMessage = Struct(
    "request_message",
    String("folder"),
    String("name"),
    UBInt64("offset"),
    UBInt32("size"),
)

ResponseMessage = Struct(
    "response_message",
    String("data"),
)

PingMessage = Struct(
    "ping_message",
)

PongMessage = Struct(
    "pong_message",
)

IndexUpdateMessage = IndexMessage

CloseMessage = Struct(
    "close_message",
    String("reason"),
)

messages_switch = Switch("message", lambda c: c["_"]["header"].message_type, {
    0: ClusterConfigMessage,
    1: IndexMessage,
    2: RequestMessage,
    3: ResponseMessage,
    4: PingMessage,
    5: PongMessage,
    6: IndexUpdateMessage,
    7: CloseMessage,
})

packet = Struct("packet",
    BitStruct(
        "header",
        ConstAdapter(BitField("message_version", 4), 0),
        BitField("message_id", 12),
        BitField("message_type", 8),
        Padding(7),
        Flag("compressed"),
    ),
    LengthValueAdapter(
        Sequence("payload",
            UBInt32("length"),
            Switch("payload", lambda context: context["_"]["header"].compressed, {
                False: messages_switch,
                True: TunnelAdapter(
                    Lz4Blob("data"),
                    messages_switch,
                )
            }),
        ),
    ),
)

packet_stream = Struct("packet_stream",
    OptionalGreedyRange(packet),
    OptionalGreedyRange(UBInt8("leftovers")),
)


from OpenSSL import SSL, crypto
import sys, os, select, socket

if not os.path.exists("client.key"):
    print "Generating private key"
    private_key = crypto.PKey()
    private_key.generate_key(crypto.TYPE_RSA, 3096)

    print "Generating cert"
    cert = crypto.X509()
    subj = cert.get_subject()
    subj.C = "US"
    subj.ST = "Minnesota"
    subj.L = "Minnetonka"
    subj.O = "my company"
    subj.OU = "my organization"
    subj.CN = "syncthing"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(subj)
    cert.set_pubkey(private_key)
    cert.sign(private_key, 'sha1')

    with open("client.crt", "w") as fp:
        fp.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open("client.key", "w") as fp:
        fp.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key))


class ClientProtocol(object):

    def __init__(self, hostname, port):
        self.local_message_id = 1

        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        #ctx.set_verify(SSL.VERIFY_PEER, verify_cb) # Demand a certificate
        ctx.use_privatekey_file('client.key')
        ctx.use_certificate_file('client.crt')

        self.socket = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket.connect((hostname, port))

    def send_message(self, type, id=None, **kwargs):
        data = packet.build(Container(
            header = Container(
                message_version=0,
                message_id=id or self.local_message_id,
                message_type=type,
                compressed=False,
            ),
            payload = Container(**kwargs),
        ))
        print packet.parse(data)
        self.socket.send(data)
        self.local_message_id += 1

    def handle_0(self, packet):
        self.send_message(
            0,
            client_name = 'syncthing',
            client_version = 'v0.10.5',
            folders = [],
            options = {
                "name": "example",
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
            for packet in container.packet:
                self.handle_packet(packet)

            data = "".join(chr(x) for x in container.leftovers)

        self.socket.shutdown()
        self.socket.close()


c = ClientProtocol("localhost", 22000)
c.handle()


"""
Container:
    header = Container:
        version = 0
        message_id = 1
        message_type = 0
        compressed = False
    length = 60
    payload = Container:
        client_name = 'syncthing'
        client_version = 'v0.10.5'
        folder_count = 0
        folder = []
        option_count = 1
        option = [
            Container:
                key = 'name'
                value = 'curiosity'
        ]
        leftovers = []
"""

"""payload = packet.build(Container(
    header = Container(
        message_version=0,
        message_id=0,
        message_type=0,
        compressed=False,
    ),
    payload = Container(
        client_name = 'syncthing',
        client_version = 'v0.0.0',
        folders = [],
        options = {
            "name": "example",
        },
    ),
))

print packet.parse(payload)
"""
