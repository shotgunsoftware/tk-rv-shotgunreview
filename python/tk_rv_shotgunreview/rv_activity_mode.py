# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import types
import os
import math

import rv
import rv.qtutils

import tank
from tank.platform.qt import QtGui, QtCore

shotgun_view = tank.platform.import_framework(
    "tk-framework-qtwidgets",
    "views",
)

shotgun_model = tank.platform.import_framework(
    "tk-framework-shotgunutils",
    "shotgun_model",
)

from .version_list_delegate import RvVersionListDelegate
from .shot_info_delegate import RvShotInfoDelegate
from .tray_delegate import RvTrayDelegate
from .tray_model import TrayModel
from .shot_info_widget import ShotInfoWidget

class RvActivityMode(rv.rvtypes.MinorMode):
    def __init__(self):
        rv.rvtypes.MinorMode.__init__(self)

        self._note_dock = None
        self._tray_dock = None
        self._tab_widget = None
        self._shot_info = None
        self._task_manager = None

        self.init(
            "RvActivityMode",
            None,
            [ 
                ("after-session-read", self.afterSessionRead, ""),
                ("before-session-read", self.beforeSessionRead, ""),
                ("after-graph-view-change", self.viewChange, ""),
                ("frame-changed", self.frameChanged, ""),
                ("incoming-source-path", self.sourcePath, ""),
                ("source-group-complete", self.sourceGroupComplete, ""),
                ("graph-state-change", self.graphStateChange, "")
            ],
            None,
            None,
        )

        rv.extra_commands.toggleFullScreen()

    #####################################################################################
    # Properties

    @property
    def note_dock(self):
        return self._note_dock

    @property
    def shot_info(self):
        return self._shot_info

    @property
    def tab_widget(self):
        return self._tab_widget

    @property
    def task_manager(self):
        return self._task_manager

    @property
    def tray_dock(self):
        return self._tray_dock

    #####################################################################################
    # RV Event Handlers

    def beforeSessionRead (self, event):
        event.reject()
        self._readingSession = True

    def afterSessionRead (self, event):
        event.reject()
        self._readingSession = False

    def inputsChanged(self, event):
        event.reject()

        try:
            file_source = rv.commands.nodesOfType("#RVSource")
            prop_name = "%s.%s" % (file_source[0], "tracking.info")
            tl = rv.commands.getStringProperty(prop_name)
            tracking_info = dict()
            
            for i in range(0,len(tl)-1, 2):
                tracking_info[tl[i]] = tl[i+1]

            # make an entity
            entity = dict()
            entity["type"] = "Version"
            entity["id"] = int(tracking_info['id'])
            if event.contents() == "viewGroup":
                self.load_data(entity)
        except Exception:
            pass

    def viewChange(self, event):
        event.reject()

    def frameChanged(self, event):
        event.reject()

    def sourcePath(self, event):
        event.reject()

    def graphStateChange(self, event):
        event.reject()

        if "tracking.info" in event.contents():
            try:
                tl = rv.commands.getStringProperty(event.contents())
                if "infoStatus" not in event.contents():
                    tracking_info = dict()
                    
                    for i in range(0,len(tl)-1, 2):
                        tracking_info[tl[i]] = tl[i+1]
                    
                    # make an entity
                    entity = {}
                    entity["type"] = "Version"
                    entity["id"] = int(tracking_info['id'])
                    
                    self.load_data(entity)
                    # self._version_activity_stream.ui.shot_info_widget.load_data_rv(tracking_info)

                    s = tracking_info['shot']
                    (s_id, s_name, s_type) = s.split('|')
                    (n, shot_id) = s_id.split('_')

                    # display VERSION info not parent shot info
                    # shot_filters = [ ['id','is', entity['id']] ]
                    # self._shot_info_model.load_data(entity_type="Version", filters=shot_filters)

                    # version_filters = [ ['project','is', {'type':'Project','id':71}],
                    #     ['entity','is',{'type':'Shot','id': int(shot_id) }] ]
                    version_filters = [
                        ['entity', 'is', {'type':'Shot', 'id': int(shot_id)}],
                    ]

                    self._version_model.load_data(
                        entity_type="Version",
                        filters=version_filters,
                    )
            except Exception:
                pass

    def sourceGroupComplete(self, event):
        event.reject()

        args = event.contents().split(";;")
        group = args[0]
        file_source = self.group_member_of_type(group, "RVFileSource")
        prop_name = "%s.%s" % (file_source, "tracking.info")

        try:
            tl = rv.commands.getStringProperty(prop_name)
            tracking_info = dict()
            
            for i in range(0,len(tl)-1, 2):
                tracking_info[tl[i]] = tl[i+1]
            
            # make an entity
            entity = {}
            entity["type"] = "Version"
            entity["id"] = int(tracking_info['id'])
            
            s = tracking_info['shot']
            (s_id, s_name, s_type) = s.split('|')
            (n, shot_id) = s_id.split('_')

            self.load_data(entity)
            
            # shot_filters = [ ['id','is', int(shot_id)] ]
            # self._shot_info_model.load_data(entity_type="Shot", filters=shot_filters)
            # self._version_activity_stream.ui.shot_info_widget.load_data_rv(tracking_info)

            version_filters = [
                ['project','is', {'type':'Project','id':71}],
                ['entity','is', {'type':'Shot','id': int(shot_id)}],
            ]

            self._version_model.load_data(
                entity_type="Version",
                filters=version_filters,
            )
        except Exception:
            pass

    def load_data(self, entity):
        # our session property is called tracking
        # tracking_str = rv.commands.getStringProperty('sourceGroup000001_source.tracking.info ')
        self._version_activity_stream.load_data(entity)
        shot_filters = [ ['id','is', entity['id']] ]
        self._shot_info_model.load_data(entity_type="Version", filters=shot_filters)

    #####################################################################################
    # UI Initialization

    def init_ui(self, note_dock, tray_dock):
        self._note_dock = note_dock
        self._tray_dock = tray_dock

        # Setup Tab widget with notes and versions, then setup the tray. 
        self._tab_widget = QtGui.QTabWidget()
        self.tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab_widget.setObjectName("tab_widget")
        
        activity_stream = tank.platform.import_framework(
            "tk-framework-qtwidgets",
            "activity_stream",
        )

        self._activity_tab_frame = QtGui.QWidget(self.note_dock)
        
        self._notes_container_frame = QtGui.QFrame(self._activity_tab_frame)
        self.cf_verticalLayout = QtGui.QVBoxLayout()
        self.cf_verticalLayout.setObjectName("cf_verticalLayout")
        self._notes_container_frame.setLayout(self.cf_verticalLayout)

        self._shot_info = QtGui.QListView()
        self.cf_verticalLayout.addWidget(self.shot_info)
        # self._version_activity_stream.ui.verticalLayout.addWidget(self.shot_info)
        
        self._shot_info_model = shotgun_model.SimpleShotgunModel(self._activity_tab_frame)
        self.shot_info.setModel(self._shot_info_model)

        self._shot_info_delegate = RvShotInfoDelegate(self.shot_info)
        self.shot_info.setItemDelegate(self._shot_info_delegate)

        self.shot_info.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.shot_info.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.shot_info.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.shot_info.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.shot_info.setUniformItemSizes(True)
        self.shot_info.setObjectName("shot_info")

        self.shot_info.setMinimumSize(ShotInfoWidget.calculate_size())
        si_size = ShotInfoWidget.calculate_size()
        self.shot_info.setMaximumSize(QtCore.QSize(si_size.width() + 10, si_size.height() + 10))
        
        shot_filters = [ ['id','is', 1161] ]
        self._shot_info_model.load_data(entity_type="Shot", filters=shot_filters, fields=["code", "link"])

        self._version_activity_stream = activity_stream.ActivityStreamWidget(self._notes_container_frame)
        self.cf_verticalLayout.addWidget(self._version_activity_stream)

        self.tab_widget.setStyleSheet(
            "QWidget { "
                "font-family: Proxima Nova; "
                "font-size: 16px; "
                "background: rgb(36,38,41); "
                "color: rgb(126,127,129); "
                "border-color: rgb(36,38,41);} "
            "QTabWidget::tab-bar { "
                "alignment: center; "
                "border: 2px solid rgb(236,38,41); } "
            "QTabBar::tab { "
                "border: 2px solid rgb(36,38,41); "
                "alignment: center; "
                "background: rgb(36,38,41); "
                "margin: 4px; "
                "color: rgb(126,127,129); } "
            "QTabBar::tab:selected { "
                "color: rgb(40,136,175)} "
            "QTabWidget::pane { "
                "border-top: 2px solid rgb(66,67,69); }"
        )

        task_manager = tank.platform.import_framework(
            "tk-framework-shotgunutils",
            "task_manager",
        )

        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self._version_activity_stream,
            start_processing=True,
            max_threads=2,
        )
        
        shotgun_globals = tank.platform.import_framework(
            "tk-framework-shotgunutils",
            "shotgun_globals",
        )

        shotgun_globals.register_bg_task_manager(self._task_manager)        
        self._version_activity_stream.set_bg_task_manager(self._task_manager)

        self._entity_version_tab = QtGui.QWidget()
        self._entity_version_tab.setObjectName("entity_version_tab")
        
        self._vertical_layout = QtGui.QVBoxLayout(self._entity_version_tab)
        self._vertical_layout.setContentsMargins(0, 0, 0, 0)
        self._vertical_layout.setObjectName("vertical_layout")
        
        self._entity_version_view = QtGui.QListView(self._entity_version_tab)
        self._entity_version_view.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self._entity_version_view.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self._entity_version_view.setUniformItemSizes(True)
        self._entity_version_view.setObjectName("entity_version_view")

        self._version_delegate = RvVersionListDelegate(self._entity_version_view)
        self._version_model = shotgun_model.SimpleShotgunModel(self._entity_version_tab)

        # Tell the view to pull data from the model.
        self._entity_version_view.setModel(self._version_model)
        self._entity_version_view.setItemDelegate(self._version_delegate)
        
        self._vertical_layout.addWidget(self._entity_version_view)

        self._version_activity_tab = QtGui.QWidget()
        self._version_activity_tab.setObjectName("version_activity_tab")
        
        self._version_activity_stream.setObjectName("version_activity_stream")
        
        self._tools_tab = QtGui.QWidget()
        self._tools_tab.setObjectName("tools_tab")

        self.tab_widget.addTab(self._notes_container_frame, "NOTES")                
        self.tab_widget.addTab(self._entity_version_tab, "VERSIONS")
        self.tab_widget.addTab(self._tools_tab, "TOOLS")

        self.note_dock.setWidget(self.tab_widget)

        # Setup the lower tray.
        self._tray_list = QtGui.QListView(self.tray_dock)
        self._tray_model = TrayModel(self._tray_list)
        self._tray_list.setModel(self._tray_model)

        self._tray_delegate = RvTrayDelegate(self._tray_list)
        self._tray_list.setItemDelegate(self._tray_delegate)

        self._tray_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._tray_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._tray_list.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self._tray_list.setFlow(QtGui.QListView.LeftToRight)
        self._tray_list.setUniformItemSizes(True)
        self._tray_list.setMinimumSize(QtCore.QSize(900,150))
        self._tray_list.setObjectName("tray_list")

        tray_filters = [['sg_cut','is', {'type':'CustomEntity10', 'id': 8}]]
        tray_fields= [
            "sg_cut_in",
            "sg_cut_out",
            "sg_cut_order",
            "sg_version.Version.sg_path_to_frames",
            "sg_version.Version.id",
            "sg_version.Version.sg_first_frame",
            "sg_version.Version.sg_last_frame",
        ]

        self._tray_model.load_data(
            entity_type="CustomEntity11",
            filters=tray_filters,
            fields=tray_fields,
        )

        self._tray_list.clicked.connect(self.tray_clicked)    
        self._tray_model.data_refreshed.connect(self.on_data_refreshed)
        self._tray_model.cache_loaded.connect(self.on_cache_loaded)

    #####################################################################################
    # Qt Slots

    def on_cache_loaded(self, stuff):
        pass

    def on_data_refreshed(self, was_refreshed):
        ids = self._tray_model.entity_ids
        our_type =  self._tray_model.get_entity_type()

        #print "ITEM: %r" % self._tray_model.index_from_entity(our_type, ids[0])

        #       sourceNode = rve.nodesInGroupOfType (sources[i], "RVFileSource")[0]
        #       (realMedia,frame) = rvc.sequenceOfFile (shot.file)
        #           seq = rvc.newNode ("RVSequenceGroup")
                # rve.setUIName (seq, self._playlist.name)
                # rvc.setNodeInputs (seq, newSources)
                # rvc.setViewNode (seq)

        #                         self._state = "loading media"
        # self._preSources = rvc.nodesOfType("RVSourceGroup")
        # deb ("calling addSources, media = %s" % media)
        # rvc.addSources(media)

        nums = []
        frames = []
        ins = []
        outs = []
        n = 0
        t = 1
        
        for i in ids:
            item = self._tray_model.index_from_entity(our_type, i)
            sg_item = shotgun_model.get_sg_data(item)
            f = sg_item['sg_version.Version.sg_path_to_frames']

            try:
                rv.commands.addSource(f)
            except Exception:
                pass

            nums.append(n)
            n = n + 1
            ins.append( sg_item['sg_cut_in'] )
            outs.append( sg_item['sg_cut_out'] )
            frames.append(t)
            t = sg_item['sg_cut_out'] - sg_item['sg_cut_in'] + 1 + t
        
        nums.append(0)
        ins.append(0)
        outs.append(0)
        frames.append(t)

        self.cut_seq = rv.commands.newNode("RVSequenceGroup")
        
        # need to get the name into the query...
        rv.extra_commands.setUIName(self.cut_seq, "CUTZ cut")
        names = rv.extra_commands.nodesInGroupOfType(self.cut_seq, 'RVSequence')
        
        k = "%s.mode.autoEDL" % names[0]
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.IntType, 1)

        rv.commands.setIntProperty('%s.edl.source' % names[0], nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % names[0], frames, True)
        rv.commands.setIntProperty('%s.edl.in' % names[0], ins, True)
        rv.commands.setIntProperty('%s.edl.out' % names[0], outs, True)
        rv.commands.setIntProperty("%s.mode.autoEDL" % names[0], [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % names[0], [0])

        sources = rv.commands.nodesOfType("RVSourceGroup")
        rv.commands.setNodeInputs(self.cut_seq, sources)
        rv.commands.setViewNode(self.cut_seq)

    def on_item_changed(curr, prev):
        pass

    def tray_clicked(self, index):
        sg_item = shotgun_model.get_sg_data(index)  
        entity = {}
        entity["type"] = "Version"
        entity["id"] = sg_item['sg_version.Version.id']
        
        # s = tracking_info['shot']
        # (s_id, s_name, s_type) = s.split('|')
        # (n, shot_id) = s_id.split('_')

        self.load_data(entity)
        
        # shot_filters = [ ['id','is', int(shot_id)] ]
        # self._shot_info_model.load_data(entity_type="Shot", filters=shot_filters)

        # version_filters = [ ['project','is', {'type':'Project','id':71}],
        #     ['entity','is',{'type':'Shot','id': int(shot_id)}] ]
        # self._version_model.load_data(entity_type="Version", filters=version_filters)

    #####################################################################################
    # General Utilities

    def activate(self):
        rv.rvtypes.MinorMode.activate(self)

    def deactivate(self):
        rv.rvtypes.MinorMode.deactivate(self)

    @staticmethod
    def group_member_of_type(node, memberType):
        for n in rv.commands.nodesInGroup(node):
            if rv.commands.nodeType(n) == memberType:
                return n
        return None

