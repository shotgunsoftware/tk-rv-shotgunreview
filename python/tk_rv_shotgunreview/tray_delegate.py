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

from .tray_widget import TrayWidget

shotgun_view = tank.platform.import_framework(
     "tk-framework-qtwidgets",
     "views",
)

shotgun_model = tank.platform.import_framework(
     "tk-framework-shotgunutils",
     "shotgun_model",
)

class RvTrayDelegate(shotgun_view.WidgetDelegate):
     def __init__(self, view):
          shotgun_view.WidgetDelegate.__init__(self, view)
          self._tray_view = view

     @property
     def tray_view(self):
          return self._tray_view

     def _create_widget(self, parent):
          """
          Returns the widget to be used when creating items
          """
          return TrayWidget(parent)

     def _on_before_paint(self, widget, model_index, style_options):
          """
          Called when a cell is being painted.
          """   
          # Get the shotgun query data for this model item.     
          sg_item = shotgun_model.get_sg_data(model_index)   

          # Extract the standard icon associated with the item.
          icon = model_index.data(QtCore.Qt.DecorationRole)
          if icon:
               thumb = icon.pixmap(100)
               widget.set_thumbnail(thumb)

     def _on_before_selection(self, widget, model_index, style_options):
          """
          Called when a cell is being selected.
          """
          self._on_before_paint(widget, model_index, style_options)        
          widget.set_selected(True)        

     def sizeHint(self, style_options, model_index):
          """
          Base the size on the icon size property of the view
          """
          return TrayWidget.calculate_size()


