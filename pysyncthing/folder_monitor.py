# -*- Mode: Python; py-indent-offset: 4 -*-
# pysyncthing - GNOME implementation of the syncthing engine
# Copyright (C) 2014 John Carr
#
#   pysyncthing/folder_monitor.py: Abstraction around Gio.FileMonitor that is recursive
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

from gi.repository import Gio


logger = logging.getLogger(__name__)


class FileMonitor(object):

    def __init__(self, path):
        self.monitors = {}
        self._handlers = {}
        self.path = path

    def start(self):
        self._listen_to_directory(Gio.File.new_for_path(self.path))

    def _listen_to_directory(self, file):
        path = file.get_path()
        logger.debug("Subscribing to directory %r", path)
        for child_info in file.enumerate_children("standard::*", Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, None):
            if child_info.get_file_type() != Gio.FileType.DIRECTORY:
                continue
            child = file.get_child(child_info.get_name())
            self._listen_to_directory(child)

        m = self.monitors[path] = file.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self._handlers[path] = m.connect("changed", self._changed)

    def _changed(self, m, f, o, event):
        path = f.get_path()

        if event == Gio.FileMonitorEvent.CREATED:
            info = f.query_info("standard::", 0, None)

            file_type = info.get_file_type()
            if file_type == Gio.FileType.DIRECTORY:
                self._listen_to_directory(f)
            elif file_type in (Gio.FileType.REGULAR, ):
                logger.debug("File %r created", path)

        elif event == Gio.FileMonitorEvent.DELETED:
            if path in self.monitors:
                logger.debug("Unsubscribing from directory %r", path)
                self.monitors[path].disconnect(self._handlers[path])
                del self._handlers[path]
                del self.monitors[path]

            if True:
                # FIXME: If a file was deleted we can't really tell what it was...
                # if info.get_file_type() in (Gio.FileType.REGULAR, ):
                logger.debug("File %r deleted", path)

        else:
            logger.debug("%r", (m, f, o, event, info))
