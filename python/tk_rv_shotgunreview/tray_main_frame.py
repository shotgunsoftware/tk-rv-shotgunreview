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

    def set_rv_mode(self, rv_mode):
        """
        reference to application state
        """
        self._rv_mode = rv_mode
        self.tray_list.rv_mode = rv_mode

    def init_ui(self):
        # self.setMinimumSize(QtCore.QSize(1255,140))
        self.setObjectName('tray_frame')
        self.tray_frame_vlayout = QtGui.QVBoxLayout(self)

        # tray button bar
        # self.tray_button_bar = QtGui.QFrame(self.tray_dock)
        self.tray_button_bar = QtGui.QFrame()
        
        # self.tray_button_bar.setStyleSheet('QFrame { background: rgb(0,200,0);}')
        self.tray_button_bar.setObjectName('tray_button_bar')
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)


        self.tray_button_bar.setSizePolicy(sizePolicy)

        self.tray_button_bar_hlayout = QtGui.QHBoxLayout(self.tray_button_bar)
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

        self.tray_button_latest_pipeline = QtGui.QPushButton()
        self.tray_button_latest_pipeline.setText('Latest in Pipeline')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_latest_pipeline)

        self.tray_button_approved = QtGui.QPushButton()
        self.tray_button_approved.setText('Approved')
        self.tray_button_bar_hlayout.addWidget(self.tray_button_approved)

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


