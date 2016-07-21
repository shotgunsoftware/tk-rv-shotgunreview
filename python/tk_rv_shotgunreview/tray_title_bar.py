# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.
import sys

from tank.platform.qt import QtCore, QtGui

class TrayTitleBar(QtGui.QFrame):

    def __init__(self, parent):

        QtGui.QFrame.__init__(self, parent)
        self.setStyleSheet("QWidget { background: rgb(100,99,98); }")

    def mouseMoveEvent(self, event):
        print "MOVE %r" % event.pos()
        sys.stdout.flush()
        event.ignore()

    def mousePressEvent(self, event):
        print "PRESS %r" % event.pos()
        sys.stdout.flush()        
        event.ignore()

    def mouseReleaseEvent(self, event):
        print "RELEASE %r" % event.pos()
        sys.stdout.flush()        
        event.ignore()

    def sizeHint(self):
        return QtCore.QSize(1280,10)

    def minimumSize(self):
        return QtCore.QSize(980,10)
