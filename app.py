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
        if os.getenv("RV_NO_CUTZ"):
            return
        parent_widget = self.engine.get_dialog_parent()
        notes_dock = QtGui.QDockWidget("CutZ", parent_widget)
        tray_dock = QtGui.QDockWidget("Tray", parent_widget)

        # if not os.getenv("RV_NO_CUTZ_STYLE"):
            # parent_widget.setStyleSheet(
            #     "QWidget { font-family: Proxima Nova; "
            #         "background: rgb(36,38,41); "
            #         "color: rgb(126,127,129); "
            #         "border-color: rgb(36,38,41);}"
            # )
 
        try:

            fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes_dock.qss")          
            f = open(fn, 'r')
            s = f.read()
            f.close()
            notes_dock.setStyleSheet(s)

        except Exception as e:
            self.engine.log_error(e)

        notes_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        tray_dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)

        self.engine.get_top_toolbar().addAction(notes_dock.toggleViewAction())

        tk_rv_shotgunreview = self.import_module("tk_rv_shotgunreview")
        self._rv_activity_stream = tk_rv_shotgunreview.RvActivityMode(app=self)
        self._rv_activity_stream.init_ui(notes_dock, tray_dock, 8)


        rv.commands.activateMode("RvActivityMode")
        
        parent_widget.addDockWidget(QtCore.Qt.RightDockWidgetArea, notes_dock)
        parent_widget.addDockWidget(QtCore.Qt.BottomDockWidgetArea, tray_dock)

        try:
            fn = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray_dock.qss")          
            f = open(fn, 'r')
            s = f.read()
            f.close()
            tray_dock.setStyleSheet(s)
        except Exception as e:
            self.engine.log_error(e)

    #####################################################################################
    # Properties

    @property
    def context_change_allowed(self):
        """
        Specifies that on-the-fly context changes are supported.
        """
        return True

    #####################################################################################
    # utility methods

    def change_to_entity_context(self, entity_type, entity_id):
        """
        Changes to the context matching that of the given entity.

        :param entity_type: The entity type (example: Cut, Version, etc).
        :param entity_id:   The id number of the entity.
        """
        # TODO: Note that this does not work right now with the
        # bootstrap strategy employed with RV. We end up getting
        # an error stating that the given entity is from a project
        # that does not match our current config and it bails.
        tk = tank.tank_from_entity(entity_type, entity_id)

        if not tk:
            return

        context = tk.context_from_entity(entity_type, entity_id)

        if not context or context == self.engine.context:
            return

        self.engine.change_context(context)

    def _env_info(self):
        self.engine.log_info("TANK_CONTEXT: %s" % os.environ.get("TANK_CONTEXT"))
        self.engine.log_info('QtGui: %r' % QtGui)
        self.engine.log_info('QtCore: %r' % QtCore)
        self._rv_activity_stream.load_data( { "type": "Version", "id": 41})

        
