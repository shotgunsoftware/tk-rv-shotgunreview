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
from .version_context_menu import VersionContextMenu
from .qtwidgets import ShotgunFieldManager
from .version_sort_filter import VersionSortFilterProxyModel

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

screen_grab = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "screen_grab",
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
        self._current_entity = None

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
            self,
            bg_task_manager=self._task_manager,
        )
        self._shotgun_field_manager.initialize()

        # These are the minimum required fields that we need
        # in order to draw all of our widgets with default settings.
        self._fields = [
            "code",
            "entity",
            "image",
            "user",
            "sg_status_list",
            "sg_path_to_frames",
            "sg_first_frame",
            "sg_last_frame",
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

        # The fields list for the Version list view delegate operate
        # the same way as the above persistent list. We're simply
        # keeping track of what we don't allow to be turned off.
        self._version_list_persistent_fields = [
            "code",
            "user",
            "sg_status_list",
        ]

        # Our sort-by list will include "id" at the head.
        self._version_list_sort_by_fields = ["id"] + self._version_list_persistent_fields

        self.version_model = shotgun_model.SimpleShotgunModel(self.ui.entity_version_tab)
        self.version_proxy_model = VersionSortFilterProxyModel(
            parent=self.ui.entity_version_view,
            filter_by_fields=self._version_list_persistent_fields,
            sort_by_field="id",
        )
        self.version_proxy_model.setFilterWildcard("*")
        self.version_proxy_model.setSourceModel(self.version_model)
        self.ui.entity_version_view.setModel(self.version_proxy_model)
        self.version_delegate = ListItemDelegate(
            view=self.ui.entity_version_view,
            fields=self._version_list_persistent_fields,
            shotgun_field_manager=self._shotgun_field_manager,
            label_exempt_fields=["code"],
        )
        self.ui.entity_version_view.setItemDelegate(self.version_delegate)
        self.ui.note_stream_widget.set_bg_task_manager(self._task_manager)
        self.ui.note_stream_widget.show_sg_stream_button = False
        self.shot_info_model = shotgun_model.SimpleShotgunModel(self.ui.note_stream_widget)

        # We need to register our screen-grab callback. Instead
        # of what ships with the widget
        screen_grab.ScreenGrabber.SCREEN_GRAB_CALLBACK = self._trigger_rv_screen_grab

        # For the basic info widget in the Notes stream we won't show
        # labels for the fields that are persistent. The non-standard,
        # user-specified list of fields that are shown when "more info"
        # is active will be labeled.
        self.ui.shot_info_widget.field_manager = self._shotgun_field_manager
        self.ui.shot_info_widget.fields = self._active_fields
        self.ui.shot_info_widget.label_exempt_fields = self._persistent_fields

        # Signal handling.
        self._task_manager.task_group_finished.connect(
            self._task_group_finished
        )
        self.ui.pin_button.toggled.connect(self.set_pinned)
        self.ui.more_info_button.toggled.connect(self._more_info_toggled)
        self.ui.shotgun_nav_button.clicked.connect(
            self.ui.note_stream_widget._load_shotgun_activity_stream
        )
        self.ui.entity_version_view.customContextMenuRequested.connect(
            self._show_version_context_menu,
        )
        self.ui.version_search.search_edited.connect(self.version_proxy_model.setFilterWildcard)

        # The fields menu attached to the "Fields..." buttons
        # when "More info" is active as well as in the Versions
        # tab.
        self._setup_fields_menu()
        self._setup_version_list_fields_menu()
        self._setup_version_sort_by_menu()

    ##########################################################################
    # properties

    @property
    def is_pinned(self):
        """
        Returns True if the panel is pinned and not processing entity
        updates, and False if it is not pinned.
        """
        return self._pinned

    ##########################################################################
    # public methods

    def add_note_attachments(self, file_paths, cleanup_after_upload=True):
        """
        Adds a given list of files to the note widget as file attachments.

        :param file_paths:              A list of file paths to attach to the
                                        current note.
        :param cleanup_after_upload:    If True, after the files are uploaded
                                        to Shotgun they will be removed from disk.
        """
        if self.ui.note_stream_widget.reply_dialog:
            self.ui.note_stream_widget.reply_dialog.note_widget.add_files_to_attachments(
                file_paths,
                cleanup_after_upload,
                apply_attachments=True,
            )

        else:
            self.ui.note_stream_widget.note_widget.add_files_to_attachments(
                file_paths,
                cleanup_after_upload,
                apply_attachments=True,
            )

    def clear(self):
        """
        Clears all data from all widgets and views in the details panel.
        """
        self._more_info_toggled(False)
        self.ui.note_stream_widget._clear()
        self.ui.shot_info_widget.clear()
        self.ui.more_info_button.hide()
        self.ui.pin_button.hide()
        self.ui.shotgun_nav_button.hide()
        self.version_model.clear()

    def load_data(self, entity):
        """
        Loads the given Shotgun entity into the details panel,
        triggering the notes and versions streams to be updated
        relative to the given entity.

        :param entity:  The Shotgun entity to load. This is a dict in
                        the form returned by the Shotgun Python API.
        """
        # If we're pinned, then we don't allow loading new entities.
        if self._pinned:
            self._requested_entity = entity
            return

        # If we got an "empty" entity from the mode, then we need
        # to clear everything out and go back to an empty state.
        if not entity or not entity.get("id"):
            self.clear()
            return

        # We have various buttons hidden until an entity is loaded,
        # so we need to turn those on now.
        self.ui.more_info_button.show()
        self.ui.pin_button.show()
        self.ui.shotgun_nav_button.show()

        # If there aren't any fields set in the info widget then it
        # likely means we're loading from a "cleared" slate and need
        # to re-add our relevant fields.
        if not self.ui.shot_info_widget.fields:
            self.ui.shot_info_widget.fields = self._active_fields
            self.ui.shot_info_widget.label_exempt_fields = self._persistent_fields

        self._current_entity = entity
        self.ui.note_stream_widget.load_data(entity)

        shot_filters = [["id", "is", entity["id"]]]
        self.shot_info_model.load_data(
            entity_type="Version",
            filters=shot_filters,
            fields=self._fields,
        )

        item = self.shot_info_model.item_from_entity(
            "Version",
            entity["id"],
        )

        if not item:
            return

        sg_data = item.get_sg_data()

        self.ui.shot_info_widget.set_entity(sg_data)
        self._more_info_toggled(self.ui.more_info_button.isChecked())

        version_filters = [["entity", "is", sg_data["entity"]]]
        self.version_model.load_data(
            "Version",
            filters=version_filters,
            fields=self._fields,
        )

        self.version_proxy_model.sort(0, QtCore.Qt.AscendingOrder)

    def set_note_screenshot(self, image_path):
        """
        Takes the given file path to an image and sets the new note
        widget's thumbnail image.

        :param image_path:  A file path to an image file on disk.
        """
        self.ui.note_stream_widget.note_widget._set_screenshot_pixmap(
            QtGui.QPixmap(image_path),
        )

    def set_pinned(self, checked):
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

            self._active_fields = self.ui.shot_info_widget.fields

    def _version_list_field_menu_triggered(self, action):
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
                self.version_delegate.add_field(field_name)

                # When a field is added to the list, then we also need to
                # add it to the sort-by menu.
                if field_name not in self._version_list_sort_by_fields:
                    self._version_list_sort_by_fields.append(field_name)
                    new_action = QtGui.QAction(
                        shotgun_globals.get_field_display_name(
                            "Version",
                            field_name,
                        ),
                        self,
                    )
                    new_action.setData(field_name)
                    self._version_sort_menu.addAction(new_action)
            else:
                self.version_delegate.remove_field(field_name)

                # We also need to remove the field from the sort-by menu. We
                # will leave "id" in the list always, even if it isn't being
                # displayed by the delegate.
                if field_name != "id" and field_name in self._version_list_sort_by_fields:
                    self._version_list_sort_by_fields.remove(field_name)
                    sort_actions = self._version_sort_menu.actions()
                    remove_action = [a for a in sort_actions if a.data() == field_name][0]
                    self._version_sort_menu.removeAction(remove_action)

            self.version_proxy_model.filter_by_fields = self.version_delegate.fields
            self.version_proxy_model.setFilterWildcard(self.ui.version_search.search_text)
            self.ui.entity_version_view.repaint()

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
        else:
            self.ui.more_info_button.setText("More info")
            self.ui.more_fields_button.hide()

            for field_name in self._active_fields:
                if field_name not in self._persistent_fields:
                    self.ui.shot_info_widget.set_field_visibility(field_name, False)

    def _selected_version_entities(self):
        """
        Returns a list of Version entities that are currently selected.
        """
        selection_model = self.ui.entity_version_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        return [shotgun_model.get_sg_data(i) for i in indexes]

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

    def _setup_version_list_fields_menu(self):
        """
        Sets up the EntityFieldMenu and attaches it as the "More fields"
        button's menu.
        """
        menu = shotgun_menus.EntityFieldMenu("Version")
        menu.set_field_filter(self._field_filter)
        menu.set_checked_filter(self._version_list_checked_filter)
        menu.set_disabled_filter(self._version_list_disabled_filter)
        self._version_list_field_menu = menu
        self._version_list_field_menu.triggered.connect(self._version_list_field_menu_triggered)
        self.ui.version_fields_button.setMenu(menu)

    def _setup_version_sort_by_menu(self):
        """
        Sets up the sort-by menu in the Versions tab.
        """
        self._version_sort_menu = QtGui.QMenu(self)

        for field_name in self._version_list_sort_by_fields:
            action = QtGui.QAction(
                shotgun_globals.get_field_display_name("Version", field_name),
                self,
            )

            # We store the database field name on the action, but
            # display the "pretty" name for users.
            action.setData(field_name)
            self._version_sort_menu.addAction(action)

        self._version_sort_menu.triggered.connect(self._sort_version_list)
        self.ui.version_sort_button.setMenu(self._version_sort_menu)

    def _show_version_context_menu(self, point):
        """
        Shows the version list context menu containing all available
        actions. Which actions are enabled is determined by how many
        items in the list are selected.

        :param point:   The QPoint location to show the context menu at.
        """
        selection_model = self.ui.entity_version_view.selectionModel()
        versions = self._selected_version_entities()
        menu = VersionContextMenu(versions)

        # Each action has its own callback, text (the label shown in the
        # menu), and selection requirement. If the selection requirement
        # is met, the action will be enabled. If not, it will be disabled.
        menu.addAction(
            action_definition=dict(
                callback=self._compare_with_current,
                required_selection="either",
                text="Compare with Current",
            )
        )

        menu.addAction(
            action_definition=dict(
                callback=self._compare_selected,
                required_selection="multi",
                text="Compare Selected",
                parent=self,
            )
        )

        menu.addAction(
            action_definition=dict(
                callback=self._swap_into_sequence,
                required_selection="single",
                text="Swap Into Sequence",
            )
        )

        menu.addAction(
            action_definition=dict(
                callback=self._replace_with_selected,
                required_selection="single",
                text="Replace",
            )
        )

        # Show the menu at the mouse cursor. Whatever action is
        # chosen from the menu will have its callback executed.
        action = menu.exec_(self.ui.entity_version_view.mapToGlobal(point))
        menu.execute_callback(action)

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

    def _trigger_rv_screen_grab(self):
        """
        Triggers an RV event instructing the mode running as part of
        the SG Review app to trigger RV's native frame capture routine.
        """
        rv.commands.sendInternalEvent(
            "new_note_screenshot",
            json.dumps(self._current_entity),
        )

    ##########################################################################
    # version list actions

    def _compare_with_current(self, versions):
        """
        Builds a new RV view that compares the given version entity
        with what's currently active in RV.

        :param versions:    The list of version entities to compare.
        """
        rv.commands.sendInternalEvent(
            "compare_with_current",
            json.dumps(versions),
        )

    def _compare_selected(self, versions):
        """
        Builds a new RV view that compares the given Versions.

        :param versions:    The list of version entities to compare.
        """
        rv.commands.sendInternalEvent(
            "compare_selected",
            json.dumps(versions),
        )

    def _swap_into_sequence(self, versions):
        """
        Replaces the current Version in the current sequence view in RV
        with the given Version.

        :param versions:    A list containing a single version entity.
        """
        rv.commands.sendInternalEvent(
            "swap_into_sequence",
            json.dumps(versions),
        )

    def _replace_with_selected(self, versions):
        """
        Replaces the current view (whether a sequence or single Version) in
        RV with the given Version.

        :param versions:    A list containing a single version entity.
        """
        rv.commands.sendInternalEvent(
            "replace_with_selected",
            json.dumps(versions),
        )

    def _sort_version_list(self, action):
        """
        Sorts the version list by the field chosen in the sort-by
        menu. This also triggers a reselection in the view in
        order to ensure proper sorting and drawing of items in the
        list.

        :param action:  The QAction chosen by the user from the menu.
        """
        field = action.data() or "id"
        self.version_proxy_model.sort_by_field = field
        self.version_proxy_model.sort(0, QtCore.Qt.AscendingOrder)

        # We need to force a reselection after sorting. This will
        # remove edit widgets and allow a full repaint of the view,
        # and then reselect to go back to editing.
        self.version_delegate.force_reselection()

    ##########################################################################
    # fields menu filters

    def _checked_filter(self, field):
        """
        Checked filter method for the EntityFieldMenu. Determines whether the
        given field should be checked in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self._active_fields)

    def _version_list_checked_filter(self, field):
        """
        Checked filter method for the EntityFieldMenu. Determines whether the
        given field should be checked in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self.version_delegate.fields)

    def _disabled_filter(self, field):
        """
        Disabled filter method for the EntityFieldMenu. Determines whether the
        given field should be active or disabled in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self._persistent_fields)

    def _version_list_disabled_filter(self, field):
        """
        Disabled filter method for the EntityFieldMenu. Determines whether the
        given field should be active or disabled in the field menu.

        :param field:   The field name being processed.
        """
        return (field in self._version_list_persistent_fields)

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

