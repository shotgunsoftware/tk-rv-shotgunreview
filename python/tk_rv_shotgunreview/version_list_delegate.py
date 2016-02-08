# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import types
import os
import math

import rv
import rv.qtutils

import tank
from tank.platform.qt import QtGui, QtCore

from .version_list_widget import VersionListWidget

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

class RvVersionListDelegate(shotgun_view.WidgetDelegate):
    def _create_widget(self, parent):
        """
        Returns the widget to be used when creating items
        """
        return VersionListWidget(parent)

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called when a cell is being painted.
        """   
        
        # extract the standard icon associated with the item
        icon = model_index.data(QtCore.Qt.DecorationRole)
        if icon:
            thumb = icon.pixmap(100)
            widget.set_thumbnail(thumb)
        
        # get the shotgun query data for this model item     
        sg_item = shotgun_model.get_sg_data(model_index)   
        # fill the content of the widget with the data of the loaded Shotgun
        code_str = sg_item.get("code")
        type_str = sg_item.get("type")
        id_str = sg_item.get("id")
        header_str = "<br>%s" % (code_str)
        body_str = " %s &mdash; %s" % (type_str, id_str)
        widget.set_text(header_str, body_str)

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
        return shotgun_view.ListWidget.calculate_size()


