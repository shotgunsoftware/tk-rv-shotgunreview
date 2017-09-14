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
from sgtk.platform.qt import QtCore, QtGui

import pprint
pp = pprint.PrettyPrinter(indent=4)

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel


class TrayModel(ShotgunModel):

    # signal which gets emitted whenever the model has been updated with fresh FILTERED data.
    filter_data_refreshed = QtCore.Signal(bool)

    def __init__(self, parent, bg_task_manager=None, engine=None):

        ShotgunModel.__init__(self, 
                  parent = parent,
                  download_thumbs = True,
                  schema_generation = 0,
                  bg_load_thumbs = True,
                  bg_task_manager = bg_task_manager)

        self._parent = parent
        self._engine = engine

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
        self._version_order = []

    @property
    def version_order(self):
        """
        Used to store a list of version ids in the order that the Versions
        should be presented in the tray. This property is only used when
        Version entities are loaded into SG Review directly -- if cuts or
        playlists are loaded up, the orders defined in those entities are
        used instead.

        :returns: A list of integer Version entity ids.
        :rtype: list
        """
        return self._version_order

    @version_order.setter
    def version_order(self, version_ids):
        self._version_order = version_ids

    def clear_pinned_items(self):
        self._pinned_items = {}        

    def update_pinned_items(self, pinned_list):
        loop_dict = pinned_list

        if not pinned_list:
            loop_dict = self._pinned_items

        for shot_key in loop_dict:
            if shot_key not in self._pinned_items:
                self._engine.log_warning( "WARNING!!! NO PATH FOR Shot %r THUMBNAIL IN TRAY _pinned_items." % shot_key )
            else:
                path = self._pinned_items[shot_key]
                if path:
                    rows = self.rowCount()
                    for x in range(0, rows):
                        index = self.index(x, 0)
                        sg = shotgun_model.get_sg_data(index)
                        if sg['type'] == "CutItem":
                            if 'shot' in sg and sg['shot']:
                                if sg['shot']['id'] == int(shot_key):
                                    self.setData(index, path, self._PINNED_THUMBNAIL)
                        elif sg['type'] == "Version":
                            if 'entity' in sg and sg['entity']:
                                if sg['entity']['id'] == int(shot_key):
                                    self.setData(index, path, self._PINNED_THUMBNAIL)
                        else:
                            self._engine.log_warning( "type %r not currently handled in update_pinned_items." % sg['type'] )

        # i think after running update it is safe to clear out the pinned items
        self.clear_pinned_items()


    def set_pinned_items(self, pinned_list):
 
        loop_dict = pinned_list
        if not pinned_list:
            loop_dict = self._pinned_items
 
        for shot_key in loop_dict.keys():
            rows = self.rowCount()
            for x in range(0, rows):
                index = self.index(x, 0)
                sg = shotgun_model.get_sg_data(index)
                try:
                    if sg['type'] == "CutItem":
                        if 'shot' in sg and sg['shot']:
                            if sg['shot']['id'] == int(shot_key):
                                if shot_key in self._pinned_items and self._pinned_items[shot_key]:
                                    self.setData(index, self._pinned_items[shot_key], self._PINNED_THUMBNAIL)

                                path = index.data(self._PINNED_THUMBNAIL)
                                if not path:
                                    path = index.data(self._ORIGINAL_THUMBNAIL)
                                self._pinned_items[shot_key] = path
                        else:
                            self._engine.log_warning('CutItem %d has no shot. Ignoring.' % sg['id'])
                    elif sg['type'] == "Version":
                        if 'entity' in sg and sg['entity']:
                            if sg['entity']['id'] == int(shot_key) and sg['entity']['type'] == "Shot":
                                if shot_key in self._pinned_items and self._pinned_items[shot_key]:
                                    self.setData(index, self._pinned_items[shot_key], self._PINNED_THUMBNAIL)
                                else:
                                    path = index.data(self._PINNED_THUMBNAIL)
                                    if not path:
                                        path = index.data(self._ORIGINAL_THUMBNAIL)
                                    self._pinned_items[shot_key] = path

                    else:
                        self._engine.log_warning( "type %r not currently handled in add_pinned_item." % sg['type'] )
                except Exception as e:
                    self._engine.log_error( "set_pinned_items: %r" % e)


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

            if sg['type'] == "Version" and 'entity' in sg and sg['entity']:
                if shot_id == sg['entity']['id']:
                    self._pinned_items[str(shot_id)] = path
 
            if sg['type'] == "CutItem":
                if 'shot' in sg and sg['shot']:
                    if shot_id == sg['shot']['id']:
                        self._pinned_items[str(shot_id)] = path
                else:
                    if 'version.Version.entity' in sg and sg['version.Version.entity']:
                        if shot_id == sg['version.Version.entity']['id']:
                            print "WARNING: shot is None, version has matching entity but not using it."

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
                if sg['shot'] and sg['shot']['id'] == shot['id']:
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
        Called when an item is created to set its tooltip. The given Cut entity
        provides information used to construct the item's tooltip such that it
        matches that shown in Shotgun's Media app, and includes the version name,
        version status, linked entity type, and linked entity name.

        :param item: Shotgun model item that requires a tooltip.
        :param sg_item: Dictionary of the entity associated with the Shotgun model item.
        """
        entity_type = sg_item.get("type")

        if entity_type == "CutItem":
            prefix = "version.Version."
        else:
            prefix = ""

        version_name = sg_item.get(prefix + "code", "[Unknown Version Name]")
        version_status = sg_item.get(prefix + "sg_status_list", None)
        linked_entity = sg_item.get(prefix + "entity", dict())
        if linked_entity:
                linked_entity_type = linked_entity.get("type", "[Unknown Linked Entity Type]")
                linked_entity_name = linked_entity.get("name", "[Unknown Linked Entity Name]")
        else:
                linked_entity_type = "[No Linked Entity]"
                linked_entity_name = "[No Linked Entity]"

        if version_status is None:
            version_status = "[Unknown Version Status]"
        else:
            version_status = self._shotgun_globals.get_status_display_name(version_status)

        item.setToolTip(
            "Version %s with status \"%s\" on %s %s" % (
                version_name,
                version_status,
                linked_entity_type,
                linked_entity_name
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

