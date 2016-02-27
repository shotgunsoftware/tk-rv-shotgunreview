# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import json

import tank
import rv

from tank.platform.qt import QtCore, QtGui

from .ui.details_panel_widget import Ui_DetailsPanelWidget
from .list_item_widget import ListItemWidget
from .list_item_delegate import ListItemDelegate
from .version_context_menu import VersionContextMenu, VersionContextMenuAction
from .qtwidgets import ShotgunFieldManager

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_menus = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "shotgun_menus",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

shotgun_globals = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_globals",
)

task_manager = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "task_manager",
)

class DetailsPanelWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        """
        Constructor

        :param parent:  The panel's parent widget.
        """
        QtGui.QWidget.__init__(self, parent)

        self._pinned = False
        self._requested_entity = None

        self.ui = Ui_DetailsPanelWidget() 
        self.ui.setupUi(self)

        # We start off with various buttons hidden. When an
        # entity is loaded for the first time we will turn them on.
        self.ui.more_info_button.hide()
        self.ui.pin_button.hide()
        self.ui.shotgun_nav_button.hide()
        self.ui.more_fields_button.hide()

        # We need to connect to some field manager signals, so
        # we will instantiate one and keep it around. It'll be
        # passed to any ListItemWidgets that are built later.
        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self.ui.note_stream_widget,
            start_processing=True,
            max_threads=2,
        )
        shotgun_globals.register_bg_task_manager(self._task_manager)

        self._shotgun_field_manager = ShotgunFieldManager(
            bg_task_manager=self._task_manager,
        )
        self._shotgun_field_manager.initialize()

        self.version_delegate = ListItemDelegate(
            parent=self.ui.entity_version_view,
            fields=["code", "user","sg_status_list"],
            shotgun_field_manager=self._shotgun_field_manager,
            label_exempt_fields=["code"],
        )

        # These are the minimum required fields that we need
        # in order to draw all of our widgets with default settings.
        self._fields = [
            "code",
            "entity",
            "image",
            "user",
            "sg_status_list",
        ]

        # These are the fields that have been given to the info widget
        # at the top of the Notes tab. This represents all fields that
        # are displayed by default when the "More info" option is active.
        self._active_fields = [
            "code",
            "entity",
            "user",
            "sg_status_list",
        ]

        # This is the subset of self._active_fields that are always
        # visible, even when "More info" is not active.
        self._persistent_fields = [
            "code",
            "entity",
        ]

        self.version_model = shotgun_model.SimpleShotgunModel(self.ui.entity_version_tab)
        self.ui.entity_version_view.setModel(self.version_model)
        self.ui.entity_version_view.setItemDelegate(self.version_delegate)
        self.ui.note_stream_widget.set_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.allow_screenshots = False
        self.ui.note_stream_widget.show_sg_stream_button = False
        self.shot_info_model = shotgun_model.SimpleShotgunModel(self.ui.note_stream_widget)

        # For the basic info widget in the Notes stream we won't show
        # labels for the fields that are persistent. The non-standard,
        # user-specified list of fields that are shown when "more info"
        # is active will be labeled.
        self.ui.shot_info_widget.fields = self._active_fields
        self.ui.shot_info_widget.label_exempt_fields = self._persistent_fields
        self.ui.shot_info_widget.field_manager = self._shotgun_field_manager

        # Signal handling.
        self._task_manager.task_group_finished.connect(
            self._task_group_finished
        )
        self.ui.pin_button.toggled.connect(self._set_pinned)
        self.ui.more_info_button.toggled.connect(self._more_info_toggled)
        self.ui.shotgun_nav_button.clicked.connect(
            self.ui.note_stream_widget._load_shotgun_activity_stream
        )
        self.ui.entity_version_view.clicked.connect(self._select_version_item)
        self.ui.entity_version_view.customContextMenuRequested.connect(self._show_version_context_menu)

        # The fields menu attached to the "More fields..." button
        # when "More info" is active.
        self._setup_fields_menu()

    ##########################################################################
    # public methods

    def load_data(self, entity):
        """
        Loads the given Shotgun entity into the details panel,
        triggering the notes and versions streams to be updated
        relative to the given entity.

        :param entity:  The Shotgun entity to load. This is a dict in
                        the form returned by the Shotgun Python API.
        """
        if not entity:
            return

        # We have various buttons hidden until an entity is loaded,
        # so we need to turn those on now.
        self.ui.more_info_button.show()
        self.ui.pin_button.show()
        self.ui.shotgun_nav_button.show()

        # If we're pinned, then we don't allow loading new entities.
        if not self._pinned:
            self.ui.note_stream_widget.load_data(entity)

            shot_filters = [["id", "is", entity["id"]]]
            self.shot_info_model.load_data(
                entity_type="Version",
                filters=shot_filters,
                fields=self._fields,
            )

            sg_data = self.shot_info_model.item_from_entity(
                "Version",
                entity["id"],
            ).get_sg_data()

            self.ui.shot_info_widget.set_entity(sg_data)
            self._more_info_toggled(self.ui.more_info_button.isChecked())

            version_filters = [["entity", "is", sg_data["entity"]]]
            self.version_model.load_data(
                "Version",
                filters=version_filters,
                fields=self._fields,
            )
        else:
            self._requested_entity = entity

    ##########################################################################
    # internal utilities

    def _field_menu_triggered(self, action):
        """
        Adds or removes a field when it checked or unchecked
        via the EntityFieldMenu.

        :param action:  The QMenuAction that was triggered. 
        """
        if action:
            # The MenuAction's data will have a "field" key that was
            # added by the EntityFieldMenu that contains the name of
            # the field that was checked or unchecked.
            field_name = action.data()["field"]

            if action.isChecked():
                self.ui.shot_info_widget.add_field(field_name)
            else:
                self.ui.shot_info_widget.remove_field(field_name)

            # The processEvents() call will ensure that the widget
            # and layout changes have all been processed and any
            # new widgets have been shown. This is important,
            # because the sizeHint call below is dependent upon
            # field widget visibility.
            QtGui.QApplication.processEvents()
            self.ui.shot_info_widget.setFixedSize(self.ui.shot_info_widget.sizeHint())
            self._active_fields = self.ui.shot_info_widget.fields

    def _more_info_toggled(self, checked):
        """
        Toggled more/less info functionality for the info widget in the
        Notes tab.

        :param checked: True or False
        """
        if checked:
            self.ui.more_info_button.setText("Hide info")
            self.ui.more_fields_button.show()

            for field_name in self._active_fields:
                self.ui.shot_info_widget.set_field_visibility(field_name, True)

            self.ui.shot_info_widget.setFixedSize(self.ui.shot_info_widget.sizeHint())
        else:
            self.ui.more_info_button.setText("More info")
            self.ui.more_fields_button.hide()

            for field_name in self._active_fields:
                if field_name not in self._persistent_fields:
                    self.ui.shot_info_widget.set_field_visibility(field_name, False)

            self.ui.shot_info_widget.setFixedSize(self.ui.shot_info_widget.sizeHint())

        self.ui.info_layout.update()

    def _selected_version_entities(self):
        """
        Returns a list of Version entities that are currently selected.
        """
        selection_model = self.ui.entity_version_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        return [shotgun_model.get_sg_data(i) for i in indexes]

    def _select_version_item(self, index):
        """
        Causes the widget at the given index to be treated and repainted
        as the selected item in the version list.

        :param index:   The QModelIndex to select.
        """
        self.ui.entity_version_view.setCurrentIndex(index)
        self.ui.entity_version_view.selectionModel().select(
            index,
            self.ui.entity_version_view.selectionModel().ClearAndSelect,
        )
        self.version_delegate._get_painter_widget(index, None).set_selected(True)
        self.ui.entity_version_view.repaint()

    def _set_pinned(self, checked):
        """
        Sets the "pinned" state of the details panel. When the panel is
        pinned it will not accept updates. It will, however, record the
        most recent entity passed to load_data that was not accepted. If
        the panel is unpinned at a later time, the most recent rejected
        entity update will be executed at that time.

        :param checked: True or False
        """
        self._pinned = checked

        if checked:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_hover.png"))
        else:
            self.ui.pin_button.setIcon(QtGui.QIcon(":/tk-rv-shotgunreview/tack_up.png"))
            if self._requested_entity:
                self.load_data(self._requested_entity)
                self._requested_entity = None

    def _setup_fields_menu(self):
        """
        Sets up the EntityFieldMenu and attaches it as the "More fields"
        button's menu.
        """
        menu = shotgun_menus.EntityFieldMenu("Version")
        menu.set_field_filter(self._field_filter)
        menu.set_checked_filter(self._checked_filter)
        menu.set_disabled_filter(self._disabled_filter)
        self._field_menu = menu
        self._field_menu.triggered.connect(self._field_menu_triggered)
        self.ui.more_fields_button.setMenu(menu)

    def _show_version_context_menu(self, point):
        """
        Shows the version list context menu containing all available
        actions. Which actions are enabled is determined by how many
        items in the list are selected.

        :param point:   The QPoint location to show the context menu at.
        """
        selection_model = self.ui.entity_version_view.selectionModel()
        num_selected = len(selection_model.selectedIndexes())
        menu = VersionContextMenu(num_selected)

        # Each action has some kind of selection requirement.
        single = VersionContextMenuAction.SingleSelectionRequired
        multi = VersionContextMenuAction.MultiSelectionRequired
        either = VersionContextMenuAction.SingleOrMultiSelectionRequired

        menu.addAction(
            VersionContextMenuAction(
                callback=self._compare_with_current,
                required_selection=either,
                text="Compare with Current",
                parent=self,
            )
        )

        menu.addAction(
            VersionContextMenuAction(
                callback=self._compare_selected,
                required_selection=multi,
                text="Compare Selected",
                parent=self,
            )
        )

        menu.addAction(
            VersionContextMenuAction(
                callback=self._swap_into_sequence,
                required_selection=single,
                text="Swap Into Sequence",
                parent=self,
            )
        )

        menu.addAction(
            VersionContextMenuAction(
                callback=self._replace_with_selected,
                required_selection=single,
                text="Replace",
                parent=self,
            )
        )

        action = menu.exec_(self.ui.entity_version_view.mapToGlobal(point))
        action()

    def _task_group_finished(self, group):
        """
        Repaints the necessary widgets and views when a task is completed
        by the ShotgunFieldManager object. This will ensure that all widgets
        making use of Shotgun field widgets will be repainted once all data
        has been queried from Shotgun.

        :param group:   The task group that was completed.
        """
        self.ui.shot_info_widget.repaint()
        self.ui.entity_version_view.repaint()

    ##########################################################################
    # version list actions

    def _compare_with_current(self):
        """
        Builds a new RV view that compares the currently-selected version
        with what's currently active in RV.
        """
        versions = self._selected_version_entities()
        rv.commands.sendInternalEvent(
            "compare_with_current",
            json.dumps(versions),
        )

    def _compare_selected(self):
        """
        Builds a new RV view that compares the currently-selected Versions.
        """
        versions = self._selected_version_entities()
        rv.commands.sendInternalEvent(
            "compare_selected",
            json.dumps(versions),
        )

    def _swap_into_sequence(self):
        """
        Replaces the current Version in the current sequence view in RV
        with the selected Version.
        """
        versions = self._selected_version_entities()
        rv.commands.sendInternalEvent(
            "swap_into_sequence",
            json.dumps(versions),
        )

    def _replace_with_selected(self):
        """
        Replaces the current view (whether a sequence or single Version) in
        RV with the selected Version.
        """
        versions = self._selected_version_entities()
        rv.commands.sendInternalEvent(
            "replace_with_selected",
            json.dumps(versions),
        )

    ##########################################################################
    # fields menu filters

    def _checked_filter(self, field):
        """
        Checked filter method for the EntityFieldMenu. Determines whether the
        given field should be checked in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self._active_fields)

    def _disabled_filter(self, field):
        """
        Disabled filter method for the EntityFieldMenu. Determines whether the
        given field should be active or disabled in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self._persistent_fields)

    def _field_filter(self, field):
        """
        Field filter method for the EntityFieldMenu. Determines whether the
        given field should be included in the field menu.

        :param field:   The field name being processed.
        """
        # Allow any fields that we have a widget available for.
        return bool(
            self.ui.shot_info_widget.field_manager.supported_fields(
                "Version",
                [field],
            )
        )

