# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui
from .tray_delegate import RvTrayDelegate
from .mini_cut_widget import MiniCutWidget

import os
import tank
task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_version_details = tank.platform.import_framework("tk-framework-qtwidgets", "version_details")

from .version_context_menu import VersionContextMenu
from .nested_version_qmenu import NestedVersionQMenu

import pprint

class TrayMainFrame(QtGui.QFrame):

    def __init__(self, parent, rv_mode):
        """
        Constructor
        """
        QtGui.QFrame.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(True)
        self.tray_dock = parent
        self.tray_model = None
        self.tray_list = None
        self.tray_delegate = None
        self.tray_proxyModel = None

        self._version_context_menu_actions = []

        self._rv_mode = rv_mode
        # using the new singleton bg manager
        self._task_manager = self._rv_mode._app.engine.bg_task_manager
        # set up the UI
        self.init_ui()

    def show_steps_and_statuses(self, visible):
        self.pipeline_filter_button.setVisible( visible )
        self.status_filter_button.setVisible( visible )

    def set_rv_mode(self, rv_mode):
        """
        reference to application state
        """
        self._rv_mode = rv_mode
        self.tray_list.rv_mode = rv_mode

    def toggle_floating(self):
        """
        Toggles the parent dock widget's floating status.
        """
        if self.tray_dock.isFloating():
            self.tray_dock.setFloating(False)
            self.dock_location_changed()
        else:
            self.tray_dock.setTitleBarWidget(None)
            self.tray_dock.setFloating(True)

    def hide_dock(self):
        """
        Hides the parent dock widget.
        """
        self.tray_dock.hide()

    def dock_location_changed(self):
        """
        Handles the dock being redocked in some location. This will
        trigger removing the default title bar.
        """
        self.tray_dock.setTitleBarWidget(QtGui.QWidget(self.tray_dock.parent()))

    def refresh_tray_dock(self):
        """
        Refresh the content of the tray dock (i.e. parent)
        """
        self._rv_mode.load_tray_with_something_new(
            self._rv_mode.last_target_entity
        )

    def init_ui(self):
        self.setObjectName('tray_frame')
        self.tray_frame_vlayout = QtGui.QVBoxLayout(self)

        # tray button bar
        self.tray_button_bar = QtGui.QFrame()
        self.tray_button_bar_grid = QtGui.QGridLayout(self.tray_button_bar)
        self.tray_button_bar_grid.setContentsMargins(0, 0, 0, 0)
        self.tray_button_bar_grid.setHorizontalSpacing(8)
        self.tray_button_bar_grid.setVerticalSpacing(0)
        
        self.tray_button_bar.setObjectName('tray_button_bar')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)

        self.tray_button_bar.setSizePolicy(sizePolicy)

        self.tray_button_bar_hlayout = QtGui.QHBoxLayout()
        self.tray_button_bar_hlayout.setSpacing(16)
        self.tray_button_bar_grid.addLayout(self.tray_button_bar_hlayout, 0, 0)
        self.tray_button_bar_hlayout.setContentsMargins(0, 0, 0, 0)
        
        self.tray_button_browse_cut = QtGui.QPushButton()
        self.tray_button_browse_cut.setText('Cut Name')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_browse_cut)

        self.tray_button_bar_hlayout.addStretch(1)

        self.tray_button_entire_cut = QtGui.QPushButton()
        self.tray_button_entire_cut.setText('Entire Cut')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_entire_cut)

        self.tray_bar_button = QtGui.QPushButton()
        self.tray_bar_button.setText('|')
        self.tray_button_bar_hlayout.addWidget(self.tray_bar_button)

        self.tray_button_mini_cut = QtGui.QPushButton()
        self.tray_button_mini_cut.setText('Mini Cut')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_mini_cut)

        self.tray_mini_label = QtGui.QPushButton()
        self.tray_mini_label.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.tray_mini_label.setText('-2+2')

        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arrow_smaller.png")
        icon = QtGui.QIcon(f)
        self.tray_mini_label.setIcon(icon)

        self.tray_button_bar_hlayout.addWidget(self.tray_mini_label) 
        self.tray_button_bar_hlayout.addStretch(1)

        self.pipeline_filter_button = QtGui.QPushButton()
        self.pipeline_filter_button.setText('Filter by Pipeline')
        self.tray_button_bar_hlayout.addWidget(self.pipeline_filter_button)

        self.status_filter_button = QtGui.QPushButton()
        self.status_filter_button.setText('Filter by Status')
        self.tray_button_bar_hlayout.addWidget(self.status_filter_button)

        self.close_button = QtGui.QToolButton()
        self.float_button = QtGui.QToolButton()
        self.refresh_button = QtGui.QToolButton()
        self.close_button.setObjectName("tray_close_button")
        self.float_button.setObjectName("tray_float_button")
        self.refresh_button.setObjectName("tray_refresh_button")

        self.close_button.setAutoRaise(True)
        self.float_button.setAutoRaise(True)
        self.float_button.setCheckable(True)
        self.refresh_button.setAutoRaise(True)

        # For whatever reason, defining this style in the tray_dock.qss
        # file doesn't work here. Doing it directly onto the buttons as
        # a result.
        self.close_button.setStyleSheet("min-width: 8px; min-height: 8px")
        self.float_button.setStyleSheet("min-width: 8px; min-height: 8px")
        self.refresh_button.setStyleSheet("min-width: 8px; min-height: 8px")
        self.close_button.setIconSize(QtCore.QSize(8,8))
        self.float_button.setIconSize(QtCore.QSize(8,8))
        self.refresh_button.setIconSize(QtCore.QSize(8,8))

        # We're taking over the responsibility of handling the title bar's
        # typical responsibilities of closing the dock and managing float
        # and unfloat behavior. We need to hook up to the dockLocationChanged
        # signal because a floating DockWidget can be redocked with a
        # double click of the window, which won't go through our button.
        self.float_button.clicked.connect(self.toggle_floating)
        self.close_button.clicked.connect(self.hide_dock)
        self.tray_dock.dockLocationChanged.connect(self.dock_location_changed)

        self.refresh_button.clicked.connect(self.refresh_tray_dock)

        self.close_icon = QtGui.QIcon()
        self.float_icon = QtGui.QIcon()

        self.close_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/close_hover.png"),
            QtGui.QIcon.Active,
            QtGui.QIcon.On,
        )
        self.close_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/close.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.close_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/close_hover.png"),
            QtGui.QIcon.Selected,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/dock_hover.png"),
            QtGui.QIcon.Active,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock_hover.png"),
            QtGui.QIcon.Active,
            QtGui.QIcon.Off,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/dock.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock_hover.png"),
            QtGui.QIcon.Selected,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock_hover.png"),
            QtGui.QIcon.Selected,
            QtGui.QIcon.Off,
        )

        self.close_button.setIcon(self.close_icon)
        self.float_button.setIcon(self.float_icon)

        # Path hack to display our own images
        rpath = os.environ.get("RV_TK_SHOTGUNREVIEW")
        self.refresh_icon = QtGui.QIcon()
        self.refresh_icon.addPixmap(
            QtGui.QPixmap(os.path.join(rpath, "resources/refresh_hover.png")),
            QtGui.QIcon.Active,
            QtGui.QIcon.On,
        )
        self.refresh_icon.addPixmap(
            QtGui.QPixmap(os.path.join(rpath, "resources/refresh.png")),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.refresh_icon.addPixmap(
            QtGui.QPixmap(os.path.join(rpath, "resources/refresh_hover.png")),
            QtGui.QIcon.Selected,
            QtGui.QIcon.On,
        )
        self.refresh_button.setIcon(self.refresh_icon)

        # The buttons will be stacked vertically, with the close button
        # even with the button bar at the top of the tray, and the float
        # button immediately below it.
        self.tray_dock_control_layout = QtGui.QHBoxLayout()
        self.tray_dock_control_layout.setSpacing(0)
        self.tray_dock_control_layout.setContentsMargins(8, 0, 0, 0)
        self.tray_dock_control_layout.addWidget(self.refresh_button)
        self.tray_dock_control_layout.addWidget(self.float_button)
        self.tray_dock_control_layout.addWidget(self.close_button)
        self.tray_button_bar_grid.addLayout(self.tray_dock_control_layout, 0, 1)

        self.tray_frame_vlayout.addWidget(self.tray_button_bar)
        self.tray_frame_vlayout.setStretchFactor(self.tray_button_bar, 1)
        
        # QListView ##########################
        #####################################################################
        self.tray_list = QtGui.QListView()
        self.tray_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tray_list.rv_mode = self._rv_mode
        self.tray_list.setFocusPolicy(QtCore.Qt.NoFocus)
                
        self.tray_frame_vlayout.addWidget(self.tray_list)
        
        from .tray_model import TrayModel
        self.tray_model = TrayModel(self.tray_list,
                                    bg_task_manager=self._task_manager,
                                    engine=self._rv_mode._app.engine)

        from .tray_sort_filter import TraySortFilter
        self.tray_proxyModel = TraySortFilter(self.tray_list)
        self.tray_proxyModel.setSourceModel(self.tray_model)

        self.tray_list.setModel(self.tray_proxyModel)
        self.tray_proxyModel.setDynamicSortFilter(True)

        self.tray_delegate = RvTrayDelegate(self.tray_list)
        self.tray_list.setItemDelegate(self.tray_delegate)

        self.tray_list.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tray_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tray_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tray_list.setFlow(QtGui.QListView.LeftToRight)
        self.tray_list.setUniformItemSizes(True)
                
        self.tray_list.setObjectName("tray_list")

        self.mc_widget = MiniCutWidget(self)
        self.mc_widget.setVisible(False)
        self.tray_dock.mc_widget = self.mc_widget
        # mc_widget can change its parent when undocked, so we need to store a reference to 
        # tray_dock so we dont have to rely on parent exclusively.
        self.mc_widget.tray_dock = self.tray_dock

        # Create context menu
        self.tray_list.customContextMenuRequested.connect(
            self._show_version_context_menu
        )

    def add_version_context_menu_action(self, action_definition):
        """
        Adds an action to the version tab's context menu.

        Action definitions passed in must take the following form:

            dict(
                callback=callable,
                text=str,
                required_selection="single"
            )

        Where the callback is a callable object that expects to receive
        a list of Version entity dictionaries as returned by the Shotgun
        Python API. The text key contains the string labels of the action
        in the QMenu, and the required_selection is one of "single", "multi",
        or "either". Any action requiring a "single" selection will be enabled
        only if there is a single item selected in the Version list view,
        those requiring "multi" selection require 2 or more selected items,
        and the "either" requirement results in the action being enabled if
        one or more items are selected.

        :param action_definition:   The action defition to add to the menu.
                                    This takes the form of a dictionary of
                                    a structure described in the method docs
                                    above.
        :type action_definition:    dict
        """
        self._version_context_menu_actions.append(action_definition)

    def _show_version_context_menu(self, point):
        """
        Shows the version list context menu containing all available
        actions. Which actions are enabled is determined by how many
        items in the list are selected.

        :param point:   The QPoint location to show the context menu at.
        """
        versions = self._selected_version_entities()
        menu = VersionContextMenu(versions)

        for menu_action in self._version_context_menu_actions:
            menu.addAction(action_definition=menu_action)

        self._add_compare_with_asset_menu(menu, versions)
        self._add_compare_with_approved_version(menu, versions)
        self._add_compare_with_latest_version(menu, versions)

        # Show the menu at the mouse cursor. Whatever action is
        # chosen from the menu will have its callback executed.
        action = menu.exec_(self.tray_list.mapToGlobal(point))
        menu.execute_callback(action)

    def _add_compare_with_asset_menu(self, menu, versions):
        """
        Create context menu for Asset Versions related to given Version(s)

        :param menu: `QMenu`
        :param versions: `list` of Version dicts
        :return: `QMenu`
        """
        if len(versions) == 1:
            versions = self._rv_mode._get_asset_versions(versions[0])
            submenu = NestedVersionQMenu(
                self._rv_mode,
                menu,
                "Compare with Asset",
                versions,
                ["entity.Asset.sg_asset_type", "entity.Asset.code"])

            menu.addMenu(submenu)
            if not versions:
                submenu.setEnabled(False)
        else:
            submenu = menu.addMenu("Compare with Asset")
            submenu.setEnabled(False)

    def _add_compare_with_approved_version(self, menu, versions):
        """
        Create context menu for "Approved" Versions related to given Version(s)

        :param menu: `QMenu`
        :param versions: `list` of Version dicts
        :return: `QMenu`
        """
        if len(versions) == 1:
            versions =self._rv_mode._get_approved_versions(versions[0])
            submenu = NestedVersionQMenu(
                self._rv_mode,
                menu,
                "Compare with Approved",
                versions,
                ["sg_task.Task.step.Step.code", "sg_task.Task.content"],
                truncate=True
            )

            menu.addMenu(submenu)
            if not versions:
                submenu.setEnabled(False)
        else:
            submenu = menu.addMenu("Compare with Approved")
            submenu.setEnabled(False)

    def _add_compare_with_latest_version(self, menu, versions):
        """
        Create context menu for latest Versions related to given Version(s)

        :param menu: `QMenu`
        :param versions: `list` of Version dicts
        :return: `QMenu`
        """
        if len(versions) == 1:
            versions = self._rv_mode._get_latest_versions(versions[0])
            submenu = NestedVersionQMenu(
                self._rv_mode,
                menu,
                "Compare with Latest",
                versions,
                ["sg_task.Task.step.Step.code", "sg_task.Task.content"],
                truncate=True
            )

            menu.addMenu(submenu)
            if not versions:
                submenu.setEnabled(False)
        else:
            submenu = menu.addMenu("Compare with Latest")
            submenu.setEnabled(False)

    def _selected_version_entities(self):
        """
        Returns a list of Version entities that are currently selected.

        I have a hunch this already exists somewhere, but I can't find it.
            -- @jburnell
        """
        selection_model = self.tray_list.selectionModel()
        indexes = selection_model.selectedIndexes()
        entities = []

        for i in indexes:
            entity = shotgun_model.get_sg_data(i)
            entities.append(entity)

        return entities
