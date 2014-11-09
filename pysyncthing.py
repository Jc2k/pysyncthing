import lz4
from construct import \
    Struct, BitStruct, Flag, Padding, Bit, PascalString, MetaArray, UBInt64, UBInt32, UBInt16, Adapter, BitField, Switch, TunnelAdapter, LengthValueAdapter, Sequence, Field, OptionalGreedyRange, UBInt8, Aligned, StringAdapter


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
    UBInt32("file_count"),
    MetaArray(lambda c: c["file_count"], FileInfo),
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
    UBInt32("folder_count"),
    MetaArray(lambda c: c["folder_count"], Folder),
    UBInt32("option_count"),
    MetaArray(lambda c: c["option_count"], Option),
    OptionalGreedyRange(UBInt8("leftovers")),
)

IndexMessage = Struct(
    "index_message",
    String("folder"),
    UBInt32("file_count"),
    MetaArray(lambda c: c["file_count"], FileInfo),
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

messages_switch = Switch("message", lambda c: c["header"].message_type, {
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
        BitField("version", 4),
        BitField("message_id", 12),
        BitField("message_type", 8),
        Padding(7),
        Flag("compressed"),
    ),
    UBInt32("length"),
    #Switch("payload", lambda context: context["header"].compressed, {
    #    False: messages_switch,
    #    True: TunnelAdapter(
    #        Lz4Blob("data"),
    #        messages_switch,
    #    )
    #})
    ClusterConfigMessage
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


# Initialize context
ctx = SSL.Context(SSL.TLSv1_2_METHOD)
#ctx.set_verify(SSL.VERIFY_PEER, verify_cb) # Demand a certificate
ctx.use_privatekey_file('client.key')
ctx.use_certificate_file('client.crt')
#ctx.load_verify_locations(os.path.join(os.cwd, 'CA.cert'))

# Set up client
sock = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
sock.connect(('localhost', 22000))


data = ""
while True:
    print len(data)
    data += sock.recv(1024)
    container = packet_stream.parse(data)
    print container

    for packet in container.packet:
        print packet

    data = container.leftovers

sock.shutdown()
sock.close()
