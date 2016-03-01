from PySide.QtCore import QTimer, SIGNAL
from PySide import QtGui, QtCore

import types
import os
import math
import rv
import rv.qtutils
import tank

import json

shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

from .tray_delegate import RvTrayDelegate
from .details_panel_widget import DetailsPanelWidget

# isnt it obvious, really?
# there is something about this i dont get?
def groupMemberOfType(node, memberType):
    for n in rv.commands.nodesInGroup(node):
        if rv.commands.nodeType(n) == memberType:
            return n
    return None

class RvActivityMode(rv.rvtypes.MinorMode):
    _RV_DATA_ROLE = QtCore.Qt.UserRole + 99

    
    def check_details(self):
        if self.details_dirty:
            self.load_version_id_from_session()
 
    def load_version_id_from_session(self):
        saf = rv.commands.sourcesAtFrame(rv.commands.frame())
        if saf:
            source_prop_name = ("%s.cut_support.json_sg_data") % str(saf[0])
            if rv.commands.propertyExists(source_prop_name):
                j_data = rv.commands.getStringProperty(source_prop_name)
                if j_data:
                    try:
                        sg_data = json.loads(str(j_data[0]))
                        print "INFO: version_id is %d" % sg_data['version.Version.id']
                        entity = {}
                        entity["type"] = "Version"
                        entity["id"] = sg_data['version.Version.id']
                        if self.version_id != entity['id']:
                            self.load_data(entity)
                            self.details_dirty = False
                        return sg_data

                    except Exception as e:
                        self.details_dirty = True
                        print "ERROR: get_version_id_from_session JSON EXCEPTION %r" % e
        else:
            print "ERROR: NO SAF?"
        return None


    def beforeSessionRead (self, event):
        # print "################### beforeSessionRead"
        event.reject()

        self._readingSession = True

    def afterSessionRead (self, event):
        # print "################### afterSessionRead"
        event.reject()

        self._readingSession = False
