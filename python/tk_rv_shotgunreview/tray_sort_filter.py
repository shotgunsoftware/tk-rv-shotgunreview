# Copyright (c) 2017 Shotgun Software Inc.
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

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

class TraySortFilter(QtGui.QSortFilterProxyModel):
    def lessThan(self, left, right):
        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)

        if 'cut_order' in sg_left and 'cut_order' in sg_right:
            return sg_left['cut_order'] < sg_right['cut_order']
        elif 'playlists.PlaylistVersionConnection.sg_sort_order' in sg_left and 'playlists.PlaylistVersionConnection.sg_sort_order' in sg_right:
                if sg_left['playlists.PlaylistVersionConnection.sg_sort_order'] == sg_right['playlists.PlaylistVersionConnection.sg_sort_order']:
                        return sg_left['playlists.PlaylistVersionConnection.id'] < sg_right['playlists.PlaylistVersionConnection.id']
                        
                return sg_left['playlists.PlaylistVersionConnection.sg_sort_order'] < sg_right['playlists.PlaylistVersionConnection.sg_sort_order']
        elif sg_left.get("type") == "Version" and sg_right.get("type") == "Version":
            # If we're dealing with Version entities, then we will make use
            # of the version_order property of our sourceModel. That gets
            # set by the rv_activity_mode when Version entities are being
            # loaded into the tray, and represents the order of the Versions
            # exactly as they were given to RV on launch.
            model = self.sourceModel()
            order = model.version_order
            left_id = sg_left.get("id")
            right_id = sg_right.get("id")

            if left_id in order and right_id in order:
                return order.index(left_id) < order.index(right_id)
            else:
                # Maintain order if we don't know enough to change it.
                return True
        else:
            return True


    # JS for playlist sorting 
    # https://github.com/shotgunsoftware/shotgun/blob/develop/cut_support_2016/public/javascripts/review_app/review_app_data_manager.js#L430

    # get_playlist_sorts: function() {
    #     return [
    #         { column: 'playlists.PlaylistVersionConnection.sg_sort_order', direction: 'asc' },
    #         { column: 'playlists.PlaylistVersionConnection.id', direction: 'asc' }
    #     ];
    # },