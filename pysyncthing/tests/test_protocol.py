import unittest
from construct import Container

from pysyncthing.protocol import packet


class TestClusterConfigMessage(unittest.TestCase):

    EXAMPLE1 = "\x00\x01\x00\x01\x00\x00\x00>\x00\x00\x00:8\x00\x00\x00\xe1\x00\x00\x00\tsyncthing\x00\x01\x00\x81\x07v0.10.5\r\x00\xf0\t\x00\x00\x00\x01\x00\x00\x00\x04name\x00\x00\x00\x07example\x00"

    def test_parse_example1(self):
        p = packet.parse(self.EXAMPLE1)
        self.assertEqual(p.header.message_type, 0)
        self.assertEqual(p.payload.client_name, "syncthing")
        self.assertEqual(p.payload.client_version, "v0.10.5")

    def test_build_example1(self):
        self.assertEqual(self.EXAMPLE1, packet.build(Container(
            header=Container(
                message_version=0,
                message_id=1,
                message_type=0,
                compressed=True,
            ),
            payload=Container(
                client_name='syncthing',
                client_version='v0.10.5',
                folders=[],
                options={
                    "name": "example",
                }
            ),
        )))
