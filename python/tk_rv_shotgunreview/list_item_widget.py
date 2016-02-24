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
    :ivar fields:           The list of Shotgun fields to display for the
                            loaded entity.
    :vartype fields:        list of strings
    """
    def __init__(
        self, parent, fields=None, show_labels=True, show_border=False,
        shotgun_field_manager=None, label_exempt_fields=None
    ):
        """
        Constructs a new ListItemWidget.

        :param parant:                  The widget's parent.
        :param fields:                  A list of Shotgun field names to display.
        :param show_labels:             Whether to show labels for fields being
                                        displayed.
        :param shotgun_field_manager:   An optional ShotgunFieldManager object. If
                                        one is not provided one will be instantiated.
        :param label_exempt_fields:     A list of field names that are exempt from having
                                        labels displayed.
        """
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_ListItemWidget() 
        self.ui.setupUi(self)

        self._entity = None
        self._show_border = show_border

        self.show_labels = show_labels
        self.label_exempt_fields = label_exempt_fields or []
        self._fields = fields or ["code", "entity"]
        self._field_visibility = {field:True for field in self.fields}

        self.field_manager = shotgun_field_manager or ShotgunFieldManager()
        self.field_manager.initialize()

        self.set_selected(False)

    def _get_fields(self):
        return self._fields

    def _set_fields(self, fields):
        self._fields = fields
        self._field_visibility = {field:True for field in fields}

    fields = property(_get_fields, _set_fields)

    def add_field(self, field_name):
        """
        Adds the given field to the list of Shotgun entity fields displayed
        by the widget.

        :param field_name:  The Shotgun entity field name to add.
        """
        if field_name in self.fields:
            return

        if field_name not in self._field_visibility:
            self._field_visibility[field_name] = True

        if not self._entity:
            self.fields.append(field_name)
            return

        field_widget = self.field_manager.create_display_widget(
            self._entity.get("type"),
            field_name,
            self._entity,
        )
        setattr(self, field_name, field_widget)

        if self.show_labels:
            # If this field is exempt from having a label, then it
            # goes into the layout in column 0, but with the column
            # span set to -1. This will cause it to occupy all of the
            # space on this row of the layout instead of just the first
            # column.
            if field_name in self.label_exempt_fields:
                self.field_grid_layout.addWidget(field_widget, len(self.fields), 0, 1, -1)
            else:
                field_label = self.field_manager.create_label(
                    self._entity.get("type"),
                    field_name,
                )
                setattr(self, "%s_label" % field_name, field_label)
                self.field_grid_layout.addWidget(field_label, len(self.fields), 0)
                self.field_grid_layout.addWidget(field_widget, len(self.fields), 1)
        else:
            self.field_grid_layout.addWidget(field_widget, len(self.fields), 0)

    def get_visible_fields(self):
        """
        Returns a list of field names that are currently visible.
        """
        return [f for f in self._field_visibility.keys() if self._field_visibility[f]]

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

            for field in self.fields:
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

            self.ui.box_layout.setStretchFactor(self.ui.right_layout, 15)
            self.ui.box_layout.setStretchFactor(self.ui.left_layout, 7)

            size_policy = QtGui.QSizePolicy(
                QtGui.QSizePolicy.Preferred,
                QtGui.QSizePolicy.MinimumExpanding,
            )

            self.thumbnail.setSizePolicy(size_policy)
            self.ui.left_layout.insertWidget(0, self.thumbnail)

            field_layout = QtGui.QHBoxLayout()
            field_grid_layout = QtGui.QGridLayout()
            field_grid_layout.setHorizontalSpacing(5)
            field_grid_layout.setVerticalSpacing(2)
            field_grid_layout.setColumnStretch(1, 3)

            self.field_layout = field_layout
            self.field_grid_layout = field_grid_layout

            field_layout.addLayout(field_grid_layout)
            field_layout.addStretch(2)

            self.ui.right_layout.insertLayout(0, field_layout)

            for i, field in enumerate(self.fields):
                field_widget = self.field_manager.create_display_widget(
                    entity.get("type"),
                    field,
                    self._entity,
                )

                # If we've been asked to show labels for the fields, then
                # build those and get them into the layout.
                if self.show_labels:
                    # If this field is exempt from having a label, then it
                    # goes into the layout in column 0, but with the column
                    # span set to -1. This will cause it to occupy all of the
                    # space on this row of the layout instead of just the first
                    # column.
                    if field in self.label_exempt_fields:
                        self.field_grid_layout.addWidget(field_widget, i, 0, 1, -1)
                    else:
                        field_label = self.field_manager.create_label(
                            entity.get("type"),
                            field,
                        )

                        field_grid_layout.addWidget(field_label, i, 0)
                        setattr(self, "%s_label" % field, field_label)
                        field_grid_layout.addWidget(field_widget, i, 1)
                else:
                    field_grid_layout.addWidget(field_widget, i, 0)
                setattr(self, field, field_widget)

            self.ui.right_layout.addStretch(3)

    def set_field_visibility(self, field_name, state):
        """
        Sets the visibility of a field widget by name.

        :param field_name:  The name of the Shotgun field.
        :param state:       True or False
        """
        if hasattr(self, field_name):
            getattr(self, field_name).setVisible(bool(state))

            field_label_name = "%s_label" % field_name
            if hasattr(self, field_label_name):
                getattr(self, field_label_name).setVisible(bool(state))

            self._field_visibility[field_name] = bool(state)
                   
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

    def sizeHint(self):
        """
        Tells Qt what the sizeHint for the widget is, based on
        the number of visible field widgets.
        """
        return ListItemWidget.calculate_size(len(self.get_visible_fields()))

    def minimumSizeHint(self):
        """
        Tells Qt what the minimumSizeHint for the widget is, based on
        the number of visible field widgets.
        """
        return self.sizeHint()

    @staticmethod
    def calculate_size(field_count=2):
        """
        Calculates and returns a suitable size for this widget.

        :param field_count: The integer number of fields to account for
                            when determining the vertical size of the
                            widget. The default assumption is the display
                            of two fields.
        """
        height = (50 + (15 * (field_count - 2)))
        return QtCore.QSize(300, height)

