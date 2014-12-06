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


logger = logging.getLogger(__name__)


class Folder(object):

    def __init__(self, name, path, peers):
        self.name = name
        self.path = path
        self.peers = peers

    def send_index(self, device):
        files = []
        device.send_message(
            1,
            folder=self.name,
            files=files,
        )

    def start(self):
        logger.debug("Watching folder %s at %s", self.name, self.path)
