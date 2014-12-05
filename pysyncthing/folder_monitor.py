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

import os
from gi.repository import Gio, GLib


class FileMonitor(object):

    def __init__(self, path):
        self.monitors = {}
        self._listen_to_directory(Gio.File.new_for_path(path))

    def _listen_to_directory(self, file):
        print "Subscribe to directory %r" % file.get_path()
        for child_info in file.enumerate_children("", 0, None):
            if child_info.get_file_type() != Gio.FileType.DIRECTORY:
                continue
            child = file.get_child(child_info.get_name())
            self._listen_to_directory(child)

        m = self.monitors[file.get_path()] = file.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        m.connect("changed", self._changed)

    def _changed(self, m, f, o, event):
        if event == Gio.FileMonitorEvent.CREATED:
            info = f.query_info("standard::", 0, None)
            if info.get_file_type() == Gio.FileType.DIRECTORY:
                self._listen_to_directory(f)
        elif event == Gio.FileMonitorEvent.DELETED:
            if f.get_path() in self.monitors:
                print "Unsubscribing from directory %r" % f.get_path()
                del self.monitors[f.get_path()]
        else:
            print m, f, o, event, info


if __name__ == "__main__":
    m = FileMonitor(os.path.join(os.environ['HOME'], "Projects", "test"))
    print "Finished subscribing"
    GLib.MainLoop().run()
