# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank.platform.qt import QtCore, QtGui

from .list_item_widget import ListItemWidget

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class ListItemDelegate(shotgun_view.EditSelectedWidgetDelegate):
    def __init__(
        self, view, fields=None, show_labels=True, show_borders=True, 
        shotgun_field_manager=None, label_exempt_fields=None, **kwargs):
        """
        Constructs a new ListItemDelegate.

        :param view:                    The parent view for this delegate.
        :param fields:                  A list of Shotgun entity fields to be displayed.
        :param show_labels:             Whether to show labels for the fields being displayed.
        :param show_borders:            Whether to draw borders around each item.
        :param shotgun_field_manager:   An option ShotgunFieldManager object to pass to any
                                        ListItemWidgets that are constructed.
        :param label_exempt_fields:     A list of field names that are exempt from having
                                        labels displayed.
        """
        shotgun_view.EditSelectedWidgetDelegate.__init__(self, view)

        self.fields = fields

        self._widget_cache = dict()
        self._show_labels = show_labels
        self._label_exempt_fields = label_exempt_fields
        self._show_borders = show_borders
        self._shotgun_field_manager = shotgun_field_manager
        self._current_editor = None

    def add_field(self, field):
        """
        Adds the given field to the list of fields to display for the entity.

        :param field:   The name of the Shotgun field to add to the delegate.
        """
        if field not in self.fields:
            self.fields.append(field)

        # If it appears that we have a editor live at the moment
        # then we need to force a reselection to rebuild that
        # editor at the correct size, taking into account the
        # change in fields.
        if self._current_editor:
            self.force_reselection()

    def force_reselection(self):
        """
        Forces a reselection of all currently-selected indexes. This serves
        the purpose of forcing a refresh of any active edit widgets.
        """
        selection = self.view.selectionModel().selection()
        self.view.selectionModel().clearSelection()
        QtGui.QApplication.processEvents()
        self.view.selectionModel().select(selection, QtGui.QItemSelectionModel.Select)

    def remove_field(self, field):
        """
        Removes the given field from the list of fields to display for the entity.

        :param field:   The name of the Shotgun field to remove from the delegate.
        """
        self.fields = [f for f in self.fields if f != field]

        # If it appears that we have a editor live at the moment
        # then we need to force a reselection to rebuild that
        # editor at the correct size, taking into account the
        # change in fields.
        if self._current_editor:
            self.force_reselection()

    def _create_widget(self, parent):
        """
        Returns the widget to be used when creating items.

        :param parent:  QWidget to parent the widget to
        :type parent:   :class:`~PySide.QtGui.QWidget`
        
        :returns:       QWidget that will be used to paint grid cells in the view.
        :rtype:         :class:`~PySide.QtGui.QWidget` 
        """
        return ListItemWidget(
            parent=parent,
            fields=self.fields,
            show_labels=self._show_labels,
            show_border=self._show_borders,
            shotgun_field_manager=self._shotgun_field_manager,
            label_exempt_fields=self._label_exempt_fields,
        )

    def _get_painter_widget(self, model_index, parent):
        """
        Constructs a widget to act as the basis for the paint event. If
        a widget has already been instantiated for this model index, that
        widget will be reused, otherwise a new widget will be instantiated
        and cached.

        :param model_index: The index of the item in the model to return a widget for
        :type model_index:  :class:`~PySide.QtCore.QModelIndex`
        :param parent:      The parent view that the widget should be parented to
        :type parent:       :class:`~PySide.QtGui.QWidget`
        :returns:           A QWidget to be used for painting the current index
        :rtype:             :class:`~PySide.QtGui.QWidget`
        """
        if model_index in self._widget_cache:
            widget = self._widget_cache[model_index]

            if self.fields != widget.fields:
                widget.fields = self.fields
                self.sizeHintChanged.emit(model_index)

            return widget

        widget = self._create_widget(parent)
        self._widget_cache[model_index] = widget
        self.sizeHintChanged.emit(model_index)

        return widget

    def _create_editor_widget(self, model_index, style_options, parent):
        """
        Called when a cell is being edited.

        :param model_index:     The index of the item in the model to return a widget for
        :type model_index:      :class:`~PySide.QtCore.QModelIndex`
        
        :param style_options:   Specifies the current Qt style options for this index
        :type style_options:    :class:`~PySide.QtGui.QStyleOptionViewItem`
        
        :param parent:          The parent view that the widget should be parented to
        :type parent:           :class:`~PySide.QtGui.QWidget`
        
        :returns:               A QWidget to be used for editing the current index
        :rtype:                 :class:`~PySide.QtGui.QWidget`
        """
        widget = self._create_widget(parent)
        self._on_before_paint(widget, model_index, style_options)
        self._current_editor = (model_index, widget)
        return widget

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called when a cell is being painted.

        :param widget: The QWidget (constructed in _create_widget()) which will 
                       be used to paint the cell. 
        :type parent:  :class:`~PySide.QtGui.QWidget`
        
        :param model_index: QModelIndex object representing the data of the object that is 
                            about to be drawn.
        :type model_index:  :class:`~PySide.QtCore.QModelIndex`
        
        :param style_options: object containing specifics about the 
                              view related state of the cell.
        :type style_options:    :class:`~PySide.QtGui.QStyleOptionViewItem`
        """
        # Get the shotgun query data for this model item.     
        sg_item = shotgun_model.get_sg_data(model_index)
        widget.set_entity(sg_item)

        if model_index in self.selection_model.selectedIndexes():
            widget.set_selected(True)
        else:
            widget.set_selected(False)

    def sizeHint(self, style_options, model_index):
        """
        Base the size on the number of entity fields to be displayed. This
        number will affect the height component of the size hint.

        :param style_options:   Specifies the current Qt style options for this index.
        :type style_options:    :class:`~PySide.QtGui.QStyleOptionViewItem`

        :param model_index:     The index of the item in the model.
        :type model_index:      :class:`~PySide.QtCore.QModelIndex`
        """
        # We have to do this ourselves instead of calling
        # _get_painter_widget because that itself emits
        # the sizeHintChanged signal, which would put us
        # into an infinite loop.
        widget = self._widget_cache.get(model_index) or self._create_widget(self.view)
        return widget.sizeHint()


