from PySide.QtCore import QFile
from PySide import QtGui, QtCore

import types
import os
import math
import rv
import rv.qtutils
import tank

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

        # playhead_moved = QtCore.Signal(dict)

        # def sourceSetup (self, event):
        #         print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& sourceSetup"
        #         print event.contents()

        #         #
        #         #  event.reject() is done to allow other functions bound to
        #         #  this event to get a chance to modify the state as well. If
        #         #  its not rejected, the event will be eaten and no other call
        #         #  backs will occur.
        #         #

        #         event.reject()
 
        #         args         = event.contents().split(";;")
        #         group        = args[0]
        #         fileSource   = groupMemberOfType(group, "RVFileSource")
        #         imageSource  = groupMemberOfType(group, "RVImageSource")
        #         source       = fileSource if imageSource == None else imageSource
        #         typeName     = rv.commands.nodeType(source)
        #         fileNames    = rv.commands.getStringProperty("%s.media.movie" % source, 0, 1000)
        #         fileName     = fileNames[0]
        #         ext          = fileName.split('.')[-1].upper()
        #         mInfo        = rv.commands.sourceMediaInfo(source, None)
        #         print "group: %s fileSource: %s fileName: %s" % (group, fileSource, fileName)
        #         propName = "%s.%s" % (fileSource, "tracking.info")
        
        #         self.propName = propName
        #         self.group = group
        #         try:
        #         tl = rv.commands.getStringProperty(propName)
        #         print tl
        #         #import ast
        #         #tl = ast.literal_eval(tracking_str)
        #         self._tracking_info= {}
                
        #         for i in range(0,len(tl)-1, 2):
        #                 self._tracking_info[tl[i]] = tl[i+1]
        #         print self._tracking_info

        #         # make an entity
        #         entity = {}
        #         entity["type"] = "Version"
        #         entity["id"] = int(self._tracking_info['id'])
        #         print entity
        #         self.load_data(entity)
        #         self.version_activity_stream.ui.shot_info_widget.load_data_rv(self._tracking_info)

        #         except Exception as e:
        #         print "OH NO %r" % e

    def beforeSessionRead (self, event):
        # print "################### beforeSessionRead"
        event.reject()

        self._readingSession = True

    def afterSessionRead (self, event):
        # print "################### afterSessionRead"
        event.reject()

        self._readingSession = False

    def inputsChanged(self, event):
        #pass
        print "################### inputsChanged %r" % event
        # print event.contents()
        event.reject()
        try:
            fileSource   = rv.commands.nodesOfType("#RVSource")
            self.propName =  "%s.%s" % (fileSource[0], "tracking.info")
            tl = rv.commands.getStringProperty(self.propName)

            self._tracking_info= {}
            
            for i in range(0,len(tl)-1, 2):
                self._tracking_info[tl[i]] = tl[i+1]

            # make an entity
            entity = {}
            entity["type"] = "Version"
            entity["id"] = int(self._tracking_info['id'])
            if event.contents() == "viewGroup":
                self.load_data(entity)
            #self.version_activity_stream.ui.shot_info_widget.load_data_rv(self._tracking_info)

        except Exception as e:
                pass
                # print "OH NO %r" % e

    def viewChange(self, event):
        #pass
        #print "################### viewChange %r" % event
        #print event.contents()
        event.reject()

    def frameChanged(self, event):
        event.reject()
        try:
            tl = rv.commands.getIntProperty('%s.edl.frame' % self.cut_seq_name)
            n = 0
            for x in tl:
                if rv.commands.frame() < x:
                    # print "SELECT %d PLEASE %d" % (x,n-1)
                    # self.tray_model.setSelection()
                    # self.playhead_moved.emit()
                    break 
                n = n + 1              
                        

            # this then is all TRAY code.
            # we extract the version id FROM the tray here and thusly FROM Toolkit FROM the DB.
            #####################################################################################
            sel_index = self.tray_model.index(n-1, 0)
            
            self.tray_list.selectionModel().select(sel_index, self.tray_list.selectionModel().ClearAndSelect)
            #self.tray_list.selectionModel().selectionChanged.emit(sel_index, sel_index)
            #self.tray_list.setCurrentIndex(self.tray_model.createIndex(n-1, 0))

            #sel_range = QtGui.QItemSelection( sel_index, sel_index)
            #self.tray_list.selectionModel().select(sel_range, self.tray_list.selectionModel().ClearAndSelect)
            

            ids = self.tray_model.entity_ids
            our_type =  self.tray_model.get_entity_type()
            item = self.tray_model.index_from_entity(our_type, ids[n-1])
            sg_item = shotgun_model.get_sg_data(item)
       
            # does updating the other dock make this one refresh now?
            if sg_item['sg_version.Version.id'] != self.version_id:
                 # make an entity
                entity = {}
                entity["type"] = "Version"
                entity["id"] = sg_item['sg_version.Version.id']
                self.load_data(entity)
                self.version_id = sg_item['sg_version.Version.id']
                self.tray_list.scrollTo(item, QtGui.QAbstractItemView.EnsureVisible)
           
            #return
            # this made it work. ug.
            #rv.qtutils.sessionWindow().setFocus()
            #self.tray_list.setFocus()

            
        except Exception as e:
            print "ERROR: RV frameChanged EXCEPTION %r" % e

    def sourcePath(self, event):
        
        # print "################### sourcePath %r" % event
        # print event.contents()
        event.reject()

    # why does cut_tracking from in contents?
    def graphStateChange(self, event):
        # print "################### graphStateChange %r" % event
        # print event.contents()
        event.reject()
        if "cut_tracking.info" in event.contents():
                try:
                    tl = rv.commands.getStringProperty(event.contents())
                    if "infoStatus" not in event.contents():
                        self._tracking_info= {}
                        
                        for i in range(0,len(tl)-1, 2):
                            self._tracking_info[tl[i]] = tl[i+1]
                        
                        # make an entity
                        entity = {}
                        entity["type"] = "Version"
                        entity["id"] = int(self._tracking_info['id'])
                        
                        self.load_data(entity)
                        # self.version_activity_stream.ui.shot_info_widget.load_data_rv(self._tracking_info)

                        s = self._tracking_info['shot']
                        (s_id, s_name, s_type) = s.split('|')
                        (n, shot_id) = s_id.split('_')
        
                        # display VERSION info not parent shot info
                        # shot_filters = [ ['id','is', entity['id']] ]
                        # self.shot_info_model.load_data(entity_type="Version", filters=shot_filters)

                        # version_filters = [ ['project','is', {'type':'Project','id':71}],
                        #     ['entity','is',{'type':'Shot','id': int(shot_id) }] ]
                        version_filters = [ ['entity','is',{'type':'Shot','id': int(shot_id) }] ]
                        
                        self.version_model.load_data(entity_type="Version", filters=version_filters)

                        
                except Exception as e:
                    pass
                #print "TRACKING ERROR: %r" % e

    # this ASSUMES cut_tracking ALREADY EXISTS
    def sourceGroupComplete(self, event):
        #print "################### sourceGroupComplete %r" % event
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

        # ok, lazy boy just added a 'cut_' to the SR convention...
        propName = "%s.%s" % (fileSource, "cut_tracking.info")
        
        self.propName = propName
        self.group = group
        try:
            tl = rv.commands.getStringProperty(propName)
            self._tracking_info= {}
            
            for i in range(0,len(tl)-1, 2):
                self._tracking_info[tl[i]] = tl[i+1]
            
            # make an entity
            entity = {}
            entity["type"] = "Version"
            entity["id"] = int(self._tracking_info['id'])
            
            s = self._tracking_info['shot']
            (s_id, s_name, s_type) = s.split('|')
            (n, shot_id) = s_id.split('_')

            self.load_data(entity)
            
            # shot_filters = [ ['id','is', int(shot_id)] ]
            # self.shot_info_model.load_data(entity_type="Shot", filters=shot_filters)

            #self.version_activity_stream.ui.shot_info_widget.load_data_rv(self._tracking_info)
            #version_filters = [ ['project','is', {'type':'Project','id':71}],
            #    ['entity','is',{'type':'Shot','id': int(shot_id)}] ]
            #self.version_model.load_data(entity_type="Version", filters=version_filters)

        except Exception as e:
                # print "No tracking info found on source-group-complete"
                pass
                # print "OH NO %r" % e

    def __init__(self, app):
        rv.rvtypes.MinorMode.__init__(self)
        
        self.note_dock = None
        self.tray_dock = None
        self.tab_widget = None
        self.mini_cut = False
        self.detail_version_id = None

        self._app = app

        self.version_id = -1 

        self._tracking_info= {}

        self.init("RvActivityMode", None,
                [ 
                ("after-session-read", self.afterSessionRead, ""),
                ("before-session-read", self.beforeSessionRead, ""),
                # ("source-group-complete", self.sourceSetup, ""),
                # ("after-graph-view-change", self.viewChange, ""),
                ("frame-changed", self.frameChanged, ""),
                # ("graph-node-inputs-changed", self.inputsChanged, ""),
                # ("incoming-source-path", self.sourcePath, ""),
                ("source-group-complete", self.sourceGroupComplete, ""),
                ("graph-state-change", self.graphStateChange, ""),
                #("view-node-changed", self.viewChange, "")
                ],
                None,
                None);

        rv.extra_commands.toggleFullScreen()
        
    def activate(self):
        rv.rvtypes.MinorMode.activate(self)

    def deactivate(self):
        rv.rvtypes.MinorMode.deactivate(self)


