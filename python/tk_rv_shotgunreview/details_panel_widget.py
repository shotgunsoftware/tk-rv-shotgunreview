# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank.platform.qt import QtCore, QtGui

from .ui.details_panel_widget import Ui_DetailsPanelWidget
from .list_item_widget import ListItemWidget
from .list_item_delegate import ListItemDelegate

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

shotgun_globals = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_globals",
)

task_manager = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "task_manager",
)

class DetailsPanelWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        """
        Constructor

        :param parent:  The panel's parent widget.
        """
        QtGui.QWidget.__init__(self, parent)

        self._pinned = False
        self._requested_entity = None

        self.ui = Ui_DetailsPanelWidget() 
        self.ui.setupUi(self)

        self.version_delegate = ListItemDelegate(
            parent=self.ui.entity_version_view,
            fields=["user","sg_status_list"],
        )

        self._fields = [
            "code",
            "entity",
            "image",
            "user",
            "sg_status_list",
        ]

        self.version_model = shotgun_model.SimpleShotgunModel(self.ui.entity_version_tab)
        self.ui.entity_version_view.setModel(self.version_model)
        self.ui.entity_version_view.setItemDelegate(self.version_delegate)

        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self.ui.note_stream_widget,
            start_processing=True,
            max_threads=2,
        )

        shotgun_globals.register_bg_task_manager(self._task_manager)

        self.ui.note_stream_widget.set_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.allow_screenshots = False
        self.ui.note_stream_widget.show_sg_stream_button = False
        self.shot_info_model = shotgun_model.SimpleShotgunModel(self.ui.note_stream_widget)

        si_size = ListItemWidget.calculate_size()
        self.ui.shot_info_widget.setMaximumSize(
            QtCore.QSize(si_size.width(), si_size.height())
        )

        # For the basic info widget in the Notes stream we won't show
        # labels for the fields we're including.
        self.ui.shot_info_widget.show_labels = False

        # Signal handling.
        self.ui.pin_button.toggled.connect(self._set_pinned)
        self.ui.shotgun_nav_button.clicked.connect(
            self.ui.note_stream_widget._load_shotgun_activity_stream
        )

    def load_data(self, entity):
        """
        Loads the given Shotgun entity into the details panel,
        triggering the notes and versions streams to be updated
        relative to the given entity.

        :param entity:  The Shotgun entity to load. This is a dict in
                        the form returned by the Shotgun Python API.
        """
        # If we're pinned, then we don't allow loading new entities.
        if not self._pinned:
            self.ui.note_stream_widget.load_data(entity)

            shot_filters = [["id", "is", entity["id"]]]
            self.shot_info_model.load_data(
                entity_type="Version",
                filters=shot_filters,
                fields=self._fields,
            )

            sg_data = self.shot_info_model.item_from_entity(
                "Version",
                entity["id"]
            ).get_sg_data()

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
        """
        Sets the "pinned" state of the details panel. When the panel is
        pinned it will not accept updates. It will, however, record the
        most recent entity passed to load_data that was not accepted. If
        the panel is unpinned at a later time, the most recent rejected
        entity update will be executed at that time.

        :param checked: True or False
        """
        self._pinned = checked

        if checked:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_hover.png"))
        else:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_up.png"))
            if self._requested_entity:
                self.load_data(self._requested_entity)
                self._requested_entity = None

