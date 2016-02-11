

# import the shotgun_model module from the shotgun utils framework
import tank

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel

class TrayModel(SimpleShotgunModel):

        def __init__(self, parent, bg_task_manager=None):
                SimpleShotgunModel.__init__(self, parent)

        def load_data(self, entity_type, filters=None, fields=None, hierarchy=None, order=None):
                filters = filters or []
                fields = fields or ["code"]
                hierarchy = hierarchy or [fields[0]]
                ShotgunModel._load_data(self, entity_type, filters, hierarchy, fields, order)
                self._refresh_data()
