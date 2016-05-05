# import the shotgun_model module from the shotgun utils framework
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
        else:
            return 1


    # JS for playlist sorting 
    # https://github.com/shotgunsoftware/shotgun/blob/develop/cut_support_2016/public/javascripts/review_app/review_app_data_manager.js#L430

    # get_playlist_sorts: function() {
    #     return [
    #         { column: 'playlists.PlaylistVersionConnection.sg_sort_order', direction: 'asc' },
    #         { column: 'playlists.PlaylistVersionConnection.id', direction: 'asc' }
    #     ];
    # },