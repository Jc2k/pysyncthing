import lz4
from construct.lib.py3compat import BytesIO
from construct import \
    ExprAdapter, Struct, BitStruct, Flag, Padding, MetaArray, UBInt64, UBInt32, BitField, \
    Switch, TunnelAdapter, LengthValueAdapter, Sequence, Field, OptionalGreedyRange, \
    UBInt8, StringAdapter, ConstAdapter, Subconstruct


class PrefixActualLength(Subconstruct):

    def __init__(self, subcon, length_field=UBInt32("length")):
        super(PrefixActualLength, self).__init__(subcon)
        self.length_field = length_field

    def _parse(self, stream, context):
        # Read and ignore the length field
        self.length_field._parse(stream, context)
        return self.subcon._parse(stream, context)

    def _build(self, obj, stream, context):
        inner_stream = BytesIO()
        self.subcon._build(obj, inner_stream, context)
        data = inner_stream.getvalue()
        self.length_field._build(len(data), stream, context)
        stream.write(data)

    def _sizeof(self, context):
        return self.length_field._sizeof(context) + \
            self.subcon._sizeof(context)


def Lz4Blob(name, length_field=UBInt32("length")):
    return ExprAdapter(
        LengthValueAdapter(
            Sequence(
                name,
                length_field,
                Field("data", lambda ctx: ctx[length_field.name]),
            )
        ),
        encoder=lambda obj, ctx: lz4.dumps(obj),
        decoder=lambda obj, ctx: lz4.loads(obj),
    )


def String(name):
    return StringAdapter(
        LengthValueAdapter(
            Sequence(
                name,
                UBInt32("length"),
                Field("data", lambda ctx: ctx["length"]),
                Padding(lambda ctx: (4 - ctx['length'] % 4) % 4),
            )
        ),
    )


def Array(name, array_of):
    return LengthValueAdapter(
        Sequence(
            name,
            UBInt32("length"),
            MetaArray(lambda c: c["length"], array_of),
        ),
    )


def Dict(name, key, value):
    return LengthValueAdapter(
        Sequence(
            name,
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
    BitStruct(
        "flags",
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
    Array("devices", Device),
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

packet = Struct(
    "packet",
    BitStruct(
        "header",
        ConstAdapter(BitField("message_version", 4), 0),
        BitField("message_id", 12),
        BitField("message_type", 8),
        Padding(7),
        Flag("compressed"),
    ),
    PrefixActualLength(
        Switch("payload", lambda context: context["header"].compressed, {
            False: messages_switch,
            True: TunnelAdapter(
                Lz4Blob("data"),
                messages_switch,
            )
        }),
    ),
)

packet_stream = Struct(
    "packet_stream",
    OptionalGreedyRange(packet),
    OptionalGreedyRange(UBInt8("leftovers")),
)
