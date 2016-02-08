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
import sys

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
          #from tank.platform.qt import QtCore, QtGui
          #ListItemWidget.resize(366, 109)
          self.tray_view = view
          self.isLit = False
          shotgun_view.WidgetDelegate.__init__(self, view)
          # note! Need to have a model connected to the view in order
          # to have a selection model.
          self.__selection_model = view.selectionModel()
          if self.__selection_model:
               self.__selection_model.selectionChanged.connect(self._on_selection_changed)
          view.clicked.connect(self._handle_clicked)

     def _handle_clicked(self, index):
          # if you're getting this, you probably ARE the current index.

          # figure out current index when it gets more complixated....
          cur_index = self.tray_view.selectionModel().currentIndex()
          (_, item, model) = self._source_for_index(cur_index)

          #print "_handle_clicked ITEM: %r" % item.data()
          # model._handle_command_triggered(item)
          # if self.isLit:
          #         self.isLit = False
          # else:
          #         self.isLit = True
          # print "SELF IS LIT: %r" % self.isLit
          #sys.stdout.write('_handle_clicks %r vs. %r' % (index, cur_index)) 
          # need to clear the selection to avoid artifacts upon editor closing
          # self.tray_view.selectionModel().clear()

          # if action is None:
          #         model._handle_command_triggered(item)
          # else:
          #         model._handle_command_triggered(
          #                 item,
          #                 command_name=action.data()["command"],
          #                 button_name=action.data()["button"],
          #                 menu_name=action.text(),
          #                 icon=action.icon(),
          #                 tooltip=action.toolTip(),
          #         )

          # and this can change the filtering and sorting, so invalidate
          # self.tray_view.model().invalidate()


     def _source_for_index(self, model_index):
          # get the original model item for the index
          model = model_index.model()
          source_index = model_index
          while hasattr(model, "sourceModel"):
              source_index = model.mapToSource(source_index)
              model = model.sourceModel()
          item = model.itemFromIndex(source_index)
          return (source_index, item, model)

     def _create_widget(self, parent):
          """
          Returns the widget to be used when creating items
          """
          w = TrayWidget(parent)
          w.clicked.connect(self._handle_clicked)

          return w

     def _on_before_paint(self, widget, model_index, style_options, selected=False):
          """
          Called when a cell is being painted.
          """   
          # get the shotgun query data for this model item     
          sg_item = shotgun_model.get_sg_data(model_index)   

          # ptf = sg_item.get('sg_version.Version.sg_path_to_frames')
          # rv.commands.addSource(ptf)
          # if widget.take_ptf == None:
          #     widget.take_ptf = ptf
          #     self.tray_view.ptfs.append(ptf)
          #     print sg_item

          # print "WIDGET %r %r" % (widget, selected)
          # ShotgunModel.SG_ASSOCIATED_FIELD_ROLE
          # extract the standard icon associated with the item
          icon = model_index.data(QtCore.Qt.DecorationRole)
          thumb = icon.pixmap(QtCore.QSize(224, 64))

          #widget.thumbnail.setMaximumSize(QtCore.QSize(750, 750))
          widget.set_thumbnail(thumb)
          widget.ui.thumbnail.setScaledContents(False)

          #if self.isLit:
          #        selected = True
          for x in self.tray_view.selectionModel().selectedIndexes():
               if model_index == x:
                    selected = True
               else:
                    selected = False

          #cur_index = self.tray_view.selectionModel().currentIndex()
          #if cur_index == model_index:
          #        selected = True


          widget.set_selected(selected)
          # fill the content of the widget with the data of the loaded Shotgun
          # code_str = sg_item.get("code")
          # type_str = sg_item.get("type")
          # id_str = sg_item.get("id")

          # header_str = "%s" % (code_str)
          # body_str = "%s %s" % (type_str, id_str)
          # widget.set_text(header_str, body_str)

     def _on_before_selection(self, widget, model_index, style_options):
          """
          Called when a cell is being selected.
          """
          # do std drawing first
          print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&_on_before_selection"
          self._on_before_paint(widget, model_index, style_options, selected=True)        
          widget.set_selected(True)  
          widget.setStyleSheet("{border: 2px solid #ff0000;}")
 

     def sizeHint(self, style_options, model_index):
          """
          Base the size on the icon size property of the view
          """
          return TrayWidget.calculate_size()
          #return QtCore.QSize(150,100)
   
     def _on_selection_changed(self, selected, deselected):
          """
          Signal triggered when someone changes the selection in the view.
          :param selected:    A list of the indexes in the model that were selected
          :type selected:     :class:`~PySide.QtGui.QItemSelection`
          :param deselected:  A list of the indexes in the model that were deselected
          :type deselected:  :class:`~PySide.QtGui.QItemSelection`
          """               
          indexes = selected.indexes()
          print "SELECTION: %r" % selected
          for s in indexes:
               print "sel: %r" % s.row()
               sg_item = shotgun_model.get_sg_data(s)
               print "sg: %r" % sg_item