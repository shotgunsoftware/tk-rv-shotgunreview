# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from .ui.details_panel_widget import Ui_DetailsPanelWidget
# from .version_list_delegate import RvVersionListDelegate
# from .shot_info_delegate import RvShotInfoDelegate
# from .shot_info_widget import ShotInfoWidget
from .list_item_widget import ListItemWidget
from .list_item_delegate import ListItemDelegate
# from .model_version_listing import SgVersionModel

import tank

from tank.platform.qt import QtCore, QtGui

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class DetailsPanelWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        """
        Constructor
        """
        QtGui.QWidget.__init__(self, parent)

        self._pinned = False
        self._requested_entity = None
        
        # set up the UI
        self.ui = Ui_DetailsPanelWidget() 
        self.ui.setupUi(self)

        self.version_delegate = ListItemDelegate(
            self.ui.entity_version_view,
        )

        self._fields = [
            "code",
            "entity",
            "image",
        ]

        self.version_model = shotgun_model.SimpleShotgunModel(self.ui.entity_version_tab)
        # self.version_model = SgVersionModel(self.ui.entity_version_tab)

        # Tell the view to pull data from the model
        self.ui.entity_version_view.setModel(self.version_model)
        self.ui.entity_version_view.setItemDelegate(self.version_delegate)

        task_manager = tank.platform.import_framework(
            "tk-framework-shotgunutils",
            "task_manager",
        )

        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self.ui.note_stream_widget,
            start_processing=True,
            max_threads=2,
        )
        
        shotgun_globals = tank.platform.import_framework(
            "tk-framework-shotgunutils",
            "shotgun_globals",
        )

        shotgun_globals.register_bg_task_manager(self._task_manager)

        self.ui.note_stream_widget.set_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.allow_screenshots = False
        self.ui.note_stream_widget.show_sg_stream_button = False
        self.shot_info_model = shotgun_model.SimpleShotgunModel(self.ui.note_stream_widget)

        si_size = ListItemWidget.calculate_size()
        self.ui.shot_info_widget.setMaximumSize(QtCore.QSize(si_size.width(), si_size.height()))

        # Signal handling.
        self.ui.pin_button.toggled.connect(self._set_pinned)
        self.ui.shotgun_nav_button.clicked.connect(self.ui.note_stream_widget._load_shotgun_activity_stream)

    def load_data(self, entity):
        # If we're pinned, then we don't allow loading new entities.
        if not self._pinned:
            self.ui.note_stream_widget.load_data(entity)

            shot_filters = [["id", "is", entity["id"]]]
            self.shot_info_model.load_data(
                entity_type="Version",
                filters=shot_filters,
                fields=self._fields,
            )

            sg_data = self.shot_info_model.item_from_entity("Version", entity["id"]).get_sg_data()
            self.ui.shot_info_widget.set_entity(sg_data)

            version_filters = [["entity", "is", sg_data["entity"]]]
            self.version_model.load_data(
                "Version",
                filters=version_filters,
                fields=self._fields,
            )
        else:
            self._requested_entity = entity

    def _set_pinned(self, checked):
        self._pinned = checked
        if checked:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_hover.png"))
        else:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_up.png"))
            if self._requested_entity:
                self.load_data(self._requested_entity)
                self._requested_entity = None

