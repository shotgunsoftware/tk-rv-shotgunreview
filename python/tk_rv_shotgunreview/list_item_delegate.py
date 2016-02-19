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
    def __init__(self, *args, **kwargs):
        shotgun_view.WidgetDelegate.__init__(self, *args, **kwargs)
        self._widget_cache = dict()

    def _create_widget(self, parent):
        """
        Returns the widget to be used when creating items
        """
        return ListItemWidget(parent)

    def _get_painter_widget(self, model_index, parent):
        if model_index in self._widget_cache:
            return self._widget_cache[model_index]

        widget = self._create_widget(parent)
        self._widget_cache[model_index] = widget

        return widget

    def _create_editor_widget(self, model_index, style_options, parent):
        widget = ListItemWidget(parent)
        sg_item = shotgun_model.get_sg_data(model_index)
        widget.set_entity(sg_item)
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
        Base the size on the icon size property of the view
        """
        return ListItemWidget.calculate_size()


