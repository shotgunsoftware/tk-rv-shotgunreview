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
# from .tray_delegate import RvTrayDelegate
import tank
# task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")

class MiniCutWidget(QtGui.QDockWidget):

    def __init__(self, parent):
        """
        Constructor
        """
        window = parent._rv_mode._app.engine.get_dialog_parent()
        print "WIN %r" % window
        QtGui.QDockWidget.__init__(self, "Blerg", window) 
        # , QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)

        self._tray = parent
        self._mini_button = self._tray.tray_button_mini_cut
        self._rv_mode= parent._rv_mode

        self.init_ui()

    def init_ui(self):
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.widget = QtGui.QFrame(self)

        self.widget.setObjectName('mini_cut_widget')
        self.widget.hlayout = QtGui.QHBoxLayout(self.widget)

        self.widget.mini_left_spinner = QtGui.QSpinBox()
        self.widget.mini_left_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_left_spinner.setValue(2)
        self.widget.hlayout.addWidget(self.widget.mini_left_spinner)

        self.widget.left_label = QtGui.QLabel()
        self.widget.left_label.setText('Before')
        self.widget.hlayout.addWidget(self.widget.left_label)

        self.widget.mini_right_spinner = QtGui.QSpinBox()
        self.widget.mini_right_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_right_spinner.setValue(2)
        self.widget.hlayout.addWidget(self.widget.mini_right_spinner)

        self.widget.right_label = QtGui.QLabel()
        self.widget.right_label.setText('After')
        self.widget.hlayout.addWidget(self.widget.right_label)

        self.widget.setStyleSheet('QFrame { background: rgb(37,38,41);  }')

        s = QtCore.QSize(250,60)

        self.widget.setMinimumSize(s)
        self.setMinimumSize(s)
 
    def enable_minicut(self, visible=True):
        p = self._tray.down_arrow_button.pos()
        s = self._mini_button.size()
        y = self._rv_mode.tray_dock.pos().y() + s.height() + p.y() + 15
        p2 = QtCore.QPoint( p.x() - 100, y)
        self.move(p2)
        #self.setVisible(visible)
        self.raise_()




