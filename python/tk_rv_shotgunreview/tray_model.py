

# import the shotgun_model module from the shotgun utils framework
import tank
from PySide import QtCore

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

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def _set_tooltip(self, item, sg_item):
        """
        Called when an item is created.

        .. note:: You can subclass this if you want to set your own tooltip for the model item. By
            default, the SG_ASSOCIATED_FIELD_ROLE data is retrieved and the field name is used to
            determine which field to pick tooltip information from.

            For example,

            .. code-block:: python

               {
                   "type": "Task",
                   "entity": {                       # (1) Tooltip becomes "Asset 'Alice'"
                       "sg_asset_type": "Character", # (2) Tooltip becomes "Asset Type 'Character'"
                       "type": "Asset",
                       "code": "Alice"
                   },
                   "content": "Art"                  # (3) Tooltip becomes "Task 'Art'"
               }

            1) If the field is an entity (e.g. entity), then the display name of that entity's type
            will be used.

            2) If the field is part of a sub-entity (e.g entity.Asset.sg_asset_type), the display
            name of the sub-entity's type followed by a space and the sub-entity's field display name
            will be used.

            3) If the field is part of an entity and not an entity field(e.g. content), the display
            name of the entity's type will be used.

            In all cases, the string ends with the quoted name of the ShotgunStandardItem.

        :param item: Shotgun model item that requires a tooltip.
        :param sg_item: Dictionary of the entity associated with the Shotgun model item.
        """

        data = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
        field = data["name"]
        print "SGDATA: %r" % sg_item
        if isinstance(sg_item[field], dict) and "type" in sg_item[field]:
            # This is scenario 1 described above.
            item.setToolTip(
                "%s '%s'" % (
                    self._shotgun_globals.get_type_display_name(sg_item[field]["type"]),
                    item.text()
                )
            )
        elif "." in field:
            # This is scenario 2 described above.
            _, sub_entity_type, sub_entity_field_name = field.split(".")
            item.setToolTip(
                "%s %s '%s'" % (
                    self._shotgun_globals.get_type_display_name(sub_entity_type),
                    self._shotgun_globals.get_field_display_name(sub_entity_type, sub_entity_field_name),
                    item.text()
                )
            )
        else:
            # This is scenario 3 described above.
            item.setToolTip(
                "%s '%s'" % (
                    self._shotgun_globals.get_type_display_name(sg_item["type"]),
                    item.text()
                )
            )


    def _request_thumbnail_download(self, item, field, url, entity_type, entity_id):
        """
        Request that a thumbnail is downloaded for an item. If a thumbnail is successfully
        retrieved, either from disk (cached) or via shotgun, the method _populate_thumbnail()
        will be called. If you want to control exactly how your shotgun thumbnail is
        to appear in the UI, you can subclass this method. For example, you can subclass
        this method and perform image composition prior to the image being added to
        the item object.

        .. note:: This is an advanced method which you can use if you want to load thumbnail
            data other than the standard 'image' field. If that's what you need, simply make
            sure that you set the download_thumbs parameter to true when you create the model
            and standard thumbnails will be automatically downloaded. This method is either used
            for linked thumb fields or if you want to download thumbnails for external model data
            that doesn't come from Shotgun.

        :param item: :class:`~PySide.QtGui.QStandardItem` which belongs to this model
        :param field: Shotgun field where the thumbnail is stored. This is typically ``image`` but
                      can also for example be ``sg_sequence.Sequence.image``.
        :param url: thumbnail url
        :param entity_type: Shotgun entity type
        :param entity_id: Shotgun entity id
        """
        super(TrayModel, self)._request_thumbnail_download(item, 'version.Version.image', url, entity_type, entity_id)