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
        self.setStyleSheet("QWidget { background: rgb(100,99,98); margin-bottom: 3px; }")
        self._last_pos = self.pos()

    def mouseMoveEvent(self, event):
        #print "MOVE %r" % event.pos()
        d = self._last_pos - event.pos()  
        #print "MNOVE %r %r" % ( d, (self.parent().pos() - d)) 
        if d.x() > -10 and d.x() < 10:
            self.parent().move(self.parent().pos() - (d/2))

        # print "%r vs %r" % ( self.parent().pos() , d)
        self._last_pos = event.pos()     
        #sys.stdout.flush()
        event.ignore()

    def mousePressEvent(self, event):
        #print "PRESS %r" % event.pos()
        #sys.stdout.flush()
        self._last_pos = event.pos()     
        event.ignore()

    def mouseReleaseEvent(self, event):
        #print "RELEASE %r" % event.pos()
        #sys.stdout.flush()    
        self._last_pos = event.pos()  

        event.ignore()

    def sizeHint(self):
        return QtCore.QSize(1280,14)

    def minimumSize(self):
        return QtCore.QSize(980,14)
