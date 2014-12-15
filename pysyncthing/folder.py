# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/folder.py: Deal with syncing a given folder with a number of peer devices
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see <http://www.gnu.org/licenses/>.

import logging
import os

from .folder_monitor import FileMonitor


logger = logging.getLogger(__name__)


class Folder(object):

    def __init__(self, name, path, devices):
        self.name = name
        self.path = path
        self.devices = devices
        self.monitor = FileMonitor(path)

    def process_remote_index(self, index):
        pass

    def send_index(self, device):
        files = []
        device.send_message(
            1,
            folder=self.name,
            files=files,
        )

    def send_index_update(self, device):
        files = []
        device.send_message(
            6,
            folder=self.name,
            files=files,
        )

    def requested_file_block(self, device, file, offset, size):
        """ A remote device asked for a file chunk """
        with open(os.path.join(self.path, file)) as fp:
            fp.seek(offset)
            data = offset.read(size)
        return data

    def receive_file_block(self, device, request, reply):
        """ We have received a chunk of a remote file """
        if request.size != len(reply.data):
            logger.warning("Asked %r for %s bytes from %r but got %s", device, request.size, request.file, len(reply.data))
            return

        with open(os.path.join(self.path, request.file), "w+") as fp:
            fp.seek(request.offset)
            fp.write(reply.data)

    def request_file_block(self, device, file, offset, size):
        """ Ask for a chunk of a remote file """
        result = self.device.send_message(
            3,
            folder=self.name,
            name=file,
            offset=offset,
            size=size,
        )
        result.callback = self.receive_file_block

    def start(self):
        logger.debug("Watching folder %s at %s", self.name, self.path)
        if not os.path.exists(self.path):
            logger.debug("Directory %r does not exist - creating", self.path)
            os.makedirs(self.path)
        self.monitor.start()
