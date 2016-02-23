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
from tank.platform.qt import QtCore

from .list_item_widget import ListItemWidget

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class ListItemDelegate(shotgun_view.WidgetDelegate):
    def __init__(self, parent, fields=None, show_labels=True, show_borders=True, **kwargs):
        """
        Constructs a new ListItemDelegate.

        :param parent:          The delegate's parent widget.
        :param fields:          A list of Shotgun entity fields to be displayed.
        :param show_labels:     Whether to show labels for the fields being displayed.
        :param show_borders:    Whether to draw borders around each item.
        """
        shotgun_view.WidgetDelegate.__init__(self, parent, **kwargs)
        
        self._widget_cache = dict()
        self._fields = fields
        self._show_labels = show_labels
        self._show_borders = show_borders

    def _create_widget(self, parent):
        """
        Returns the widget to be used when creating items.
        """
        return ListItemWidget(
            parent=parent,
            fields=self._fields,
            show_labels=self._show_labels,
            show_border=self._show_borders,
        )

    def _get_painter_widget(self, model_index, parent):
        """
        Constructs a widget to act as the basis for the paint event. If
        a widget has already been instantiated for this model index, that
        widget will be reused, otherwise a new widget will be instantiated
        and cached.
        """
        if model_index in self._widget_cache:
            return self._widget_cache[model_index]

        widget = self._create_widget(parent)
        self._widget_cache[model_index] = widget

        return widget

    def _create_editor_widget(self, model_index, style_options, parent):
        """
        Called when a cell is being edited.
        """
        widget = self._create_widget(parent)
        self._on_before_paint(widget, model_index, style_options)
        return widget

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called when a cell is being painted.
        """
        # get the shotgun query data for this model item     
        sg_item = shotgun_model.get_sg_data(model_index)
        widget.set_entity(sg_item)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when a cell is being selected.
        """
        # do std drawing first
        self._on_before_paint(widget, model_index, style_options)        
        widget.set_selected(True)        

    def sizeHint(self, style_options, model_index):
        """
        Base the size on the number of entity fields to be displayed. This
        number will affect the height component of the size hint.
        """
        if self._fields:
            field_count = len(self._fields)
        else:
            field_count = 2

        return ListItemWidget.calculate_size(field_count)


