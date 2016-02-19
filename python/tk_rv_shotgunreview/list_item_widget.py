# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from .ui.list_item_widget import Ui_ListItemWidget

import tank

from tank.platform.qt import QtCore, QtGui
from .qtwidgets import ShotgunFieldManager

class ListItemWidget(QtGui.QWidget):
    """
    Simple list *item* widget which hosts a square thumbnail, header text
    and body text. It has a fixed size. Multiple of these items are typically
    put together inside a QListView to form a list.
    
    This class is typically used in conjunction with a QT View and the 
    ShotgunDelegate class. 
    """

    def __init__(self, parent):
        """
        Constructor
        """
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_ListItemWidget() 
        self.ui.setupUi(self)

        self._field_manager = ShotgunFieldManager()
        self._field_manager.initialize()

        self._entity = None

    def set_entity(self, entity):
        if self._entity and self._entity == entity:
            return

        if self._entity:
            self._entity = entity
            self.ui.thumbnail.set_value(entity.get("image"))
            self.ui.code.set_value(entity.get("code"))
            self.ui.link.set_value(entity.get("entity"))
        else:
            self._entity = entity

            self.ui.thumbnail = self._field_manager.create_display_widget(
                entity.get("type"),
                "image",
                self._entity,
            )

            self.ui.thumbnail.setMinimumWidth(100)

            self.ui.code = self._field_manager.create_display_widget(
                entity.get("type"),
                "code",
                self._entity,
            )

            self.ui.link = self._field_manager.create_display_widget(
                entity.get("type"),
                "entity",
                self._entity,
            )

            self.ui.code_layout = QtGui.QHBoxLayout()
            self.ui.code_layout.addWidget(self.ui.code)
            self.ui.code_layout.addItem(
                QtGui.QSpacerItem(
                    20,
                    40,
                    QtGui.QSizePolicy.Minimum,
                    QtGui.QSizePolicy.Expanding,
                ),
            )

            self.ui.link_layout = QtGui.QHBoxLayout()
            self.ui.link_layout.addWidget(self.ui.link)
            self.ui.link_layout.addItem(
                QtGui.QSpacerItem(
                    20,
                    40,
                    QtGui.QSizePolicy.Minimum,
                    QtGui.QSizePolicy.Expanding,
                ),
            )

            self.ui.left_layout.addWidget(self.ui.thumbnail)
            self.ui.right_layout.insertLayout(1, self.ui.link_layout)
            self.ui.right_layout.insertLayout(2, self.ui.code_layout)
                   
    def set_selected(self, selected):
        """
        Adjust the style sheet to indicate selection or not
        """
        p = QtGui.QPalette()
        # highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        
        # transp_highlight_str = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
        # highlight_str = "rgb(%s, %s, %s)" % (highlight_col.red(), highlight_col.green(), highlight_col.blue())
        
        # if selected:
        #     self.ui.box.setStyleSheet("""#box {border-width: 2px; 
        #                                          border-color: %s; 
        #                                          border-style: solid; 
        #                                          background-color: %s}
        #                               """ % (highlight_str, transp_highlight_str))

        # else:
        #     self.ui.box.setStyleSheet("")
    
    # def set_thumbnail(self, pixmap):
    #     self.ui.thumbnail.setPixmap(pixmap)
            
    # def set_text(self, header, body):
    #     """
    #     Populate the lines of text in the widget
    #     """
    #     pass
    #     # self.setToolTip("%s\n%s" % (header, body))        
    #     # self.ui.header_label.setText(header)
    #     # self.ui.body_label.setText(body)

    @staticmethod
    def calculate_size():
        """
        Calculates and returns a suitable size for this widget.
        """        
        return QtCore.QSize(300, 50)

