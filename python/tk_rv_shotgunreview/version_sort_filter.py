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
    """
    A sort/filter proxy model that handles sorting and filtering
    data in a ShotgunModel by given Shotgun fields on the entities
    stored therein.

    :ivar filter_by_fields: A list of string Shotgun field names to filter on.
    :ivar sort_by_field:    A string Shotgunfield name to sort by.
    :ivar filter_value:     A string to check against the filter_by_fields data
                            when filtering.
    """
    def __init__(self, parent, filter_by_fields, sort_by_field, filter_value=None):
        """
        Initializes a new VersionSortFilterProxyModel.

        :param parent:              The Qt parent of the proxy model.
        :param filter_by_fields:    A list of string Shotgun field names
                                    to filter on.
        :param sort_by_field:       A string Shotgun field name to sort
                                    by.
        :param filter_value:        A string to check against the filter_by_fields
                                    data when filtering.
        """
        super(VersionSortFilterProxyModel, self).__init__(parent)

        self.filter_by_fields = list(filter_by_fields)
        self.sort_by_field = sort_by_field
        self.filter_value = filter_value

    def lessThan(self, left, right):
        """
        Returns True if "left" is less than "right", otherwise
        False. This sort is handled based on the data pulled from
        Shotgun for the current sort_by_field registered with this
        proxy model.

        :param left:    The QModelIndex of the left-hand item to
                        compare.
        :param right:   The QModelIndex of the right-hand item to
                        compare against.
        """
        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)

        # This might be overkill, because we could be calling
        # the base class' lessThan method, which supports sorting
        # a number of different data types. However, we're dealing
        # with a lot of different types of fields, including some
        # that might not exist as of this writing, and we can't
        # guarantee that all data pulled from Shotgun will be
        # supported by the base-level lessThan. As such, we'll
        # let Python handle the sorting and use the results of
        # that, which should work with a wider variety of data
        # types.
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
        """
        Returns True if the model index should be shown, and False
        if it should not. This is determined based on whether the
        proxy model's filter_value is found in the Shotgun data for
        the fields specified in the filter_by_fields list registered
        with the proxy model.

        :param row:         The row being processed.
        :param model_index: The QModelIndex of the item being processed.
        """
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
