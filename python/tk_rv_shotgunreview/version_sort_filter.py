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

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class VersionSortFilterProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent, filter_by_fields, sort_by_field, filter_value=None):
        super(VersionSortFilterProxyModel, self).__init__(parent)

        self.filter_by_fields = list(filter_by_fields)
        self.sort_by_field = sort_by_field
        self.filter_value = filter_value

    def lessThan(self, left, right):
        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)

        try:
            return sg_left[self.sort_by_field] is sorted(
                [
                    sg_left[self.sort_by_field],
                    sg_right[self.sort_by_field],
                ]
            )[0]
        except KeyError:
            return True

    def filterAcceptsRow(self, row, model_index):
        if not self.filter_value or not self.filter_by_fields:
            return True

        sg_data = shotgun_model.get_sg_data(model_index)

        for field in self.filter_by_fields:
            try:
                if self.filter_value in sg_data[field]:
                    return True
            except KeyError:
                pass

        return False