#        rv.extra_commands.toggleFullScreen()


    def inputsChanged(self, event):
        #pass
        print "################### inputsChanged %r" % event
        # print event.contents()
        event.reject()
        self.details_dirty = True

    def viewChange(self, event):
        #pass
        print "################### viewChange %r" % event
        print "contents %r" % event.contents()
        event.reject()
        #self.details_dirty = True
        self.load_version_id_from_session()


    def frameChanged(self, event):
        event.reject()
        try:

            saf = rv.commands.sourcesAtFrame(rv.commands.frame())
            if saf:
                source_prop_name = ("%s.cut_support.json_sg_data") % str(saf[0])
                if rv.commands.propertyExists(source_prop_name):
                    j_data = rv.commands.getStringProperty(source_prop_name)
                    if j_data:
                        try:
                            sg_data = json.loads(str(j_data[0]))
                            if sg_data['version.Version.id'] != self.version_id:
                                print "INFO: version_id is %d" % sg_data['version.Version.id']
                                entity = {}
                                entity["type"] = "Version"
                                entity["id"] = sg_data['version.Version.id']
                                self.load_data(entity)
                                self.version_id = sg_data['version.Version.id']

                        except Exception as e:
                            print "ERROR: frameChanged JSON EXCEPTION %r" % e
        

            # this then is all TRAY code.
            # we extract the version id FROM the tray here and thusly FROM Toolkit FROM the DB.
            #####################################################################################
            if rv.commands.propertyExists('%s.edl.frame' % self.cut_seq_name):
                tl = rv.commands.getIntProperty('%s.edl.frame' % self.cut_seq_name)
                n = 0
                for x in tl:
                    if rv.commands.frame() < x:
                        break 
                    n = n + 1              

                sel_index = self.tray_model.index(n-1, 0)
                sels = self.tray_list.selectionModel().selectedIndexes()[0]
                if sels != sel_index:
                    sm = self.tray_list.selectionModel()           
                    sm.select(sel_index, sm.ClearAndSelect)
                    self.tray_list.scrollTo(sel_index, QtGui.QAbstractItemView.PositionAtCenter)
            
        except Exception as e:
            print "ERROR: RV frameChanged EXCEPTION %r" % e

    def sourcePath(self, event):
        
        print "################### sourcePath %r" % event
        # print event.contents()
        event.reject()

    # why does cut_tracking from in contents?
    def graphStateChange(self, event):
        print "################### graphStateChange %r" % event
        # print event.contents()
        event.reject()
        self.details_dirty = True

    # this ASSUMES cut_tracking ALREADY EXISTS
    def sourceGroupComplete(self, event):
        print "################### sourceGroupComplete %r" % event
        #print event.contents()
        # this event shows up with some built in goodness in contents.
        # below are some nice things i stole from Jon about how to 
        # dig info out of whats there
        event.reject()

        args         = event.contents().split(";;")
        group        = args[0]
        fileSource   = groupMemberOfType(group, "RVFileSource")

        # i guess im not using the rest of these yet
        imageSource  = groupMemberOfType(group, "RVImageSource")
        source       = fileSource if imageSource == None else imageSource
        typeName     = rv.commands.nodeType(source)
        fileNames    = rv.commands.getStringProperty("%s.media.movie" % source, 0, 1000)
        fileName     = fileNames[0]
        ext          = fileName.split('.')[-1].upper()
        mInfo        = rv.commands.sourceMediaInfo(source, None)
        # print "group: %s fileSource: %s fileName: %s" % (group, fileSource, fileName)

        source_prop_name = ("%s.cut_support.json_sg_data") % source
        if rv.commands.propertyExists(source_prop_name):
            j_data = rv.commands.getStringProperty(source_prop_name)
            if j_data:
                try:
                    sg_data = json.loads(str(j_data[0]))
                    if sg_data['version.Version.id'] != self.version_id:
                        print "INFO: version_id is %d" % sg_data['version.Version.id']
                        entity = {}
                        entity["type"] = "Version"
                        entity["id"] = sg_data['version.Version.id']
                        self.load_data(entity)

                except Exception as e:
                    print "ERROR: RV JSON EXCEPTION %r" % e

    def on_view_size_changed(self, event):
        event.reject()
        traysize = self.tray_dock.size().width()
        self.tray_main_frame.resize(traysize - 10, self._tray_height)

    def __init__(self, app):
        rv.rvtypes.MinorMode.__init__(self)
        
        self.note_dock = None
        self.tray_dock = None
        self.tab_widget = None
        self.mini_cut = False
        self.detail_version_id = None
        self._tray_height = 140
        self.last_mini_center = None

        # RV specific
        # the current sequence node
        self.cut_seq_node = None
        self.loaded_sources = {}
        # self._tracking_info= {}
        self.version_id = -1 

        self._app = app

        self.init("RvActivityMode", None,
                [ 
                ("after-session-read", self.afterSessionRead, ""),
                ("before-session-read", self.beforeSessionRead, ""),
                # ("source-group-complete", self.sourceSetup, ""),
                ("after-graph-view-change", self.viewChange, ""),
                ("frame-changed", self.frameChanged, ""),
                ("graph-node-inputs-changed", self.inputsChanged, ""),
                # ("incoming-source-path", self.sourcePath, ""),
                ("source-group-complete", self.sourceGroupComplete, ""),
                ("graph-state-change", self.graphStateChange, ""),
                ('id_from_gma', self.on_id_from_gma, ""),
                ('view-size-changed', self.on_view_size_changed, ''),
                ],
                None,
                None);
        
    def activate(self):
        rv.rvtypes.MinorMode.activate(self)

    def deactivate(self):
        rv.rvtypes.MinorMode.deactivate(self)
   
    # meant to be the one that rules them all
    def load_timeline(self, start_row, end_row, add_source=False):
        print "load_timeline:"
        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        ids = self.tray_model.entity_ids
        our_type =  self.tray_model.get_entity_type()

        source_nums = []
        frames = []
        ins = []
        outs = []
        
        n = ids[start_row]
        t = 1
        
        for i in ids[start_row:end_row]:
            item = self.tray_model.index_from_entity(our_type, i)
            sg_item = shotgun_model.get_sg_data(item)
            f = sg_item['version.Version.sg_path_to_frames']
            if add_source:
                rv.commands.addSource(f)
            source_nums.append(n)
            n = n + 1
            ins.append( sg_item['cut_item_in'] )
            outs.append( sg_item['cut_item_out'] )
            frames.append(t)
            t = sg_item['cut_item_out'] - sg_item['cut_item_in'] + 1 + t
        
        source_nums.append(0)
        ins.append(0)
        outs.append(0)
        frames.append(t)

        if add_source:
            self.rv_source_nums = source_nums
            self.rv_frames = frames
            self.rv_ins = ins
            self.rv_outs = outs

        self.cut_seq_node = rv.commands.newNode("RVSequenceGroup")
        
        # need to get the name into the query...
        rv.extra_commands.setUIName(self.cut_seq_node, "CUTZ cut")
        self.cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq_node, 'RVSequence')[0]

        k = "%s.mode.autoEDL" % str(self.cut_seq_name)
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.IntType, 1)
               
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        sources = rv.commands.nodesOfType("RVSourceGroup")
        rv.commands.setNodeInputs(self.cut_seq_node, sources[start_row:end_row])
        rv.commands.setViewNode(self.cut_seq_node)

        self.tray_list.setCurrentIndex(self.tray_model.createIndex(n-1, 0))
            

