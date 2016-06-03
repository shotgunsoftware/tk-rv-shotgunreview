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
import tank

class MiniCutWidget(QtGui.QDockWidget):

    def __init__(self, parent):
        """
        Constructor
        """
        window = parent._rv_mode._app.engine.get_dialog_parent()
        QtGui.QDockWidget.__init__(self, "MiniCut", window) 

        self._tray = parent
        self._mini_button = self._tray.tray_button_mini_cut
        self._rv_mode= parent._rv_mode
        self.widget = None

        self.init_ui()
        self.topLevelChanged.connect(self.dock_handler)

    def dock_handler(self, stuff):
        self.setFloating(False)

    def init_ui(self):
        style =  """
            QSpinBox  {
                padding-left: 1px;
                padding-right: 1px;
                padding-top: 1px;
                padding-bottom: 1px;
                background-color: rgb(27,27,27);
                opacity: 0;
                min-height: 36px;
                border: 1px solid rgb(42,42,42);
                border-image: none;
                color: rgb(200, 200, 200);
                selection-background-color: rgb(50,50,51);
                selection-color: rgb(255,255,255);
            }
            QSpinBox:focus {
                border: 4px solid rgb(42,42,45);
                selection-color: rgb(255,255,255);
            }
            QSpinBox::lineEdit:focus {
                border: 4px solod rgb(0,0,0);
                selection-color: rgb(255,255,255);
            }
            QSpinBox::up-button {
                width: 14px;
                height: 14px;
            }
            QSpinBox::down-button {
                width: 14px;
                height: 14px;
            }

        """
        self.setTitleBarWidget(None)
        self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)

        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.widget = QtGui.QFrame(self)

        self.widget.setObjectName('mini_cut_widget')
        self.widget.hlayout = QtGui.QHBoxLayout(self.widget)

        self.widget.mini_left_spinner = QtGui.QSpinBox()
        #self.widget.mini_left_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_left_spinner.setValue(2)
        self.widget.mini_left_spinner.setStyleSheet(style)
        self.widget.hlayout.addWidget(self.widget.mini_left_spinner)

        self.widget.left_label = QtGui.QLabel()
        self.widget.left_label.setText('Before')
        self.widget.hlayout.addWidget(self.widget.left_label)

        self.widget.mini_right_spinner = QtGui.QSpinBox()
        self.widget.mini_right_spinner.setObjectName("right_spinner")
        #self.widget.mini_right_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_right_spinner.setValue(2)
        self.widget.mini_right_spinner.setStyleSheet(style)
        self.widget.hlayout.addWidget(self.widget.mini_right_spinner)

        self.widget.right_label = QtGui.QLabel()
        self.widget.right_label.setText('After')
        self.widget.hlayout.addWidget(self.widget.right_label)

        self.widget.setStyleSheet('QFrame { background: rgb(37,38,41); }')

        s = QtCore.QSize(250,60)

        self.widget.setMinimumSize(s)
        self.setMinimumSize(s)
 
    def position_minicut(self):
        p = self._tray.down_arrow_button.pos()
        s = self._mini_button.size()
        y = self._rv_mode.tray_dock.pos().y() + s.height() + p.y() + 15
        p2 = QtCore.QPoint( p.x() - 100, y)
        self.move(p2)
        self.raise_()

    def repaint_and_position(self):
        self.setFloating(False)
        self.position_minicut()
        self.repaint()

    def double_click_handler(self):
        print "WORKS"
        pass


