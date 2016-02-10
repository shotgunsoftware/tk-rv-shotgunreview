from PySide import QtGui, QtCore

import types
import os
import math
import rv
import rv.qtutils
import sys
import tank

from .tray_widget import TrayWidget


shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")



class RvTrayDelegate(shotgun_view.WidgetDelegate):
        _RV_DATA_ROLE = QtCore.Qt.UserRole + 99

        def __init__(self, view):
                self.tray_view = view
                shotgun_view.WidgetDelegate.__init__(self, view)
                # note! Need to have a model connected to the view in order
                # to have a selection model.
                self.__selection_model = view.selectionModel()
                if self.__selection_model:
                        self.__selection_model.selectionChanged.connect(self._on_selection_changed)
                        self.__selection_model.currentChanged.connect(self._on_current_changed)
  
                view.clicked.connect(self._handle_clicked)
                view.doubleClicked.connect(self._handle_double_clicked)
                view.entered.connect(self._handle_entered)
                       
        def _handle_entered(self, index):
                print "ITEM ENTERED: %r" % index
                # if index is None:
                #         self.tray_view.selectionModel().clear()
                # else:
                #         self.tray_view.selectionModel().setCurrentIndex(
                #                 index,
                #                 QtGui.QItemSelectionModel.SelectCurrent)
                # self.tray_view.update(index)
                (_, item, model) = self._source_for_index(index)
                item.repaint()

        def _handle_double_clicked(self, action=None):
                print "DOUBLE CLICK on ITEM %r" % action
                
                #self.tray_view.update(action)
                # (_, item, model) = self._source_for_index(action)
                # model.layoutAboutToBeChanged.emit()
                # model.changePersistentIndex(action, action)
                # model.layoutChanged.emit()


        def _handle_clicked(self, action=None):
                
                # figure out current index when it gets more complixated....
                cur_index = self.tray_view.selectionModel().currentIndex()
                (_, item, model) = self._source_for_index(cur_index)
                
                d = { 'rv_cut_selected': item.row() }
                item.setData(d, self._RV_DATA_ROLE)
                # self.tray_view.selectionModel().clear()
                #self.tray_view.model().invalidate()
                #self.tray_view.update(action)
                #item.update()

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

                rv_item = model_index.data(self._RV_DATA_ROLE)
 
                icon = model_index.data(QtCore.Qt.DecorationRole)
                thumb = icon.pixmap(widget.sizeHint())
                widget.set_thumbnail(thumb)
                widget.ui.thumbnail.setScaledContents(False)

                in_mini_cut = False
                cur_index = self.tray_view.selectionModel().currentIndex()
 
                if rv_item and rv_item['rv_cut_selected'] == model_index.row():
                        selected = True

                #Qif self.tray_view.mini_cut.mini_on:
                if (model_index.row() < (cur_index.row() + 3)) and (model_index.row() > (cur_index.row() - 3)):
                        in_mini_cut = True

                if rv_item and rv_item['rv_cut_selected'] != model_index.row():
                        (_, item, model) = self._source_for_index(model_index)
                        item.setData(None, self._RV_DATA_ROLE)
                        selected = False

                if cur_index.row() == model_index.row():
                        selected = True
                widget.set_selected(selected, in_mini_cut)

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
                
                # for s in indexes:
                #         print "sel: %r" % s.row()
                #         sg_item = shotgun_model.get_sg_data(s)
                #         print "sg: %r" % sg_item

        # works but not useful?
        def _on_current_changed(self, current_index, previous_index):
                pass
                # print "NOW %d WAS %d" % (current_index.row(), previous_index.row())

