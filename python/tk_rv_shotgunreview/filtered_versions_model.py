# import the shotgun_model module from the shotgun utils framework
import tank
from sgtk.platform.qt import QtCore, QtGui

shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
SimpleShotgunModel = shotgun_model.SimpleShotgunModel
ShotgunModel = shotgun_model.ShotgunModel


class FilteredVersionsModel(ShotgunModel):

    def __init__(self, parent, bg_task_manager=None, tray_model=None):

        ShotgunModel.__init__(self, 
                  parent = parent,
                  download_thumbs = True,
                  schema_generation = 0,
                  bg_load_thumbs = True,
                  bg_task_manager = bg_task_manager)


        self._tray_model = tray_model

        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138

    def load_data(self, entity_type, filters=None, fields=None, hierarchy=None, order=None, additional_filter_presets=None):
        filters = filters or []
        fields = fields or ["code"]
        hierarchy = hierarchy or [fields[0]]
        ShotgunModel._load_data(self, entity_type, filters, hierarchy, fields, order, None, None, None, additional_filter_presets)
        self._refresh_data()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


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
        # XXX this actually is default behavior, but if the query changes this might need additional logic.
        sg = item.data(self.SG_DATA_ROLE)
        super(FilteredVersionsModel, self)._request_thumbnail_download(item, 'image', sg['image'], 'Version', sg['id'])


    def _populate_item(self, item, sg_data):
        """
        Whenever an item is downloaded from Shotgun, this method is called. It allows subclasses to intercept
        the construction of a :class:`~PySide.QtGui.QStandardItem` and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.

        This method is called before the item is added into the model tree. At the point when
        the item is added into the tree, various signals will fire, informing views and proxy
        models that a new item has been added. This methods allows a subclassing object to
        add custom data prior to this.

        .. note:: When an item is fetched from the cache, this method is *not* called, it will
            only be called when shotgun data initially arrives from a Shotgun API query.

        .. note:: This is typically subclassed if you retrieve additional fields alongside the standard "name" field
            and you want to put those into various custom data roles. These custom fields on the item
            can later on be picked up by custom (delegate) rendering code in the view.

        :param item: :class:`~PySide.QtGui.QStandardItem` that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in _load_data()
        """
        # default implementation does nothing
        # this one doesnt get called....

    def _populate_default_thumbnail(self, item):
        """
        Called whenever an item is constructed and needs to be associated with a default thumbnail.
        In the current implementation, thumbnails are not cached in the same way as the rest of
        the model data, meaning that this method is executed each time an item is constructed,
        regardless of if it came from an asynchronous shotgun query or a cache fetch.

        The purpose of this method is that you can subclass it if you want to ensure that items
        have an associated thumbnail directly when they are first created.

        Later on in the data load cycle, if the model was instantiated with the
        `download_thumbs` parameter set to True,
        the standard Shotgun ``image`` field thumbnail will be automatically downloaded for all items (or
        picked up from local cache if possible). When these real thumbnails arrive, the
        meth:`_populate_thumbnail()` method will be called.

        :param item: :class:`~PySide.QtGui.QStandardItem` that is about to be added to the model.
            This has been primed with the standard settings that the ShotgunModel handles.
        """
        # the default implementation does nothing
        # XXX this does get called but kinda useless here... as there is no view attached
        pass


    def _populate_thumbnail(self, item, field, path):
        """
        Called whenever the real thumbnail for an item exists on disk. The following
        execution sequence typically happens:

        - :class:`~PySide.QtGui.QStandardItem` is created, either through a cache load from disk or
          from a payload coming from the Shotgun API.
        - After the item has been set up with its associated Shotgun data,
          :meth:`_populate_default_thumbnail()` is called, allowing client code to set
          up a default thumbnail that will be shown while potential real thumbnail
          data is being loaded.
        - The model will now start looking for the real thumbail.
        - If the thumbnail is already cached on disk, :meth:`_populate_thumbnail()` is called very soon.
        - If there isn't a thumbnail associated, :meth:`_populate_thumbnail()` will not be called.
        - If there isn't a thumbnail cached, the model will asynchronously download
          the thumbnail from Shotgun and then (after some time) call :meth:`_populate_thumbnail()`.

        This method will be called for standard thumbnails if the model has been
        instantiated with the download_thumbs flag set to be true. It will be called for
        items which are associated with shotgun entities (in a tree data layout, this is typically
        leaf nodes). It will also be called once the data requested via _request_thumbnail_download()
        arrives.

        This method makes it possible to control how the thumbnail is applied and associated
        with the item. The default implementation will simply set the thumbnail to be icon
        of the item, but this can be altered by subclassing this method.

        :param item: :class:`~PySide.QtGui.QStandardItem` which is associated with the given thumbnail
        :param field: The Shotgun field which the thumbnail is associated with.
        :param path: A path on disk to the thumbnail. This is a file in jpeg format.
        """
        # the default implementation sets the icon
        # XXX does not get called... but if it does...
        self._tray_model.swap_in_thumbnail(item, field, image, path)
 
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
        """
        # XXX we use this one
        # call the tray model with the data in this model to update the thumbnail there.
        self._tray_model.swap_in_thumbnail(item, field, image, path)
