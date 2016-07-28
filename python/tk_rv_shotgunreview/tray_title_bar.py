# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.
from tank.platform.qt import QtCore, QtGui

class TrayTitleBar(QtGui.QFrame):
    """
    when the tray is floating, and you click on a menu but dont select anything, that is
    mouse off the menu, the menu remains open, and you can move the dock but the menu tears
    off and remains stationary. 

    the menus remain open because the session window is active and receiving their events
    which are getting eaten by the dock.

    so instead of using the default native titlebar, we make a custom one that we can use
    to force the dock window to be active, thus auto-closing the menus, for that we have to
    implement the drag and consume the event.
    """

    def __init__(self, parent):
        QtGui.QFrame.__init__(self, parent)
        self.setStyleSheet("QFrame { background: rgb(100,99,98); margin-bottom: 3px; }")
        self._clicked_pos = None

    def mouseMoveEvent(self, event):
        # we often get here without a starting Press event, since that gets
        # consumed by the menu's active window. So if clicked pos is none,
        # we'll just use our current position as the click point.
        if not self._clicked_pos:
            self._clicked_pos = event.pos()

        self.parent().move(event.globalPos() - self._clicked_pos )  
        event.accept()

    def mousePressEvent(self, event):
        self._clicked_pos = event.pos()
        event.ignore()

    def mouseReleaseEvent(self, event):
        # we can get a release without a pressed. so by setting to None
        # here we can tell in mousemove if we never got a pressed and 
        # clicked_pos is invalid.
        self._clicked_pos = None
        event.ignore()

    def sizeHint(self):
        # seems to yield a decent starting place for now
        return QtCore.QSize(1280,14)

    def minimumSize(self):
        # insures that we see something
        return QtCore.QSize(980,14)
