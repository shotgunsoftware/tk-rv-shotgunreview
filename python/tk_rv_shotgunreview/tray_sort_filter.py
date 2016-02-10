# import the shotgun_model module from the shotgun utils framework
import tank
from tank.platform.qt import QtCore, QtGui

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel

class TraySortFilter(QtGui.QSortFilterProxyModel):

        def lessThan(self, left, right):

                sg_left = shotgun_model.get_sg_data(left)
                sg_right = shotgun_model.get_sg_data(right)
                return sg_left['sg_cut_order'] < sg_right['sg_cut_order']