################################################################################### qt stuff down here. 

    def load_data(self, entity):
        self.version_id = entity['id']
        self.details_panel.load_data(entity)
        self.details_dirty = False
 
    def init_ui(self, note_dock, tray_dock, version_id):
        self.note_dock = note_dock
        self.tray_dock = tray_dock
        
        # Setup the details panel.
        self.details_panel = DetailsPanelWidget()
        self.note_dock.setWidget(self.details_panel)
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

        self.tray_dock.setMinimumSize(QtCore.QSize(1355,self._tray_height))
        # ug, for now till i can clean up the methods
        from .tray_main_frame import TrayMainFrame
        self.tray_main_frame = TrayMainFrame(self.tray_dock)
        
        # just map these back for the moment...
        self.tray_model = self.tray_main_frame.tray_model
        self.tray_proxyModel = self.tray_main_frame.tray_proxyModel
        self.tray_delegate = self.tray_main_frame.tray_delegate
        self.tray_list = self.tray_main_frame.tray_list
        self.tray_button_entire_cut = self.tray_main_frame.tray_button_entire_cut
        self.tray_button_mini_cut = self.tray_main_frame.tray_button_mini_cut
        self.tray_button_browse_cut = self.tray_main_frame.tray_button_browse_cut
        
        self.tray_model.data_refreshed.connect(self.on_data_refreshed)
        self.tray_model.cache_loaded.connect(self.on_cache_loaded)
        self.tray_list.clicked.connect(self.tray_clicked)
        self.tray_list.activated.connect(self.tray_activated)
        self.tray_list.doubleClicked.connect(self.tray_double_clicked)

        self.tray_button_entire_cut.clicked.connect(self.on_entire_cut)
        self.tray_button_mini_cut.clicked.connect(self.on_mini_cut)
        
        self.tray_button_browse_cut.clicked.connect(self.on_browse_cut)
        self.tray_main_frame.tray_button_latest_pipeline.clicked.connect(self.load_sequence_with_versions)

        self.load_tray_with_cut_id(1)

        self.details_timer = QTimer()
        self.note_dock.connect(self.details_timer, SIGNAL("timeout()"), self.check_details)
        self.details_timer.start(1000)


    def on_browse_cut(self):
        # forcing a test....
        entity = {}
        entity['id'] = 6
        entity['type'] = 'Cut'
        rv.commands.sendInternalEvent('id_from_gma', json.dumps(entity))        
        # self.load_tray_with_cut_id(6)

    def on_id_from_gma(self, event):
        print "on_id_from_gma %r" % event.contents()
        try:
            d = json.loads(event.contents())
            if d['type'] == "Cut":
                self.load_tray_with_cut_id(d['id'])
        except Exception as e:
            print "ERROR: on_id_from_gma %r" % e

    def load_sequence_with_versions(self):
        # versions will be a string at some point
        e = [{'id': 6006, 'type': 'Version'}, {'id': 6025, 'type': 'Version'}, {'id': 6060, 'type': 'Version'}]
        print e
        # for i in e:

        #     v_filters = [ ['version','is', {'type':'Version', 'id': i }] ]

        #     v_fields= [
        #             "sg_path_to_frames",
        #             "sg_first_frame", "sg_last_frame", 
        #             "image"
        #             ]

            #self.v_model.load_data(entity_type="Version", filters=v_filters, fields=v_fields)


    def load_tray_with_cut_id(self, cut_id=None):
        if cut_id:
            self.tray_cut_id = cut_id
        
        tray_filters = [ ['cut','is', {'type':'Cut', 'id': self.tray_cut_id }] ]

        tray_fields= ["cut_item_in", "cut_item_out", "cut_order", 
                "version.Version.sg_path_to_frames", "version.Version.id",
                "version.Version.sg_first_frame", "version.Version.sg_last_frame", 
                "version.Version.image", "cut.Cut.code", "cut.Cut.id"]

        orders = [{'field_name':'cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CutItem", filters=tray_filters, fields=tray_fields, order=orders)
        
        if self.mini_cut:
            self.on_entire_cut()


    def on_entire_cut(self):
        print "ON ENTIRE CUT"
        self.mini_cut = False
        self.tray_list.mini_cut = False
        #e_ids = self.tray_model.entity_ids
        #e_type = self.tray_model.get_entity_type()
        
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        #sources = rv.commands.nodesOfType("RVSourceGroup")
        #rv.commands.setNodeInputs(self.cut_seq_node, sources)
        rv.commands.setViewNode(self.cut_seq_node)

        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')

    def on_mini_cut(self):
        print "ON MINI CUT"
        # print "current selection: %r" % self.tray_list.currentIndex()
        self.mini_cut = True
        self.tray_list.mini_cut = True
        # get current selection
        # cur_index = self.tray_list.currentIndex()
        if self.last_mini_center:
            self.load_mini_cut(self.last_mini_center)
            self.tray_list.selectionModel().select(self.last_mini_center, self.tray_list.selectionModel().ClearAndSelect)
        
        else:
            self.load_mini_cut(self.tray_list.currentIndex())

        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')

    def on_cache_loaded(self):
        print "CACHE LOADED"

    def on_data_refreshed(self, was_refreshed):
        print "ON_DATA_REFRESHED: %r" % was_refreshed
        v_id = -1
        # first see if we have a selection
        cur_index = self.tray_list.currentIndex()
        if cur_index:
            sg_item = shotgun_model.get_sg_data(cur_index)
            if sg_item:
                v_id = sg_item['version.Version.id']

        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        rows = self.tray_proxyModel.rowCount()
 
        ids = self.tray_model.entity_ids
        our_type =  self.tray_model.get_entity_type()

        self.rv_source_nums = []
        self.rv_frames = []
        self.rv_ins = []
        self.rv_outs = []
        sources = []

        n = 0
        t = 1

        cut_name = None
        final_selection = None

        for x in range(0, rows):
            item = self.tray_proxyModel.index(x, 0)
            sg_item = shotgun_model.get_sg_data(item)
            print sg_item
            f = sg_item['version.Version.sg_path_to_frames']
            if f in self.loaded_sources:
                source_name = self.loaded_sources[f]
            else:
                source_name = rv.commands.addSourceVerbose([f])
                self.loaded_sources[f] = source_name
           
            source_prop_name = ("%s.cut_support.json_sg_data") % source_name
            try:
                sg_item['ui_index'] = n
                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)
                json_sg_item = json.dumps(sg_item)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                print "ERROR: on_data_refreshed %r" % e

            # get the source id number...
            (num_plus, _) = source_name.split('_')
            sources.append(num_plus)
            
            ( _, nu) = num_plus.split('p')
            # it does not appear that the source array is anyting but sequential from zero
            #n = int(nu)

            self.rv_source_nums.append(n)
            n = n + 1

            self.rv_ins.append( sg_item['cut_item_in'] )
            self.rv_outs.append( sg_item['cut_item_out'] )
            self.rv_frames.append(t)
            
            t = sg_item['cut_item_out'] - sg_item['cut_item_in'] + 1 + t
            cut_name = sg_item['cut.Cut.code']
            if sg_item['version.Version.id'] == v_id:
                final_selection = item
        
        self.rv_source_nums.append(0)
        self.rv_ins.append(0)
        self.rv_outs.append(0)
        self.rv_frames.append(t)

        self.cut_seq_node = rv.commands.newNode("RVSequenceGroup")
        
        # need to get the name into the query...
        self.tray_main_frame.tray_button_browse_cut.setText(cut_name)
        rv.extra_commands.setUIName(self.cut_seq_node, cut_name)
        self.cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq_node, 'RVSequence')[0]

        k = "%s.mode.autoEDL" % str(self.cut_seq_name)
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.IntType, 1)
                
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        #sources = rv.commands.nodesOfType("RVSourceGroup")
        rv.commands.setNodeInputs(self.cut_seq_node, sources)
        rv.commands.setViewNode(self.cut_seq_node)

        if final_selection:
            self.tray_list.setCurrentIndex(final_selection)
            self.tray_list.selectionModel().select(final_selection, self.tray_list.selectionModel().ClearAndSelect)
        else:            
            zero_index = self.tray_model.createIndex(0, 0)
            self.tray_list.setCurrentIndex(zero_index)
            self.tray_list.selectionModel().select(zero_index, self.tray_list.selectionModel().ClearAndSelect)
        

        sels = self.tray_list.selectionModel().selectedIndexes()[0]
        sg_item = shotgun_model.get_sg_data(sels)

        entity = {}
        entity["type"] = "Version"
        entity["id"] = sg_item['version.Version.id']
        
        self.load_data(entity)
        self.tray_list.scrollTo(item, QtGui.QAbstractItemView.EnsureVisible)

        #rv.extra_commands.toggleFullScreen()
        rv.commands.fullScreenMode(True)
                  
        # this works but maybe i dont need it after all...
    def on_item_changed(curr, prev):
        pass
        # print "item changed"
        # print curr, prev

    def tray_double_clicked(self, index):
        sg_item = shotgun_model.get_sg_data(index)
        single_source = []
        single_frames = []
        single_ins = []
        single_outs = []
        t = 1
        single_source.append(index.row())
        single_ins.append(sg_item['cut_item_in'])
        single_outs.append(sg_item['cut_item_out'])
        single_frames.append(t)
        t = sg_item['cut_item_out'] - sg_item['cut_item_in'] + 1 + t
        single_frames.append(t)
        single_source.append(0)
        single_ins.append(0)
        single_outs.append(0)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, single_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, single_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, single_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        sources = rv.commands.nodesOfType("RVSourceGroup")
        single = [ sources[index.row()] ]
        rv.commands.setNodeInputs(self.cut_seq, single)
        rv.commands.setViewNode(self.cut_seq)
        rv.commands.setFrame(1)
        rv.commands.play()

    def tray_activated(self, index):
        print "Tray Activated! %r" % index

    def load_mini_cut(self, index):
        self.last_mini_center = index

        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        rows = self.tray_proxyModel.rowCount()

        e_ids = self.tray_model.entity_ids
        e_type = self.tray_model.get_entity_type()

        mini_sources = []
        mini_frames = []
        mini_ins = []
        mini_outs = []
        mini_source_names = []
        
        t = 1
        w = 0
        
        rs = max(0,index.row()-2)
        re = min(index.row()+3, rows)

        for x in range(rs, re):
            m_item = self.tray_proxyModel.index(x, 0)
            #m_item = self.tray_model.item_from_entity(e_type, e_ids[x])
            sg = shotgun_model.get_sg_data(m_item)
            #print "%d %r" % (x, sg['version.Version.sg_path_to_frames'])
            source_name = self.loaded_sources[sg['version.Version.sg_path_to_frames']]
            (num_plus, _) = source_name.split('_')
            mini_source_names.append(num_plus)
            #( _, nu) = num_plus.split('p')
            #n = int(nu)

            mini_sources.append(w)
            w = w + 1
            
            mini_ins.append( sg['cut_item_in'] )
            mini_outs.append( sg['cut_item_out'] )
            mini_frames.append(t)
            t = sg['cut_item_out'] - sg['cut_item_in'] + 1 + t
        
        mini_sources.append(0)
        mini_ins.append(0)
        mini_outs.append(0)
        mini_frames.append(t)

        cut_seq_node = rv.commands.newNode("RVSequenceGroup")
        cut_seq_name = rv.extra_commands.nodesInGroupOfType(cut_seq_node, 'RVSequence')[0]

        rv.extra_commands.setUIName(cut_seq_node, "MiniCut-" + cut_seq_name)     
        
        rv.commands.setIntProperty('%s.edl.source' % cut_seq_name, mini_sources, True)
        rv.commands.setIntProperty('%s.edl.frame' % cut_seq_name, mini_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % cut_seq_name, mini_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % cut_seq_name, mini_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % cut_seq_name, [0])

        rv.commands.setNodeInputs(cut_seq_node, mini_source_names)
        rv.commands.setViewNode(cut_seq_node)

    def tray_clicked(self, index):
        print "TRAY_CLICKED %r" % index.row()

        if self.mini_cut:
            # you are in mini cut so center the cut on this index
            # if you were already on that shot stay there
            self.load_mini_cut(index)

        # look and see what source the playhead is on
        # if its not the same as the one in sg_item 
        # then we need to move the playhead

        sg_item = shotgun_model.get_sg_data(index)  
        
        entity = {}
        entity["type"] = "Version"
        entity["id"] = sg_item['version.Version.id']

        ph_version = self.load_version_id_from_session()
        if entity['id'] != ph_version['id']:
            #move the playhead to entity shot
            f = sg_item['version.Version.sg_path_to_frames']
            s = self.loaded_sources[f]
            ph_idx = ph_version['ui_index']
            i_diff = index.row() - ph_idx
            f_index = ph_idx + i_diff
            tl =  rv.commands.getIntProperty('%s.edl.frame' % self.cut_seq_name)
            fno = tl[f_index]
            rv.commands.setFrame(fno)
            print "MOVE TO SOURCE %r %r" % (s, ph_version)


        self.load_data(entity)

    def on_item_changed(self, item):
        print "ON ITEM CHANGED %d" % item.row()
        if item.row() == 0:
            self.tray_list.setCurrentIndex(item)
            self.tray_list.setFocus()




