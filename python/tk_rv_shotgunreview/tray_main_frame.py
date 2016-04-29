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
import tank
task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")

class TrayMainFrame(QtGui.QFrame):

    def __init__(self, parent):
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

        self._rv_mode = None

        self._task_manager = task_manager.BackgroundTaskManager(parent=self,
                                                                start_processing=True,
                                                                max_threads=2)
        
        # set up the UI
        self.init_ui()

        #self._task_manager.task_completed.connect(self.on_task_complete)
        #self._task_manager.task_group_finished.connect(self.on_task_group_finished)
        #self._task_manager.task_failed.connect(self.on_task_failed)


    def on_task_complete(self, uid, group, result):
        """
        result is the result set from the query
        """
        print "TASK COMPLETE - uid: %r group: %r result: %r" %( uid, group, result)

    def on_task_group_finished(self, group):
        print "TASK GROUP FINISHED: %r" % group

    def on_task_failed(self, uid, group, message, traceback_str):
        print "TASK FAILED!! %r" % message

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
            self.close_button.hide()
            self.float_button.hide()
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
        trigger removing the default title bar and forcing a show of
        the replacement buttons that this frame provides to handle
        the title bar's typical responsibilities.
        """
        self.tray_dock.setTitleBarWidget(QtGui.QWidget(self.tray_dock.parent()))
        self.close_button.show()
        self.float_button.show()

    def init_ui(self):
        # self.setMinimumSize(QtCore.QSize(1255,140))
        self.setObjectName('tray_frame')
        self.tray_frame_vlayout = QtGui.QVBoxLayout(self)

        # tray button bar
        # self.tray_button_bar = QtGui.QFrame(self.tray_dock)
        self.tray_button_bar = QtGui.QFrame()
        self.tray_button_bar_grid = QtGui.QGridLayout(self.tray_button_bar)
        self.tray_button_bar_grid.setContentsMargins(0, 0, 0, 0)
        self.tray_button_bar_grid.setHorizontalSpacing(8)
        self.tray_button_bar_grid.setVerticalSpacing(0)
        
        # self.tray_button_bar.setStyleSheet('QFrame { background: rgb(0,200,0);}')
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
        

        bar = QtGui.QPushButton()
        bar.setText('|')
        self.tray_button_bar_hlayout.addWidget(bar)


        self.tray_button_mini_cut = QtGui.QPushButton()
        self.tray_button_mini_cut.setText('Mini Cut')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_mini_cut)


        self.mini_left_spinner = QtGui.QSpinBox()
        self.mini_left_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mini_left_spinner.setValue(2)
        self.tray_button_bar_hlayout.addWidget(self.mini_left_spinner)

        left_label = QtGui.QLabel()
        left_label.setText('Before')
        self.tray_button_bar_hlayout.addWidget(left_label)

        self.mini_right_spinner = QtGui.QSpinBox()
        self.mini_right_spinner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.mini_right_spinner.setValue(2)
        self.tray_button_bar_hlayout.addWidget(self.mini_right_spinner)

        right_label = QtGui.QLabel()
        right_label.setText('After')
        self.tray_button_bar_hlayout.addWidget(right_label)

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
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock_hover.png"),
            QtGui.QIcon.Active,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On,
        )
        self.float_icon.addPixmap(
            QtGui.QPixmap(":/tk-rv-shotgunreview/undock_hover.png"),
            QtGui.QIcon.Selected,
            QtGui.QIcon.On,
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
        self.tray_list.setFocusPolicy(QtCore.Qt.NoFocus)
                
        self.tray_frame_vlayout.addWidget(self.tray_list)
        #self.tray_frame_vlayout.setStretchFactor(self.tray_list, 1)
        
        from .tray_model import TrayModel
        self.tray_model = TrayModel(self.tray_list, bg_task_manager=self._task_manager)

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
       
        # st = "QListView { border: none;}"
        # self.setStyleSheet(st)


