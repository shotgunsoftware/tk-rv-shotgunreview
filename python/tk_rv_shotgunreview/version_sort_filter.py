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

shotgun_globals = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_globals",
)

class VersionSortFilterProxyModel(QtGui.QSortFilterProxyModel):
    """
    A sort/filter proxy model that handles sorting and filtering
    data in a ShotgunModel by given Shotgun fields on the entities
    stored therein.

    :ivar filter_by_fields: A list of string Shotgun field names to filter on.
    :ivar sort_by_field:    A string Shotgunfield name to sort by.
    """
    def __init__(self, parent, filter_by_fields, sort_by_field):
        """
        Initializes a new VersionSortFilterProxyModel.

        :param parent:              The Qt parent of the proxy model.
        :param filter_by_fields:    A list of string Shotgun field names
                                    to filter on.
        :param sort_by_field:       A string Shotgun field name to sort
                                    by.
        """
        super(VersionSortFilterProxyModel, self).__init__(parent)

        self.filter_by_fields = list(filter_by_fields)
        self.sort_by_field = sort_by_field

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

    def filterAcceptsRow(self, row, source_parent):
        """
        Returns True if the model index should be shown, and False
        if it should not. This is determined based on whether the
        proxy model's filter is found in the Shotgun data for
        the fields specified in the filter_by_fields list registered
        with the proxy model.

        :param row:             The row being processed.
        :param source_parent:   The parent index from the source model.
        """
        if not self.filter_by_fields:
            return True

        # We only have one column, so column 0 is what we're
        # after.
        sg_data = shotgun_model.get_sg_data(
            self.sourceModel().index(row, 0, source_parent),
        )

        if not sg_data:
            return True

        for field in self.filter_by_fields:
            # We will attempt to detect bubble fields and also check those
            # to see if it's an entity and handle it appropriately.
            if "." in field:
                (field_entity_type, short_name) = field.split(".")[-2:]
            else:
                (field_entity_type, short_name) = ("Version", field)

            data_type = shotgun_globals.get_data_type(field_entity_type, short_name)

            try:
                # If this is an entity field, then we'll attempt to take the
                # name from that and match against it. If not, we take the
                # data as is and stringify it before matching.
                #
                # TODO: Do we need to make this more robust? There might be
                # other complex data types that won't behave as expected with
                # the simple stringify here.
                if data_type == "entity":
                    match_data = sg_data[field]["name"]
                else:
                    match_data = sg_data[field]

                # We'll make this a looser match by making it case insensitive
                # and bounding it with wildcards. This makes using the search
                # feature much more like a "search" and less like a regex
                # experiment.
                regex = self.filterRegExp()
                regex.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                regex.setPattern("*%s*" % regex.pattern())

                if regex.exactMatch(str(match_data)):
                    return True
            except KeyError:
                pass

        return False
