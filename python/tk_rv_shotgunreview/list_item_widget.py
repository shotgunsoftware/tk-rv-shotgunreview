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
    Simple list *item* widget which hosts a thumbnail, plus any requested
    entity fields in a layout to the right of the thumbnail.

    :ivar show_labels:      Whether to show entity field labels when the
                            widget is drawn.
    :vartype show_labels:   bool
    :ivar field_manager:    The accompanying ShotgunFieldManager object
                            used to construct all Shotgun field widgets.
    """
    def __init__(
        self, parent, fields=None, show_labels=True, show_border=False,
        shotgun_field_manager=None
    ):
        """
        Constructs a new ListItemWidget.

        :param parant:                  The widget's parent.
        :param fields:                  A list of Shotgun field names to display.
        :param show_labels:             Whether to show labels for fields being
                                        displayed.
        :param shotgun_field_manager:   An optional ShotgunFieldManager object. If
                                        one is not provided one will be instantiated.
        """
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_ListItemWidget() 
        self.ui.setupUi(self)

        self._fields = fields or ["code", "entity"]
        self._entity = None
        self._show_border = show_border

        self.show_labels = show_labels

        self.field_manager = shotgun_field_manager or ShotgunFieldManager()
        self.field_manager.initialize()

        self.set_selected(False)

    def set_entity(self, entity):
        """
        Sets the widget's entity and builds or refreshes the thumbnail
        and any fields being displayed.

        :param entity:  The Shotgun entity data dict, as returned from
                        the Shotgun Python API.
        """
        # Don't bother if it's the same entity we already have.
        if self._entity and self._entity == entity:
            return

        # If we've already been populated previously, then we will
        # set the values of the existing field widgets. Otherwise
        # this is a first-time setup and we need to create and place
        # the field widgets into the layout.
        if self._entity:
            self._entity = entity
            self.thumbnail.set_value(entity.get("image"))

            for field in self._fields:
                field_widget = getattr(self, field)
                if field_widget:
                    field_widget.set_value(entity.get(field))
        else:
            self._entity = entity
            self.thumbnail = self.field_manager.create_display_widget(
                entity.get("type"),
                "image",
                self._entity,
            )

            size_policy = QtGui.QSizePolicy(
                QtGui.QSizePolicy.MinimumExpanding,
                QtGui.QSizePolicy.MinimumExpanding,
            )
            size_policy.setHorizontalStretch(1)

            self.thumbnail.setSizePolicy(size_policy)

            self.ui.left_layout.addWidget(self.thumbnail)

            field_layout = QtGui.QHBoxLayout()
            field_grid_layout = QtGui.QGridLayout()
            field_grid_layout.setHorizontalSpacing(5)
            field_grid_layout.setColumnStretch(1, 3)

            self.field_layout = field_layout
            self.field_grid_layout = field_grid_layout

            field_layout.addLayout(field_grid_layout)
            field_layout.addStretch(2)

            # We want to put it below the upper spacer in the layout. The
            # reason for the findChild here is that Designer does not appear
            # to create an attribute to store spacer items in the way that
            # it does for widgets. As a result, we have to look it up by
            # name and type.
            upper_spacer = self.ui.right_layout.findChild(
                QtGui.QSpacerItem,
                "upper_spacer",
            )

            self.ui.right_layout.insertLayout(
                self.ui.right_layout.indexOf(upper_spacer) + 1,
                field_layout,
            )

            for i, field in enumerate(self._fields):
                field_widget = self.field_manager.create_display_widget(
                    entity.get("type"),
                    field,
                    self._entity,
                )

                # If we've been asked to show labels for the fields, then
                # build those and get them into the layout.
                if self.show_labels:
                    field_label = self.field_manager.create_label(
                        entity.get("type"),
                        field,
                    )

                    field_grid_layout.addWidget(field_label, i, 0)
                    setattr(self, "%s_label" % field, field_label)

                field_grid_layout.addWidget(field_widget, i, 1)
                setattr(self, field, field_widget)

            self.ui.right_layout.addStretch(3)
                   
    def set_selected(self, selected):
        """
        Adjust the style sheet to indicate selection or not.

        :param selected:    Whether the widget is selected or not.
        """
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        highlight_str = "rgb(%s, %s, %s)" % (
            highlight_col.red(),
            highlight_col.green(),
            highlight_col.blue(),
        )
        
        if selected:
            self.ui.box.setStyleSheet(
                """
                #box {
                    border-top-width: 1px;
                    border-bottom-width: 1px;
                    border-right-width: 2px;
                    border-left-width: 2px;
                    border-color: %s;
                    border-style: solid;
                }
                """ % (highlight_str)
            )
        elif self._show_border:
            self.ui.box.setStyleSheet(
                """
                #box {
                    border-top-width: 1px;
                    border-bottom-width: 1px;
                    border-right-width: 2px;
                    border-left-width: 2px;
                    border-color: rgb(66,67,69);
                    border-style: solid;
                }
                """
            )
        else:
            self.ui.box.setStyleSheet("")

    @staticmethod
    def calculate_size(field_count=2):
        """
        Calculates and returns a suitable size for this widget.

        :param field_count: The integer number of fields to account for
                            when determining the vertical size of the
                            widget. The default assumption is the display
                            of two fields.
        """
        height = (50 + (10 * (field_count - 2)))
        return QtCore.QSize(300, height)

