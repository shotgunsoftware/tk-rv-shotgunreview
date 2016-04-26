# import the shotgun_model module from the shotgun utils framework
import tank
from PySide import QtCore

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel


class RelCutsModel(SimpleShotgunModel):

    def __init__(self, parent, bg_task_manager=None):
        SimpleShotgunModel.__init__(self, parent)
        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138

    def load_data(self, entity_type, filters=None, fields=None, hierarchy=None, order=None):
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = hierarchy or [fields[0]]
        ShotgunModel._load_data(self, entity_type, filters, hierarchy, fields, order)
        self._refresh_data()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

