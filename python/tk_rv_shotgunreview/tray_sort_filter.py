# import the shotgun_model module from the shotgun utils framework
import tank
from tank.platform.qt import QtCore, QtGui

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
#SimpleShotgunModel = shotgun_model.SimpleShotgunModel
#ShotgunModel = shotgun_model.ShotgunModel

class TraySortFilter(QtGui.QSortFilterProxyModel):

    #playhead_moved = QtCore.Signal(dict)
    
    def lessThan(self, left, right):

        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)
        #print "SORT: %d %d" % (sg_left['cut_order'], sg_right['cut_order'])
        if 'cut_order' in sg_left and 'cut_order' in sg_right:
            return sg_left['cut_order'] < sg_right['cut_order']
        else:
            return 1