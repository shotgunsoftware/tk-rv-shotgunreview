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
from .version_list_delegate import RvVersionListDelegate
from .shot_info_delegate import RvShotInfoDelegate
from .shot_info_widget import ShotInfoWidget

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
        
        # set up the UI
        self.ui = Ui_DetailsPanelWidget() 
        self.ui.setupUi(self)

        self.version_delegate  = RvVersionListDelegate(self.ui.entity_version_view)
        self.version_model = shotgun_model.SimpleShotgunModel(self.ui.entity_version_tab)

        # Tell the view to pull data from the model
        self.ui.entity_version_view.setModel(self.version_model)
        self.ui.entity_version_view.setItemDelegate(self.version_delegate)

        task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")
        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self.ui.note_stream_widget,
            start_processing=True,
            max_threads=2,
        )
        
        shotgun_globals = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")
        shotgun_globals.register_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.set_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.allow_screenshots = False

        self.shot_info_model = shotgun_model.SimpleShotgunModel(self.ui.note_stream_widget)
        self.ui.entity_details_view.setModel(self.shot_info_model)

        self.shot_info_delegate = RvShotInfoDelegate(self.ui.entity_details_view)
        self.ui.entity_details_view.setItemDelegate(self.shot_info_delegate)

        self.ui.entity_details_view.setMinimumSize(ShotInfoWidget.calculate_size())
        si_size = ShotInfoWidget.calculate_size()
        self.ui.entity_details_view.setMaximumSize(QtCore.QSize(si_size.width() + 10, si_size.height() + 10))

    def load_data(self, entity):
        self.ui.note_stream_widget.load_data(entity)
        shot_filters = [['id','is', entity['id']]]
        self.shot_info_model.load_data(entity_type="Version", filters=shot_filters)

