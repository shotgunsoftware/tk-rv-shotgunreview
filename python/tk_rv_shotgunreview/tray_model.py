

# import the shotgun_model module from the shotgun utils framework
import tank
from PySide import QtCore, QtGui

import pprint
pp = pprint.PrettyPrinter(indent=4)


shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel

class TrayModel(ShotgunModel):

    # signal which gets emitted whenever the model has been updated with fresh FILTERED data.
    filter_data_refreshed = QtCore.Signal(bool)

    def __init__(self, parent, bg_task_manager=None):

        ShotgunModel.__init__(self, 
                  parent = parent,
                  download_thumbs = True,
                  schema_generation = 0,
                  bg_load_thumbs = True,
                  bg_task_manager = bg_task_manager)

        self._parent = parent

        # this holds alternate version data
        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138
        
        # this is actual pixmap data - XXX do we need it?
        self._CUT_THUMB_ROLE = QtCore.Qt.UserRole + 1701

        # these hold the URL of where you can get the thumbnail from
        # which for us SHOULD come from the cache.
        # the cache will translate the URL into a path on disk and we can
        # build the icon from that.
        # XXX - sb - is there any S3 timout worry here?
        self._ORIGINAL_THUMBNAIL = QtCore.Qt.UserRole + 1702
        self._FILTER_THUMBNAIL = QtCore.Qt.UserRole + 1703
        self._PINNED_THUMBNAIL = QtCore.Qt.UserRole + 1704

        self._pinned_items = {}

    def clear_pinned_items(self):
        self._pinned_items = {}        

    def update_pinned_items(self, pinned_list):

        if not pinned_list:
            return

        for shot_key in pinned_list:
            if shot_key not in self._pinned_items:
                print "WARNING!!! NO PATH FOR Shot %r THUMBNAIL IN TRAY _pinned_items." % shot_key
            else:
                path = self._pinned_items[shot_key]
                if path:
                    rows = self.rowCount()
                    for x in range(0, rows):
                        index = self.index(x, 0)
                        sg = shotgun_model.get_sg_data(index)
                        if sg['type'] == "CutItem":
                            if 'version.Version.entity' in sg and sg['version.Version.entity']:
                                if sg['version.Version.entity']['id'] == int(shot_key):
                                    self.setData(index, path, self._PINNED_THUMBNAIL)
                        else:
                            print "ITS NOT A CUT - WHAT DO WE WANT TO DO?"
                            pp.pprint(sg)


    def set_pinned_items(self, pinned_list):
        if not pinned_list:
            return
 
        for shot_key in pinned_list.keys():
            rows = self.rowCount()
            for x in range(0, rows):
                index = self.index(x, 0)
                sg = shotgun_model.get_sg_data(index)
                if sg['type'] == "CutItem":
                    if 'version.Version.entity' in sg and sg['version.Version.entity']:
                        if sg['version.Version.entity']['id'] == int(shot_key):
                            
                            if shot_key in self._pinned_items and self._pinned_items[shot_key]:
                                self.setData(index, self._pinned_items[shot_key], self._PINNED_THUMBNAIL)

                            path = index.data(self._PINNED_THUMBNAIL)
                            if not path:
                                path = index.data(self._ORIGINAL_THUMBNAIL)
                            self._pinned_items[shot_key] = path
                else:
                    print "ITS NOT A CUT - WHAT DO WE WANT TO DO?"
                    pp.pprint(sg)


    def add_pinned_item(self, version_data):

        # we expect a RV style version data dict, which
        # should also contain __image_path for us
        # to push into _PINNED_THUMBNAIL
        #
        # maybe we dont need an image path as in this
        # case we want ORIGINAL path to be copied into
        # this dict
        if not version_data:
            return

        shot_id = int(version_data.keys()[0])
 
        rows = self.rowCount()
        for x in range(0, rows):
            index = self.index(x, 0)
            sg = shotgun_model.get_sg_data(index)
            orig_path = index.data(self._ORIGINAL_THUMBNAIL)
            pinned_path = index.data(self._PINNED_THUMBNAIL)
            filtered_path = index.data(self._FILTER_THUMBNAIL)
            path = orig_path

            if pinned_path:
                path = pinned_path
            if filtered_path and not pinned_path:
                path = filtered_path
            

            image_dict = {}

            if sg['type'] == "Version" and 'entity' in sg:
                if shot_id == sg['entity']['id']:
                    self._pinned_items[str(shot_id)] = path

            if sg['type'] == "CutItem":
                if 'shot' in sg and sg['shot']:
                    if shot_id == sg['shot']['id']:
                        self._pinned_items[str(shot_id)] = path
                else:
                    if 'version.Version.entity' in sg:
                        if shot_id == sg['version.Version.entity']['id']:
                            path = index.data(self._ORIGINAL_THUMBNAIL)
                            self._pinned_items[str(shot_id)] = path
            

    def notify_filter_data_refreshed(self, modified=True):
        self.filter_data_refreshed.emit(modified)

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

    def swap_in_thumbnail(self, item, field, image, path=None):
        """
        The params coming into this function are from ANOTHER MODEL!
        To do the actual swap out, we look at the SG data from the other
        model, find the matching shot in this model, and then set the
        thumbnail in this model with the other models data.
        """

        sgv = item.data(self.SG_DATA_ROLE)
        shot = sgv['entity']

        rows = self.rowCount()
        for x in range(0, rows):
            m_idx = self.index(x, 0)
            sg = m_idx.data(self.SG_DATA_ROLE)
            if 'shot' in sg:
                if sg['shot']['id'] == shot['id']:
                    t_item = self.itemFromIndex(m_idx)
                    if not image:
                        # we have no image, then revert to the one we stored on load 
                        thumb = m_idx.data(self._CUT_THUMB_ROLE)
                        t_item.setIcon(thumb)
                    else:
                        thumb = QtGui.QPixmap.fromImage(image)
                        t_item.setIcon(thumb)

                    # None here means dont use it. empty string better?
                    t_item.setData(path, self._FILTER_THUMBNAIL)



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
        sg = item.data(self.SG_DATA_ROLE)

        # XXX - having no 'shot' key means that the incoming query was for a
        # version or playlist, so we want the version image - sb
        if 'shot' not in sg:
            super(TrayModel, self)._request_thumbnail_download(item, 'image', sg['image'], 'Version', sg['id'])
            return

        if sg['image']: # the Cut Item image
            super(TrayModel, self)._request_thumbnail_download(item, 'image', sg['image'], 'CutItem', sg['id'])
            return

        if sg['version.Version.image']: # the Cut Item's Version image
            super(TrayModel, self)._request_thumbnail_download(item, 'version.Version.image', sg['version.Version.image'], 'Version', sg['version.Version.id'])
            return

        if sg['cut.Cut.image']: # the Cut image
            super(TrayModel, self)._request_thumbnail_download(item, 'cut.Cut.image', sg['cut.Cut.image'], 'Cut', sg['cut.Cut.id'])
            return

        if sg['cut.Cut.version.Version.image']: # the Cut's Version image
            super(TrayModel, self)._request_thumbnail_download(item, 'cut.Cut.version.Version.image', sg['cut.Cut.version.Version.image'], 'Version', sg['cut.Cut.version.Version.id'])
            return


    def _populate_thumbnail_image(self, item, field, image, path):
        """
        Similar to :meth:`_populate_thumbnail()` but this method is called instead
        when the bg_load_thumbs parameter has been set to true. In this case, no
        loading of thumbnail data from disk is necessary - this has already been
        carried out async and is passed in the form of a QImage object.

        For further details, see :meth:`_populate_thumbnail()`

        :param item: :class:`~PySide.QtGui.QStandardItem` which is associated with the given thumbnail
        :param field: The Shotgun field which the thumbnail is associated with.
        :param image: QImage object with the thumbnail loaded
        :param path: A path on disk to the thumbnail. This is a file in jpeg format.

        this happens on model loading... so we store the incoming thumbnail away to use
        when we need to revert to original thumbnail.
        """
        thumb = QtGui.QPixmap.fromImage(image)
        item.setData(thumb, self._CUT_THUMB_ROLE)
        item.setData(path, self._ORIGINAL_THUMBNAIL)
        item.setIcon(thumb)