######## qt stuff down here. 


    def load_data(self, entity):
        self.version_id = entity['id']
        self.details_panel.load_data(entity)
 
        # we start with the two docks, and load them with goodies
        # note_dock holds the new DetailsPaneWidget
        # tray_dock holds a QFrame .... lets break that guy out.
    def init_ui(self, note_dock, tray_dock, version_id):
        self.note_dock = note_dock
        self.tray_dock = tray_dock

        self.tray_dock.setMinimumSize(QtCore.QSize(1355,140))


        # Setup the details panel.
        self.details_panel = DetailsPanelWidget()
        self.note_dock.setWidget(self.details_panel)
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

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

        # self.tray_model.itemChanged.connect(self.on_item_changed)
        

        tray_filters = [ ['sg_cut','is', {'type':'CustomEntity10', 'id': 8}] ]
        tray_fields= ["sg_cut_in", "sg_cut_out", "sg_cut_order", 
                "sg_version.Version.sg_path_to_frames", "sg_version.Version.id",
                "sg_version.Version.sg_first_frame", "sg_version.Version.sg_last_frame"]

        orders = [{'field_name':'sg_cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CustomEntity11", filters=tray_filters, fields=tray_fields, order=orders)


    def on_browse_cut(self):
        print "ON BROWSE CUT"
        tray_filters = [ ['sg_cut','is', {'type':'CustomEntity10', 'id': 23}] ]
        tray_fields= ["sg_cut_in", "sg_cut_out", "sg_cut_order", 
                "sg_version.Version.sg_path_to_frames", "sg_version.Version.id",
                "sg_version.Version.sg_first_frame", "sg_version.Version.sg_last_frame"]

        orders = [{'field_name':'sg_cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CustomEntity11", filters=tray_filters, fields=tray_fields, order=orders)

        self.on_entire_cut()

 
    def on_entire_cut(self):
        print "ON ENTIRE CUT"
        self.mini_cut = False
        self.tray_list.mini_cut = False
        e_ids = self.tray_model.entity_ids
        e_type = self.tray_model.get_entity_type()
        
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        # rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        # rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        sources = rv.commands.nodesOfType("RVSourceGroup")
        rv.commands.setNodeInputs(self.cut_seq, sources)
        rv.commands.setViewNode(self.cut_seq)

        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
        

    def on_mini_cut(self):
        print "ON MINI CUT"
        print "current selection: %r" % self.tray_list.currentIndex()
        self.mini_cut = True
        self.tray_list.mini_cut = True
        #setattr(self.tray_list.mini_cut, 'mini_on', True)
        # get current selection
        cur_index = self.tray_list.currentIndex()
        # get cut info from somewhere... model? sg_data
        # get prev and next from current... selRange
        # get shots on either side
        # tear down graph, build new one
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')

    def on_cache_loaded(self):
        print "CACHE LOADED"

    def on_data_refreshed(self, was_refreshed):
        print "DATA_REFRESHED: %r" % was_refreshed

        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        ids = self.tray_model.entity_ids
        our_type =  self.tray_model.get_entity_type()

        self.rv_source_nums = []
        self.rv_frames = []
        self.rv_ins = []
        self.rv_outs = []
        n = 0
        t = 1
        
        for i in ids:
            item = self.tray_model.index_from_entity(our_type, i)
            sg_item = shotgun_model.get_sg_data(item)
            # print "ODR: %r" % sg_item
            f = sg_item['sg_version.Version.sg_path_to_frames']
            rv.commands.addSource(f)
            self.rv_source_nums.append(n)
            n = n + 1
            self.rv_ins.append( sg_item['sg_cut_in'] )
            self.rv_outs.append( sg_item['sg_cut_out'] )
            self.rv_frames.append(t)
            t = sg_item['sg_cut_out'] - sg_item['sg_cut_in'] + 1 + t
        
        self.rv_source_nums.append(0)
        self.rv_ins.append(0)
        self.rv_outs.append(0)
        self.rv_frames.append(t)

        self.cut_seq = rv.commands.newNode("RVSequenceGroup")
        
        # need to get the name into the query...
        rv.extra_commands.setUIName(self.cut_seq, "CUTZ cut")
        self.cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq, 'RVSequence')[0]

        k = "%s.mode.autoEDL" % str(self.cut_seq_name)
        print "ADDING %s" % k
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.IntType, 1)
        
        
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        sources = rv.commands.nodesOfType("RVSourceGroup")
        rv.commands.setNodeInputs(self.cut_seq, sources)
        rv.commands.setViewNode(self.cut_seq)
        
        self.tray_list.setCurrentIndex(self.tray_model.createIndex(n-1, 0))
            
        # this works but maybe i dont need it after all...
    def on_item_changed(curr, prev):
        pass
        # print "item changed"
        # print curr, prev

    def load_timeline(self, index, start_row, end_row, add_source=False):
        print "load_timeline:"
        ids = self.tray_model.entity_ids
        our_type =  self.tray_model.get_entity_type()

        source_nums = []
        frames = []
        ins = []
        outs = []
        n = ids[start].row()
        t = 1
        
        for i in ids[start_row:end_row]:
            item = self.tray_model.index_from_entity(our_type, i)
            sg_item = shotgun_model.get_sg_data(item)
            f = sg_item['sg_version.Version.sg_path_to_frames']
            if add_source:
                rv.commands.addSource(f)
            source_nums.append(n)
            n = n + 1
            ins.append( sg_item['sg_cut_in'] )
            outs.append( sg_item['sg_cut_out'] )
            frames.append(t)
            t = sg_item['sg_cut_out'] - sg_item['sg_cut_in'] + 1 + t
        
        source_nums.append(0)
        ins.append(0)
        outs.append(0)
        frames.append(t)

        self.cut_seq = rv.commands.newNode("RVSequenceGroup")
        
        # need to get the name into the query...
        rv.extra_commands.setUIName(self.cut_seq, "CUTZ cut")
        self.cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq, 'RVSequence')[0]

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
        rv.commands.setNodeInputs(self.cut_seq, sources[start_row:end_row])
        rv.commands.setViewNode(self.cut_seq)


    def tray_double_clicked(self, index):
        sg_item = shotgun_model.get_sg_data(index)
        single_source = []
        single_frames = []
        single_ins = []
        single_outs = []
        t = 1
        single_source.append(index.row())
        single_ins.append(sg_item['sg_cut_in'])
        single_outs.append(sg_item['sg_cut_out'])
        single_frames.append(t)
        t = sg_item['sg_cut_out'] - sg_item['sg_cut_in'] + 1 + t
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

        # self.tray_list.selectionModel().selectionChanged.emit(index, None)
        # self.ui.thumbnail.style().unpolish(self.ui.thumbnail)
        # self.ui.thumbnail.style().polish(self.ui.thumbnail)
        # self.ui.thumbnail.update()
        # self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        #self.tray_list.model().invalidate()
        #self.tray_list.repaint()

    def tray_activated(self, index):
        print "Tray Activated! %r" % index


    def tray_clicked(self, index):
        print "MODE_TRAY_CLICKED %r" % index.row()

        if self.mini_cut:
            e_ids = self.tray_model.entity_ids
            e_type = self.tray_model.get_entity_type()

            mini_sources = []
            mini_frames = []
            mini_ins = []
            mini_outs = []
            t = 1
            rs = max(0,index.row()-2)
            re = min(index.row()+3, len(self.rv_source_nums)+1)
            for x in range(rs, re):
                m_item = self.tray_model.item_from_entity(e_type, e_ids[x])
                sg = shotgun_model.get_sg_data(m_item)
                print "%d %r" % (x, sg['sg_version.Version.sg_path_to_frames'])
                mini_sources.append(x)
                mini_ins.append( sg['sg_cut_in'] )
                mini_outs.append( sg['sg_cut_out'] )
                mini_frames.append(t)
                t = sg['sg_cut_out'] - sg['sg_cut_in'] + 1 + t
            mini_sources.append(0)
            mini_ins.append(0)
            mini_outs.append(0)
            mini_frames.append(t)
            
            #rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, mini_sources, True)
            rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, mini_frames, True)
            rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, mini_ins, True)
            rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, mini_outs, True)
            
            rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
            rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

            sources = rv.commands.nodesOfType("RVSourceGroup")
            # print "SOURCES: %r" % sources
            rv.commands.setNodeInputs(self.cut_seq, sources[index.row()-2:index.row()+3])
            rv.commands.setViewNode(self.cut_seq)

        sg_item = shotgun_model.get_sg_data(index)  

        entity = {}
        entity["type"] = "Version"
        entity["id"] = sg_item['sg_version.Version.id']

        # s = self._tracking_info['shot']
        # (s_id, s_name, s_type) = s.split('|')
        # (n, shot_id) = s_id.split('_')

        self.load_data(entity)
        # self.tray_list.update()

        #self.tray_list.selectionModel().selectionChanged.emit(index, None)
        rv.qtutils.sessionWindow().setFocus()
        #self.tray_list.selectionModel().clear()

        # self.tray_list.model().invalidate()

        # version_filters = [ ['project','is', {'type':'Project','id':71}],
        #     ['entity','is',{'type':'Shot','id': int(shot_id)}] ]
        # self.version_model.load_data(entity_type="Version", filters=version_filters)

    def on_item_changed(self, item):
        print "ON ITEM CHANGED %d" % item.row()
        if item.row() == 0:
            self.tray_list.setCurrentIndex(item)
            self.tray_list.setFocus()




