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
# from .tray_dock_dragbar import TrayDockDragbar

import os
import tank
task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")

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
            # tbar = TrayDockDragbar(self.tray_dock.parent(), self.tray_dock)
            # tbar.setMinimumSize(QtCore.QSize(720,50))
            # self.tray_dock.setTitleBarWidget(tbar)
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
        # self.tray_dock.setTitleBarWidget(QtGui.QWidget(self.tray_dock.parent()))
        pass

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
        self.tray_mini_label.setText('-2+2')
        self.tray_button_bar_hlayout.addWidget(self.tray_mini_label)

        # arrow down button
        self.down_arrow_button = QtGui.QPushButton()
        # self.down_arrow_button.setStyleSheet( 'QPushButton { background: #ff0000;}' )
        self.down_arrow_button.setObjectName("down_arrow_button")
        self.down_arrow_button.setFixedSize(12,12)
        self.down_arrow_button.setContentsMargins(0,0,0,0)
        self.down_arrow_button.setMaximumSize( QtCore.QSize(10,10) )
        self.down_arrow_button.setMinimumSize( QtCore.QSize(10,10) )

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.down_arrow_button.setSizePolicy(sizePolicy)

        # :tk-rv-shotgunreview/arrow.png);
        # XXX - sb - using the above stype didnt work. there's more to it than
        #            just placing a file in with the others. 

        self.down_arrow_button.setIconSize(QtCore.QSize(10,10))

        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arrow_smaller.png")
        icon = QtGui.QIcon( f )

        self.down_arrow_button.setIcon(icon)
        self.tray_button_bar_hlayout.addWidget(self.down_arrow_button)
 
        self.tray_button_bar_hlayout.addStretch(1)

        self.pipeline_filter_button = QtGui.QPushButton()
        self.pipeline_filter_button.setText('Filter by Pipeline')
        self.tray_button_bar_hlayout.addWidget(self.pipeline_filter_button)

        self.status_filter_button = QtGui.QPushButton()
        self.status_filter_button.setText('Filter by Status')
        self.tray_button_bar_hlayout.addWidget(self.status_filter_button)

        self.close_button = QtGui.QToolButton()
        self.float_button = QtGui.QToolButton()
        self.close_button.setObjectName("tray_close_button")
        self.float_button.setObjectName("tray_float_button")
        self.close_button.setAutoRaise(True)
        self.float_button.setAutoRaise(True)
        self.float_button.setCheckable(True)

        # For whatever reason, defining this style in the tray_dock.qss
        # file doesn't work here. Doing it directly onto the buttons as
        # a result.
        self.close_button.setStyleSheet("min-width: 8px; min-height: 8px")
        self.float_button.setStyleSheet("min-width: 8px; min-height: 8px")
        self.close_button.setIconSize(QtCore.QSize(8,8))
        self.float_button.setIconSize(QtCore.QSize(8,8))

        # We're taking over the responsibility of handling the title bar's
        # typical responsibilities of closing the dock and managing float
        # and unfloat behavior. We need to hook up to the dockLocationChanged
        # signal because a floating DockWidget can be redocked with a
        # double click of the window, which won't go through our button.
        self.float_button.clicked.connect(self.toggle_floating)
        self.close_button.clicked.connect(self.hide_dock)
        self.tray_dock.dockLocationChanged.connect(self.dock_location_changed)

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

        # The buttons will be stacked vertically, with the close button
        # even with the button bar at the top of the tray, and the float
        # button immediately below it.
        self.tray_button_bar_grid.addWidget(self.close_button, 0, 1)
        self.tray_button_bar_grid.addWidget(self.float_button, 1, 1)

        self.tray_frame_vlayout.addWidget(self.tray_button_bar)
        self.tray_frame_vlayout.setStretchFactor(self.tray_button_bar, 1)
        
        # QListView ##########################
        #####################################################################
        self.tray_list = QtGui.QListView()
        self.tray_list.rv_mode = self._rv_mode
        self.tray_list.setFocusPolicy(QtCore.Qt.NoFocus)
                
        self.tray_frame_vlayout.addWidget(self.tray_list)
        
        from .tray_model import TrayModel
        self.tray_model = TrayModel(self.tray_list, bg_task_manager=self._task_manager, engine=self._rv_mode._app.engine)

        from .tray_sort_filter import TraySortFilter
        self.tray_proxyModel =  TraySortFilter(self.tray_list)
        self.tray_proxyModel.setSourceModel(self.tray_model)

        self.tray_list.setModel(self.tray_proxyModel)
        self.tray_proxyModel.setDynamicSortFilter(True)

        self.tray_delegate = RvTrayDelegate(self.tray_list)
        self.tray_list.setItemDelegate(self.tray_delegate)

        self.tray_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tray_list.setFlow(QtGui.QListView.LeftToRight)
        self.tray_list.setUniformItemSizes(True)
                
        self.tray_list.setObjectName("tray_list")

        self.mc_widget = MiniCutWidget(self)
        self.mc_widget.setVisible(False)
        self.tray_dock.mc_widget = self.mc_widget
        # know thy tray
        self.mc_widget.tray_dock = self.tray_dock
       


