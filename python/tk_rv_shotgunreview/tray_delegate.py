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
    _RV_DATA_ROLE = QtCore.Qt.UserRole + 1138

    def __init__(self, view):
        self.tray_view = view
        shotgun_view.WidgetDelegate.__init__(self, view)
        self.__selection_model = view.selectionModel()
        # make an alpha
        # self._alpha_size = TrayWidget.calculate_size()
        self._pen = QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.SolidLine)

        # pinned icon
        try:
            f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_app_pinned.png")
            self.pin_pixmap = QtGui.QPixmap(f)

            f2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ae.jpeg")
            self.missing_pixmap = QtGui.QPixmap(f2)

        except Exception as e:
            print "ERROR: cant load pin %r" % e
        # alpha_data = []
        # for x in range( 0, self._alpha_size.width() * self._alpha_size.height() ):
        #     alpha_data.append(127)
        # self._alpha_bitmap = QtGui.QBitmap.fromData(self._alpha_size, bytearray(alpha_data))
        # self._alpha_brush = QtGui.QBrush(QtGui.QColor(0,0,0,64))
                   
    def _handle_entered(self, index):
        # print "ITEM ENTERED: %r" % index
        pass
        # if index is None:
        #         self.tray_view.selectionModel().clear()
        # else:
        #         self.tray_view.selectionModel().setCurrentIndex(
        #                 index,
        #                 QtGui.QItemSelectionModel.SelectCurrent)
        # self.tray_view.update(index)
        # (_, item, model) = self._source_for_index(index)
        # item.repaint()

    def _handle_double_clicked(self, action=None):
        # print "DOUBLE CLICK on ITEM %r" % action
        cur_index = self.tray_view.selectionModel().currentIndex()
        (_, item, model) = self._source_for_index(cur_index)
        
        d = item.data(self._RV_DATA_ROLE)
        if d:
                d['rv_dbl_clicked'] = True
        else:
                d = {'rv_dbl_clicked': True}
        item.setData(d, self._RV_DATA_ROLE)

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
        # w.clicked.connect(self._handle_clicked)

        return w

    def _on_before_paint(self, widget, model_index, style_options, selected=False):
        """
        Called when a cell is being painted.
        """   
        # get the shotgun query data for this model item     
        sg_item = shotgun_model.get_sg_data(model_index)   
        #rv_item = model_index.data(self._RV_DATA_ROLE)

        icon = model_index.data(QtCore.Qt.DecorationRole)
        if icon:
            thumb = icon.pixmap(widget.sizeHint())
            widget.set_thumbnail(thumb)
            widget.ui.thumbnail.setScaledContents(False)

        in_mini_cut = False

        if self.tray_view.selectionModel().isSelected(model_index):
            selected = True
        
        widget.set_selected(selected, in_mini_cut)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when a cell is being selected.
        """
        # do std drawing first
        # this never happens ....
        # print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&_on_before_selection"
        self._on_before_paint(widget, model_index, style_options, selected=True)        
        widget.set_selected(True)  
        widget.setStyleSheet("{border: 2px solid #ff0000;}")

    def update_rv_role(self, index, entity):
        (source_index, item, model) = self._source_for_index(index)
        item.setData(entity, self._RV_DATA_ROLE)

    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        paint_widget = self._get_painter_widget(model_index, self.parent())
        return paint_widget.size()
        # return TrayWidget.calculate_size()
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
         

    # works but not useful?
    def _on_current_changed(self, current_index, previous_index):
        pass
        # print "_on_current_changed %d WAS %d" % (current_index.row(), previous_index.row())

    def paint(self, painter, style_options, model_index):
        """
        Paint method to handle all cells that are not being currently edited.

        :param painter:         The painter instance to use when painting
        :param style_options:   The style options to use when painting
        :param model_index:     The index in the data model that needs to be painted
        """
        sg_item = shotgun_model.get_sg_data(model_index)
        # rv_item = model_index.data(self._RV_DATA_ROLE)
        # if rv_item:
        #     print "RV ITEM IS HERE %r" % rv_item  
        # else:
        #     icon = model_index.data(QtCore.Qt.DecorationRole)
        #     if icon:
        #         (_, item, model) = self._source_for_index(model_index)
        #         item.setIcon(icon)


        #     print "NO RV ITEM"
        # for performance reasons, we are not creating a widget every time
        # but merely moving the same widget around. 
        paint_widget = self._get_painter_widget(model_index, self.parent())
        if not paint_widget:
            # just paint using the base implementation:
            QtGui.QStyledItemDelegate.paint(self, painter, style_options, model_index)
            return

        # make sure that the widget that is just used for painting isn't visible otherwise
        # it'll appear in the wrong place!
        paint_widget.setVisible(False)

        # call out to have the widget set the right values            
        self._on_before_paint(paint_widget, model_index, style_options)

        # now paint!
        painter.save()
        try:
            paint_widget.resize(style_options.rect.size())
            painter.translate(style_options.rect.topLeft())
            # note that we set the render flags NOT to render the background of the widget
            # this makes it consistent with the way the editor widget is mounted inside 
            # each element upon hover.

            paint_widget.render(painter, 
                                      QtCore.QPoint(0,0),
                                      renderFlags=QtGui.QWidget.DrawChildren)

            if self.tray_view.rv_mode.index_is_pinned(model_index.row()):
                painter.drawPixmap(paint_widget.width() - self.pin_pixmap.width(), 0, self.pin_pixmap)
                #painter.fillRect( self._alpha_size.width() - 10, 0, 10, 10, QtGui.QColor(240,200,50,127) )

            # print "image: %r %r %r " % (sg_item['version.Version.id'] ,sg_item['cut.Cut.image'] ,sg_item['cut.Cut.version.Version.image'])
            if not sg_item.get('version.Version.id') and not sg_item.get('image') and not sg_item.get('cut.Cut.version.Version.image'):
                target = QtCore.QRectF(0.0, 0.0, paint_widget.width(), paint_widget.height() )
                source = QtCore.QRectF(0, 0, self.missing_pixmap.width(), self.missing_pixmap.height())
                # painter.drawPixmap(target, self.missing_pixmap, source)
                painter.fillRect( 0, 0, paint_widget.width(), paint_widget.height(), QtGui.QColor(10,0,0,255) )
                painter.drawText(0,5,100,100, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter, 'MISSING')


            mini_data = self.tray_view.rv_mode.cached_mini_cut_data

            if mini_data.active and painter:
                if mini_data.focus_clip == model_index.row():
                    painter.setPen(self._pen)
                    ws = paint_widget.size()
                    painter.drawRect( 1, 1, ws.width()-2, ws.height()-2)

                if mini_data.first_clip > model_index.row() or mini_data.last_clip < model_index.row():
                    painter.fillRect( 0, 0, paint_widget.width(), paint_widget.height(), QtGui.QColor(0,0,0,127) )


        finally:
            painter.restore()
