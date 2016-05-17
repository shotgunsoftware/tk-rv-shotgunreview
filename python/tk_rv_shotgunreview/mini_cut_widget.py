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
        QtGui.QDockWidget.__init__(self, parent)

        self._tray = parent
        self._mini_button = self._tray.tray_button_mini_cut
        self._rv_mode= parent._rv_mode

        self.init_ui()

    def init_ui(self):
        self.setObjectName('mini_cut_widget')
        self.hlayout = QtGui.QHBoxLayout()

        self.mini_left_spinner = QtGui.QSpinBox()
        self.mini_left_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mini_left_spinner.setValue(2)
        self.hlayout.addWidget(self.mini_left_spinner)

        self.left_label = QtGui.QLabel()
        self.left_label.setText('Before')
        self.hlayout.addWidget(self.left_label)

        self.mini_right_spinner = QtGui.QSpinBox()
        self.mini_right_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mini_right_spinner.setValue(2)
        self.hlayout.addWidget(self.mini_right_spinner)

        self.right_label = QtGui.QLabel()
        self.right_label.setText('After')
        self.hlayout.addWidget(self.right_label)
 
    def enable_minicut(self, visible=True):
        p = self._mini_button.pos()
        s = self._mini_button.size()
        p2 = QtCore.QPoint( p.x(), p.y() + s.height())
        self.move(p2)
        self.setVisible(visible)




