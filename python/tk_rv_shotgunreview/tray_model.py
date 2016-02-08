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

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class TrayModel(shotgun_model.SimpleShotgunModel):
    def __init__(self, parent, bg_task_manager=None):
        shotgun_model.SimpleShotgunModel.__init__(self, parent)

    def load_data(self, entity_type, filters=None, fields=None, hierarchy=None):
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = hierarchy or [fields[0]]
        shotgun_model.ShotgunModel._load_data(
            self,
            entity_type,
            filters,
            hierarchy,
            fields,
        )
        self._refresh_data()
