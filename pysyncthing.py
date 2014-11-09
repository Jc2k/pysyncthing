import lz4
from construct import \
    Struct, BitStruct, Flag, Padding, Bit, PascalString, MetaArray, UBInt64, UBInt32, Adapter, BitField, Switch, TunnelAdapter, LengthValueAdapter, Sequence, Field, OptionalGreedyRange, UBInt8


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
    return PascalString(name, length_field=UBInt32("length"))


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
    Switch("payload", lambda context: context["header"].compressed, {
        False: messages_switch,
        True: TunnelAdapter(
            Lz4Blob("data"),
            messages_switch,
        )
    })
)

packet_stream = Struct("packet_stream",
    OptionalGreedyRange(packet),
    OptionalGreedyRange(UBInt8("leftovers")),
)


from OpenSSL import SSL
import sys, os, select, socket

def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    print 'Got certificate: %s' % cert.get_subject()
    return ok

# Initialize context
ctx = SSL.Context(SSL.TLSv1_2_METHOD)
ctx.set_verify(SSL.VERIFY_PEER, verify_cb) # Demand a certificate
#ctx.use_privatekey_file (os.path.join(os.cwd, 'client.pkey'))
#ctx.use_certificate_file(os.path.join(os.cwd, 'client.cert'))
#ctx.load_verify_locations(os.path.join(os.cwd, 'CA.cert'))

# Set up client
sock = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
sock.connect(('localhost', 22000))


data = ""
while True:
    data += sock.recv(1024)
    container = packet_stream.parse(data)

    for packet in container.packet:
        print packet

    data = container.leftovers

sock.shutdown()
sock.close()
