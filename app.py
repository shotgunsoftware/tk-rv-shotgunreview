# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import tank
from sgtk.platform import Application
from tank.platform.qt import QtGui, QtCore

import rv.qtutils
import rv.commands

class RVShotgunReviewApp(Application):
    """
    The app entry point. This class is responsible for intializing and tearing down
    the application, handle menu registration etc.
    """
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        parent_widget = self.engine.get_dialog_parent()
        notes_dock = QtGui.QDockWidget("CutZ", parent_widget)
        tray_dock = QtGui.QDockWidget("Tray", parent_widget)

        parent_widget.setStyleSheet(
            "QWidget { font-family: Proxima Nova; "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129); "
                "border-color: rgb(36,38,41);}"
        )
        notes_dock.setStyleSheet(
            "QWidget { "
                "font-family: Proxima Nova; "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129);} "
            "QDockWidget::title { "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129); "
                "padding: 8px; border: 0px;}"
        )
        tray_dock.setStyleSheet(
            "QWidget { "
                "font-family: Proxima Nova; "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129);} "
            "QDockWidget { "
                "padding: 8px; }"
            "QDockWidget::title { "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129); "
                "padding: 8px; border: 0px;}"
        )

        notes_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        tray_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)

        self.engine.get_top_toolbar().addAction(notes_dock.toggleViewAction())

        tk_rv_shotgunreview = self.import_module("tk_rv_shotgunreview")
        self._rv_activity_stream = tk_rv_shotgunreview.RvActivityMode(app=self)
        self._rv_activity_stream.init_ui(notes_dock, tray_dock, 8)

        rv.commands.activateMode("RvActivityMode")
        
        parent_widget.addDockWidget(QtCore.Qt.RightDockWidgetArea, notes_dock)
        parent_widget.addDockWidget(QtCore.Qt.BottomDockWidgetArea, tray_dock)

        # TODO: debug info and triggers a load_data for activity stream REMOVE LATER
        # self._env_info()

    def _env_info(self):
        self.engine.log_info("TANK_CONTEXT: %s" % os.environ.get("TANK_CONTEXT"))
        self.engine.log_info('QtGui: %r' % QtGui)
        self.engine.log_info('QtCore: %r' % QtCore)
        self._rv_activity_stream.load_data( { "type": "Version", "id": 41})

        
