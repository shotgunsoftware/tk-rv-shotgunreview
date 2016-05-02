# import the shotgun_model module from the shotgun utils framework
import tank
from tank.platform.qt import QtCore, QtGui

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

class StepsSortFilter(QtGui.QSortFilterProxyModel):
   
    def lessThan(self, left, right):

        sg_left = shotgun_model.get_sg_data(left)
        sg_right = shotgun_model.get_sg_data(right)
        if 'list_order' in sg_left and 'list_order' in sg_right:
            return sg_left['list_order'] < sg_right['list_order']
        else:
            return 1