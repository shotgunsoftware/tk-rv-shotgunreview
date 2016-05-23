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
        QtGui.QDockWidget.__init__(self, "MiniCut", window) 
        # , QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)

        self._tray = parent
        self._mini_button = self._tray.tray_button_mini_cut
        self._rv_mode= parent._rv_mode
        self.widget = None

        self.init_ui()
        # self.widget.mini_left_spinner.doubleClicked.connect(self.double_click_handler)
        self.topLevelChanged.connect(self.dock_handler)

    def dock_handler(self, stuff):
        print "DOCK %r" % stuff
        self.setFloating(False)

    def init_ui(self):
        self.setTitleBarWidget(None)
        #self.setFloating(False)
        self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)

        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.widget = QtGui.QFrame(self)

        self.widget.setObjectName('mini_cut_widget')
        self.widget.hlayout = QtGui.QHBoxLayout(self.widget)

        self.widget.mini_left_spinner = QtGui.QSpinBox()
        #self.widget.mini_left_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_left_spinner.setValue(2)
        self.widget.hlayout.addWidget(self.widget.mini_left_spinner)

        self.widget.left_label = QtGui.QLabel()
        self.widget.left_label.setText('Before')
        self.widget.hlayout.addWidget(self.widget.left_label)

        self.widget.mini_right_spinner = QtGui.QSpinBox()
        self.widget.mini_right_spinner.setObjectName("right_spinner")
        #self.widget.mini_right_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.widget.mini_right_spinner.setValue(2)
        #self.widget.mini_right_spinner.setStyleSheet('QSpinBox:focus, QLineEdit:focus { border: 1px solid rgb(255,0,0); } QSpinBox, QLineEdit { selection-border-color: rgb(250,50,55);}')
        self.widget.mini_right_spinner.setStyleSheet(
            """
            QSpinBox  {
            padding-left: .2em;
            padding-right: .2em;
            padding-top: .2ex;
            padding-bottom: .2ex;
            border-radius: .15em;
            background-color: rgb(27,27,27);
            opacity: 0;
            min-height: 1.25em;
            border: 0px solid rgb(242,42,42);
            color: rgb(200, 200, 200);
            selection-background-color: rgb(250,50,55);
            selection-color: rgb(255,255,255);
            }
            QLineEdit::focus,  QSpinBox::focus {
            border: 0px solid rgb(242,42,55);
            }
            """
            )
        #QLineEdit:focus,  QSpinBox:focus {
        #    border: 2px solid rgb(42,42,255);
        #}
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


