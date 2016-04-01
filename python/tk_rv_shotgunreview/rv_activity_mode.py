from PySide.QtCore import QTimer, SIGNAL
from PySide import QtGui, QtCore

import copy
import types
import os
import math
import rv
import rv.qtutils
# import sgtk
import tank

import json

shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")


from .tray_delegate import RvTrayDelegate
from .details_panel_widget import DetailsPanelWidget

import sgtk

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
 
    def load_version_id_from_session(self, source_name=None):
        if not source_name:
            saf = rv.commands.sourcesAtFrame(rv.commands.frame())
            if saf:
                source_name = str(saf[0])

        if source_name:
            source_prop_name = ("%s.cut_support.json_sg_data") % source_name
            if rv.commands.propertyExists(source_prop_name):
                j_data = rv.commands.getStringProperty(source_prop_name)
                if j_data:
                    try:
                        sg_data = json.loads(str(j_data[0]))
                        entity = {}
                        entity['type'] = 'Version'
                        if 'version.Version.id' in sg_data:
                            entity['id'] = sg_data['version.Version.id']
                        else:
                            entity['id'] = sg_data['id']
                        if self.version_id != entity['id']:
                            self.load_data(entity)
                            self.details_dirty = False
                        return sg_data
                    except Exception as e:
                        print "ERROR: load_version_id_from_session JSON EXCEPTION %r" % e
                        #self.details_dirty = True
                        print "JDATA: %r" % j_data
                        print "source_name: %r" % source_name
                        print "entity: %r" % entity
            else:
                print "ERROR: NO PROP NAMED %s" % source_name
        return None

    # RV Evenets

    def replaceWithSelected(self, event):
        s = copy.copy(event.contents())
        print "replaceWithSelected"
        try:
            v = json.loads(s)
            self.load_sequence_with_versions(v)
        except Exception as e:
            print "ERROR: replaceWithSelected %r" % e
        finally:
            event.reject()

    def swapIntoSequence(self, event):
        s = copy.copy(event.contents())
        try:
            v = json.loads(s)
        except Exception as e:
            print "ERROR: swapIntoSequence JSON %r" % e
        try:
            self.replace_version_in_sequence(v)
        except Exception as e:
            print "ERROR: swapIntoSequence %r" % e
        finally:
            event.reject()

    def compareWithCurrent(self, event):
        print "COMPARE"
        print "%r" % event.contents()
        vlist = []
        try:
            # examine whats under the playhead, thats a source you want.
            ph_version = self.load_version_id_from_session()
            vlist.append(ph_version)
            # now whatever we got from the event
            vd = json.loads(event.contents())
            for v in vd:
                # print "Version id: %d" % v['id']
                v['pinned'] = 1
                vlist.append(v)
            self.load_sequence_with_versions(vlist)
            
        except Exception as e:
            print "ERROR: compareWithCurrent %r" % e
            print "%r" % event.contents()

        finally:
            event.reject()

        """
        u'sg_last_frame' 82
        u'code' u'BBB_08_a-team_006_ANIM_001'
        u'image' u'https://sg-media-usor-01.s3.amazonaws.com/25f4a7a8f476fdba7f4412605a46bd46d4318af7/d5b0911e76c31ada4dbb666581dcfb52c5cfbc95/BBB_08_a-team_006_ANIM_001_thumb_t.jpg?AWSAccessKeyId=AKIAJEA7VWGTG3UYWNWA&Expires=1457522191&Signature=Wah2K%2Fa9twvNTe4URix3uonfTYg%3D'
        u'sg_first_frame' 40
        u'entity' {u'type': u'Shot', u'id': 1228, u'name': u'08_a-team_006'}
        u'sg_path_to_frames' u'/rvshotgundemo/BBB_Short/08_a-team/006/ANIM/001/BBB_08_a-team_006_ANIM_001.40-82#.jpg'
        u'sg_status_list' u'rev'
        u'user' {u'type': u'HumanUser', u'id': 73, u'name': u'Johnny Duguid'}
        u'type' u'Version'
        u'id' 6044
        """

    def beforeSessionRead (self, event):
        # print "################### beforeSessionRead"
        event.reject()
        self._readingSession = True

    def afterSessionRead (self, event):
        # print "################### afterSessionRead"
        event.reject()
        self._readingSession = False

    def inputsChanged(self, event):
        # print "################### inputsChanged %r" % event
        # print event.contents()
        event.reject()
        self.details_dirty = True

    def viewChange(self, event):
        # print "################### viewChange %r" % event
        # print "contents %r" % event.contents()
        event.reject()
        self.load_version_id_from_session()

    def frameChanged(self, event):
        event.reject()
        try:
            sg_data = self.load_version_id_from_session()
            if sg_data:
                if 'ui_index' in sg_data:
                    idx = sg_data['ui_index']
                    sel_index = self.tray_model.index(idx, 0)
                    sels = self.tray_list.selectionModel().selectedIndexes()
                    if sel_index not in sels:
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
        # print "################### graphStateChange %r" % event
        # print event.contents()
        event.reject()
        self.details_dirty = True

    # this ASSUMES cut_tracking ALREADY EXISTS
    def sourceGroupComplete(self, event):
        # this event shows up with some built in goodness in contents.
        # below are some nice things i stole from Jon about how to 
        # dig info out of whats there
        event.reject()

        # sg_data = self.load_version_id_from_session()

        args         = event.contents().split(";;")
        # this source group was just created.
        if args[1] == "new":
            return
        else:
            print "################### sourceGroupComplete %r" % event
            print args[1]
            print event.contents()

    def on_view_size_changed(self, event):
        event.reject()
        traysize = self.tray_dock.size().width()
        self.tray_main_frame.resize(traysize - 10, self._tray_height)

    def __init__(self, app):
        rv.rvtypes.MinorMode.__init__(self)
        self._bundle = sgtk.platform.current_bundle()
        
        self.note_dock = None
        self.tray_dock = None
        self.tab_widget = None
        self.mini_cut = False
        self.detail_version_id = None

        self._tray_height = 180

        self.last_mini_center = None
        self._mini_before_shots = 2
        self._mini_after_shots = 2
        self._mini_cut_seq_name = None
        self.mini_cut_seq_node = None

        self.details_dirty = False

        self.pinned_items = []

        # RV specific
        # the current sequence node
        self.cut_seq_node = None
        self.loaded_sources = {}
        self._layout_node = None
        self.mod_seq_node = None
        self.want_stacked = False
        self.version_swap_out = None
        self.no_cut_context = False

        self.version_id = -1
        self.entity_from_gma = None


        # models for ad-hoc queries
        self._shot_model = shotgun_model.SimpleShotgunModel(rv.qtutils.sessionWindow())
        self._cuts_model = shotgun_model.SimpleShotgunModel(rv.qtutils.sessionWindow())

        self._app = app

        self.init("RvActivityMode", None,
                [ 
                ("after-session-read", self.afterSessionRead, ""),
                ("before-session-read", self.beforeSessionRead, ""),
                # ("source-group-complete", self.sourceSetup, ""),
                ("after-graph-view-change", self.viewChange, ""),
                ("frame-changed", self.frameChanged, ""),
                ("graph-node-inputs-changed", self.inputsChanged, ""),
                ("compare_with_current", self.compareWithCurrent, ""),
                ("swap_into_sequence", self.swapIntoSequence, ""),
                ("source-group-complete", self.sourceGroupComplete, ""),
                ("replace_with_selected", self.replaceWithSelected, ""),
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
              

    ################################################################################### qt stuff down here. 

    def load_data(self, entity):
        self.version_id = entity['id']
        try:
            self.details_panel.load_data(entity)
        except Exception as e:
            print "DETAILS PANEL: sent %r got %r" % (entity, e)
        # saw False even if we fail? endless loop? delay?
        self.details_dirty = False
 
    def init_ui(self, note_dock, tray_dock, version_id):
        self.note_dock = note_dock
        self.tray_dock = tray_dock
        
        # Setup the details panel.
        self.details_panel = DetailsPanelWidget()
        self.note_dock.setWidget(self.details_panel)
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

        self.tray_dock.setMinimumSize(QtCore.QSize(720,self._tray_height))
        
        # ug, for now till i can clean up the methods
        from .tray_main_frame import TrayMainFrame
        self.tray_main_frame = TrayMainFrame(self.tray_dock)
        self.tray_main_frame.set_rv_mode(self)
        
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

        # self.load_tray_with_cut_id(6)

        self.details_timer = QTimer(rv.qtutils.sessionWindow())
        self.note_dock.connect(self.details_timer, SIGNAL("timeout()"), self.check_details)
        self.details_timer.start(1000)


    def on_browse_cut(self):
        # forcing a test....
        entity = {}
        entity['id'] = 6
        entity['type'] = 'Cut'

        # version
        # entity['id'] = 7406
        # entity['type'] = 'Version'

        # entity['id'] = 62
        # entity['type'] = "Playlist"
        rv.commands.sendInternalEvent('id_from_gma', json.dumps(entity))        

    def get_version_from_id(self, id):
        v_fields = [
            "sg_path_to_frames", "id",
            "sg_first_frame", "sg_last_frame",
            "sg_path_to_movie", "sg_movie_aspect_ratio",
            "sg_movie_as_slate", "sg_frames_aspect_ratio",
            "sg_frames_has_slate", "image", "code"
            "sg_uploaded_movie_frame_rate", "sg_uploaded_movie_mp4", 
        ]
        # get the version info we need
        version  = self._bundle.shotgun.find_one("Version", [["id", "is", id]], v_fields)

        return self.convert_sg_dict(version)


    def on_id_from_gma(self, event):
        print "on_id_from_gma %r" % event.contents()
        self.pinned_items = []
        self.version_swap_out = None
        self.no_cut_context = False
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')

        try:
            
            d = json.loads(event.contents())
            # we save the request so that we know what exactly was requested when we get down to loading the tray asynchronously
            self.entity_from_gma = d

            if d['type'] == "Cut":
                # self.tray_dock.setVisible(True)
                self.load_tray_with_cut_id(d['id'])
            if d['type'] == "Version":
                
                # disabling this feature for now....
                
                # shot = self._bundle.shotgun.find_one("Version", [["id", "is", d["id"]]], ["entity"] ).get('entity')
                # orders = [{'field_name':'cut.Cut.updated_at','direction':'desc'}]
                # cuts = self._bundle.shotgun.find('CutItem', [['shot', 'is', shot]], fields=["cut", "cut.Cut.updated_at"], order=orders)
                
                cuts = None

                # now we have the latest cut
                # we need to swap in the version we want into the cut.
                v_fields = [
                    "sg_path_to_frames", "id",
                    "sg_first_frame", "sg_last_frame",
                    "sg_path_to_movie", "sg_movie_aspect_ratio",
                    "sg_movie_as_slate", "sg_frames_aspect_ratio",
                    "sg_frames_has_slate", "image", "code",
                    "sg_uploaded_movie_frame_rate", "sg_uploaded_movie_mp4", 
                ]
                # get the version info we need
                version  = self._bundle.shotgun.find_one("Version", [["id", "is", d['id']]], v_fields)

                if cuts:
                    version['cutitem_id'] = cuts[0]['id']
                    self.version_swap_out = version
                    self.load_tray_with_cut_id(cuts[0]['cut']['id'])

                else:
                    # we bail to the single version
                    sg_dict = self.convert_sg_dict(version)
                    sa = [sg_dict]
                    self.load_sequence_with_versions(sa)
                    self.no_cut_context = True
                    # self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
                    # self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
                    # self.tray_model.clear()
                    # self.tray_dock.setVisible(False)


            if d['type'] == "Playlist":
                # self.tray_dock.setVisible(True)
                # playlist = self._bundle.shotgun.find_one("Playlist", [['id', 'is', d['id']]], fields=['versions'])
                # print "PLAYLIST: %r" % playlist
                # for v in playlist['versions']:
                #     p = self._bundle.shotgun.find_one("Version", [['id', 'is', v['id']]], fields=['sg_path_to_frames'])
                #     print p
                #plist = self._bundle.shotgun.find("Version", [["playlists", "is", {"type": "Playlist", "id": d["id"]}]], fields=['sg_path_to_frames'])
                #print "PLIST: %r" % plist
                self.load_tray_with_playlist_id(d['id'])

        except Exception as e:
            print "ERROR: on_id_from_gma %r" % e

    def replace_version_in_sequence(self, versions):
        #print "VERSIONS: %r" % versions
        #version = versions[0]
        fno = rv.commands.frame()    
        for version in versions:
            version = self.convert_sg_dict(version)
            # print "replace_version_in_sequence %r %d" % (version, fno)

            # ok, selected cutitem in tray is destination for this version
            ph_version = self.load_version_id_from_session()
            if 'ui_index' not in ph_version:
                self._app.engine.log_error('ui_index missing from %r' % ph_version)

            f = version['version.Version.sg_path_to_frames']

            try:
                if not f:
                    f =  'black,start=%d,end=%d.movieproc' % (version['version.Version.sg_first_frame'],
                                                              version['version.Version.sg_last_frame'])            
                if f in self.loaded_sources:
                    source_name = self.loaded_sources[f]
                else:
                    source_name = rv.commands.addSourceVerbose([f])
                    self.loaded_sources[f] = source_name
                source_prop_name = ("%s.cut_support.json_sg_data") % source_name

                group_name = rv.commands.nodeGroup(source_name)

                if version['version.Version.code']:
                    rv.extra_commands.setUIName(source_name, version['version.Version.code'])
                    if group_name:
                        rv.extra_commands.setUIName(group_name, version['version.Version.code'])
                

                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)

                # add markers from ph_version
                # if 'ui_index' in ph_version:
                version['ui_index'] = ph_version['ui_index']
                version['tl_index'] = ph_version['tl_index']
                # as we are swapping in, this version will be pinned
                version['pinned'] = 1
                self.pinned_items.append(version['ui_index'])


                source_index = ph_version['ui_index']
                if not self.swapped_sources:
                    self.swapped_sources = list(self.tray_sources)
                
                (source, _) = source_name.split('_')
                self.swapped_sources[source_index] = source

                # as this is a version we may need to translate the dict into a different form...?
                json_sg_item = json.dumps(version)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
                        
            except Exception as e:
                print "replace version in session: %r" % e

        if not self.cut_seq_node:
            self.cut_seq_node = rv.commands.newNode("RVSequenceGroup")
        
        cut_name = self.tray_main_frame.tray_button_browse_cut.text()
        if cut_name:
            rv.extra_commands.setUIName(self.cut_seq_node, cut_name)
        #self.tray_main_frame.tray_button_browse_cut.setText('MOD.' + cut_name)
        
        self.mod_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq_node, 'RVSequence')[0]

        rv.commands.setIntProperty('%s.edl.source' % self.mod_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.mod_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.mod_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.mod_seq_name, self.rv_outs, True)
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.mod_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.mod_seq_name, [0])

        rv.commands.setNodeInputs(self.cut_seq_node, self.swapped_sources)
        rv.commands.setViewNode(self.cut_seq_node)
        rv.commands.setFrame(fno)

        seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
        rv.commands.setIntProperty(seq_pinned_name, self.pinned_items, True)

        self.load_data(versions[0])
        self.tray_list.repaint()


    def load_sequence_with_versions(self, vlist):
        print "load_sequence_with_versions: %r" % vlist
        
        v_sources = []
        v_frames = []
        v_ins = []
        v_outs = []
        v_source_names = []
        
        t = 1
        w = 0
        shot_start = 0

        # ph_dict = self.load_version_id_from_session()
        # if ph_dict:            
        #     if 'ui_index' in ph_dict:
        #         self.pinned_items.append(ph_dict['ui_index'])

        for sgd in vlist:
            sg = self.convert_sg_dict(sgd)
            sg['pinned'] = 1
            f = sg['version.Version.sg_path_to_frames']

            if not f:
                f =  'black,start=%d,end=%d.movieproc' % (sg['sg_first_frame'], sg['sg_last_frame'])

            try:
                if f:    
                    if f in self.loaded_sources:
                        source_name = self.loaded_sources[f]
                    else:
                        source_name = rv.commands.addSourceVerbose([f])
                        self.loaded_sources[f] = source_name
                    group_name = rv.commands.nodeGroup(source_name)
                    rv.extra_commands.setUIName(source_name, sg['version.Version.code'])
                    rv.extra_commands.setUIName(group_name, sg['version.Version.code'])
                
                else:
                    print "ERROR: f is %r" % f
                    continue
            except Exception as e:
                print "%r" % e

            source_prop_name = ("%s.cut_support.json_sg_data") % source_name
            try:
                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)
                json_sg_item = json.dumps(sg)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                print "ERROR: load_sequence_with_versions %r" % e
                print "%r" % sg

            (num_plus, _) = source_name.split('_')
            v_source_names.append(num_plus)
 
            v_sources.append(w)
            self.pinned_items.append(w)
            w = w + 1
            
            v_frames.append(t)

            if 'version.Version.sg_first_frame' in sg:
                v_ins.append( sg['version.Version.sg_first_frame'] )
                v_outs.append( sg['version.Version.sg_last_frame'] )            
                t = sg['version.Version.sg_last_frame'] - sg['version.Version.sg_first_frame'] + 1 + t
            else:
                v_ins.append( sg['sg_first_frame'] )
                v_outs.append( sg['sg_last_frame'] )            
                t = sg['sg_last_frame'] - sg['sg_first_frame'] + 1 + t
        
        v_sources.append(0)
        v_ins.append(0)
        v_outs.append(0)
        v_frames.append(t)

        if self.want_stacked:
            if not self._stack_node:
                self._stack_node = rv.commands.newNode('RVStackGroup')
            self._v_cut_seq_name = sg['version.Version.code']
            rv.extra_commands.setUIName(self._stack_node, self._v_cut_seq_name)     
            rv.commands.setNodeInputs(self._stack_node, v_source_names)
            rv.commands.setViewNode(self._stack_node)

        else:        
            if not self._layout_node:
                self._layout_node = rv.commands.newNode("RVLayoutGroup")
            self._v_cut_seq_name = sg['version.Version.code']
            rv.extra_commands.setUIName(self._layout_node, self._v_cut_seq_name)
            rv.commands.setStringProperty("%s.layout.mode" % self._layout_node, ["grid"]);     
        
            rv.commands.setNodeInputs(self._layout_node, v_source_names)
            rv.commands.setViewNode(self._layout_node)

        # if ph_dict:
        #     if 'ui_index' in ph_dict:
        #         seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
        #         rv.commands.setIntProperty(seq_pinned_name, self.pinned_items, True)

        #         self.load_data(vlist[0])
        #         self.tray_list.repaint()
        # else:
        self.tray_dock.toggleViewAction()
        self.tray_model.clear()

        # rv.commands.setFrame(shot_start + shot_offset)

    def load_tray_with_playlist_id(self, playlist_id=None):
        #plist = self._bundle.shotgun.find("Version", [["playlists", "is", {"type": "Playlist", "id": d["id"]}]], fields=['sg_path_to_frames'])
        plist_filters = [["playlists", "is", {"type": "Playlist", "id": playlist_id}]]
        plist_fields =  ['sg_path_to_frames', 'sg_first_frame', 'sg_last_frame', 
                        'sg_path_to_movie', 'sg_movie_aspect_ratio', 'sg_movie_as_slate',
                        'sg_frames_aspect_ratio', 'sg_frames_has_slate',
                        'sg_uploaded_movie_frame_rate', 'sg_uploaded_movie_mp4', 'code', 'client_code'
                        'playlists']
        self.tray_model.load_data(entity_type="Version", filters=plist_filters, fields=plist_fields)


    def load_tray_with_cut_id(self, cut_id=None):
        if cut_id:
            self.tray_cut_id = cut_id
        
        tray_filters = [ ['cut','is', {'type':'Cut', 'id': self.tray_cut_id }] ]

        tray_fields= ["cut_item_in", "cut_item_out", "cut_order",
                "edit_in", "edit_out", "code",
                "version.Version.sg_path_to_frames", "version.Version.id",
                "version.Version.sg_first_frame", "version.Version.sg_last_frame",
                "version.Version.sg_path_to_movie", "version.Version.sg_movie_aspect_ratio",
                "version.Version.sg_movie_as_slate", "version.Version.sg_frames_aspect_ratio",
                "version.Version.sg_frames_has_slate", "version.Version.image",
                "version.Version.code",
                "version.Version.sg_uploaded_movie_frame_rate", "version.Version.sg_uploaded_movie_mp4", 
                "cut.Cut.code", "cut.Cut.id", "cut.Cut.version", "cut.Cut.fps", "cut.Cut.Version", "cut.Cut.revision_numnber"]

        orders = [{'field_name':'cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CutItem", filters=tray_filters, fields=tray_fields, order=orders)
        
        if self.mini_cut:
            self.on_entire_cut()


    def on_entire_cut(self):
        if self.no_cut_context:
            return
        #print "ON ENTIRE CUT"


        # store whatever frame we are on now
        # fno = rv.commands.frame()
        # this is a MetaInfo, frame is sourceFrame:
        #  {u'node': u'sourceGroup000013_source', u'frame': 66, u'nodeType': u'RVFileSource'}
        # smi = rv.extra_commands.sourceMetaInfoAtFrame(fno)
        #
        # so a cut can have frames that are repeated, so getting the source frame
        # can be unhelpful
        # instead use the global tl spec and figure out how many frmes in from cut in,
        # use the mini_index in sg_data
        # sf = rv.extra_commands.sourceFrame(fno)
        # print "%d %r %d\n" % (fno, smi, sf)
        self.mini_cut = False
        self.tray_list.mini_cut = False

        #sg_data = self.load_version_id_from_session()
        #print "ENTIRE: %r" % sg_data        
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        rv.commands.setViewNode(self.cut_seq_node)

        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
 
        self.tray_list.repaint()


    def on_mini_cut(self):
        if self.no_cut_context:
            return
        # print "ON MINI CUT"
        self.mini_cut = True
        self.tray_list.mini_cut = True

        sel_index = self.tray_list.selectionModel().selectedIndexes()[0]

        global_frame = rv.commands.frame()
        sg_data = self.load_version_id_from_session()
        if 'tl_index' not in sg_data:
            print "ERROR: missing tl_index in session for %r" % sg_data
            return
        tl_index = sg_data['tl_index']
               
        self.load_mini_cut(sel_index, global_frame - tl_index)

        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')

        self.tray_list.repaint()


    def on_cache_loaded(self):
        pass
        #print "CACHE LOADED."

    def get_media_path(self, sg):
        if 'version.Version.sg_path_to_frames' not in sg:
            sg = self.convert_sg_dict(sg)
        # prefer frames
        if sg['version.Version.sg_path_to_frames']:
            return sg['version.Version.sg_path_to_frames']
        if sg['version.Version.sg_path_to_movie']:
            return sg['version.Version.sg_path_to_movie']
        start = 0
        
        if sg['sg_first_frame']:
            start = sg['sg_first_frame']
        else:
            start = sg['edit_in']
        end = 1
        if sg['sg_last_frame']:
            end = sg['sg_last_frame']
        else:
            end = sg['sg_last_frame']
        s = 'black,start=%d,end=%d.movieproc' % (start, end)
        return s
            

    def set_session_prop(self, name, item):
        try:
            if not rv.commands.propertyExists(name):
                rv.commands.newProperty(name, rv.commands.StringType, 1)
            cut_json = json.dumps(item)
            rv.commands.setStringProperty(name, [cut_json], True)
        except Exception as e:
            print "ERROR: set_session_prop %r" % e

    def convert_sg_dict(self, sg_dict):
        if 'version.Version.sg_path_to_frames' in sg_dict:
            return sg_dict

        f = [   "version.Version.sg_path_to_frames", "version.Version.id",
                "version.Version.sg_first_frame", "version.Version.sg_last_frame",
                "version.Version.sg_path_to_movie", "version.Version.sg_movie_aspect_ratio",
                "version.Version.sg_movie_as_slate", "version.Version.sg_frames_aspect_ratio",
                "version.Version.sg_frames_has_slate", "version.Version.image", "version.Version.code",
                "version.Version.sg_uploaded_movie_frame_rate", "version.Version.sg_uploaded_movie_mp4", 
            ]

        for k in f:
            s = k.replace('version.Version.', '')
            if s in sg_dict:
                sg_dict[k] = sg_dict[s]

        return sg_dict

    # the way data from shotgun gets into the tray
    def on_data_refreshed(self, was_refreshed):
        self.swapped_sources = None

        v_id = -1
        # first see if we have a selection
        cur_index = self.tray_list.currentIndex()
        if cur_index:
            sg_item = shotgun_model.get_sg_data(cur_index)
            if sg_item:
                v_id = sg_item['version.Version.id']

        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)
        rows = self.tray_proxyModel.rowCount()

        if rows < 1:
            self._app.engine.log_error('Query returned no rows.')
            return
 
        self.rv_source_nums = []
        self.rv_frames = []
        self.rv_ins = []
        self.rv_outs = []
        self.tray_sources = []

        n = 0
        t = 1

        tray_seq_name = None
        final_selection = None
        cut_items = []
        cutitem_keys = ["cut_item_in", "cut_item_out", "cut_order", "edit_in", "edit_out", "id", "code"]

        for x in range(0, rows):
            item = self.tray_proxyModel.index(x, 0)
            sg_item = shotgun_model.get_sg_data(item)
            if not sg_item:
                print "WOW what do I do when there is no data at all for item %d" % item.row()
            sg_item = self.convert_sg_dict(sg_item)
            
            # removing keys we want on the source node
            if 'cut_item_in' in sg_item:
                cutitem_dict = dict ( [(k, sg_item[k]) for k in cutitem_keys])
                cut_items.append(cutitem_dict)

            if self.version_swap_out:
                if cutitem_dict['id'] == self.version_swap_out['cutitem_id']:
                    # update sg_item with new fields.
                    # crap if version.Version is in there we need to map to that
                    tmp_dict = self.convert_sg_dict(self.version_swap_out)
                    for k in tmp_dict:
                        sg_item[k] = tmp_dict[k]

            #if 'version.Version.sg_path_to_frames' in sg_item:
            f = sg_item['version.Version.sg_path_to_frames']
            #else:
            #    f = sg_item['sg_path_to_frames']
            
            if not f:
                vid = sg_item['version.Version.id']
                if sg_item['cut.Cut.version']:
                    vid = sg_item['cut.Cut.version']['id']
                                  
                v = self.get_version_from_id(vid)
                if v['version.Version.sg_path_to_movie']:
                    f = v['version.Version.sg_path_to_movie']

                f = 'black,start=%d,end=%d.movieproc' % (v['version.Version.sg_first_frame'], v['version.Version.sg_last_frame'])
            
            if f in self.loaded_sources:
                    source_name = self.loaded_sources[f]
            else:
                source_name = rv.commands.addSourceVerbose([f])
                group_name = rv.commands.nodeGroup(source_name)
                if sg_item['version.Version.code']:
                    rv.extra_commands.setUIName(source_name, sg_item['version.Version.code'])
                    rv.extra_commands.setUIName(group_name, sg_item['version.Version.code'])
                
                self.loaded_sources[f] = source_name
           
            source_prop_name = ("%s.cut_support.json_sg_data") % source_name
            try:
                sg_item['ui_index'] = n
                sg_item['tl_index'] = t
                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)
                json_sg_item = json.dumps(sg_item)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                print "ERROR: on_data_refreshed %r" % e

            # get the source id number...
            (num_plus, _) = source_name.split('_')
            self.tray_sources.append(num_plus)
            
            # ( _, nu) = num_plus.split('p')
            # it does not appear that the source array is anyting but sequential from zero
            # n = int(nu)

            self.rv_source_nums.append(n)
            n = n + 1

            if 'cut_item_in' not in sg_item:
                sg_item['cut_item_in'] = sg_item['sg_first_frame']
                sg_item['cut_item_out'] = sg_item['sg_last_frame']

            if not sg_item['cut_item_in']:
                sg_item['cut_item_in'] = sg_item['edit_in']
                sg_item['cut_item_out'] = sg_item['edit_out']

            self.rv_ins.append( sg_item['cut_item_in'] )
            self.rv_outs.append( sg_item['cut_item_out'] )
            self.rv_frames.append(t)
            
            t = sg_item['cut_item_out'] - sg_item['cut_item_in'] + 1 + t
            if 'version.Version.id' in sg_item:
                if sg_item['version.Version.id'] == v_id:
                    final_selection = item
        
        tray_seq_name = 'unknown'
        if not sg_item:
            self._app.engine.log_error('SG_ITEM is null.')
            return

        if 'cut.Cut.code' in sg_item:
            tray_seq_name = sg_item['cut.Cut.code']
            if sg_item['cut.Cut.revision_numnber'] > 1:
                tray_seq_name = "%s_%04d" % (sg_item['cut.Cut.code'], sg_item['cut.Cut.revision_numnber'])
        
        self.rv_source_nums.append(0)
        self.rv_ins.append(0)
        self.rv_outs.append(0)
        self.rv_frames.append(t)

        #if not self.cut_seq_node:
        self.cut_seq_node = rv.commands.newNode("RVSequenceGroup")

        # create a cut level dict from sg_item
        cut_keys = ["cut.Cut.code", "cut.Cut.id", "cut.Cut.version", "cut.Cut.fps"]
        cut_dict = None
        if 'cut.Cut.code' in sg_item:
            cut_dict = dict ( [(k, sg_item[k]) for k in cut_keys])
        
        self.cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.cut_seq_node, 'RVSequence')[0]
        seq_prop_name = ("%s.cut_support.json_cut_data") % self.cut_seq_name

        if cut_dict:
            self.set_session_prop(seq_prop_name, cut_dict)
            seq_prop_name = ("%s.cut_support.json_cutitem_data") % self.cut_seq_name
            self.set_session_prop(seq_prop_name, cut_items)
        else:
            print "PLIST: %r" % sg_item
            if 'playlists' in sg_item:
                for p in sg_item['playlists']:
                    if p['id'] == self.entity_from_gma['id']:
                        seq_prop_name = ("%s.cut_support.json_playlist_data") % self.cut_seq_name
                        self.set_session_prop(seq_prop_name, p)
                        tray_seq_name = p['name']
            else:
                tray_seq_name = sg_item['code']

        self.tray_main_frame.tray_button_browse_cut.setText(tray_seq_name)
        rv.extra_commands.setUIName(self.cut_seq_node, tray_seq_name)

        k = "%s.mode.autoEDL" % str(self.cut_seq_name)
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.IntType, 1)

        # self._app.tank.shotgun_url
        k = "%s.cut_support.shotgun_url" % str(self.cut_seq_name)
        if not rv.commands.propertyExists(k):
            rv.commands.newProperty(k, rv.commands.StringType, 1)
        rv.commands.setStringProperty(k, [self._app.tank.shotgun_url], True)

                
        rv.commands.setIntProperty('%s.edl.source' % self.cut_seq_name, self.rv_source_nums, True)
        rv.commands.setIntProperty('%s.edl.frame' % self.cut_seq_name, self.rv_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self.cut_seq_name, self.rv_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self.cut_seq_name, self.rv_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        rv.commands.setNodeInputs(self.cut_seq_node, self.tray_sources)
        rv.commands.setViewNode(self.cut_seq_node)

        if final_selection:
            self.tray_list.selectionModel().select(final_selection, self.tray_list.selectionModel().ClearAndSelect)
        else:            
            zero_index = self.tray_model.createIndex(0, 0)
            self.tray_list.selectionModel().select(zero_index, self.tray_list.selectionModel().ClearAndSelect)
        
        # rv.commands.fullScreenMode(True)

        self.tray_list.scrollTo(item, QtGui.QAbstractItemView.EnsureVisible)
        self.load_version_id_from_session()

        seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
        if not rv.commands.propertyExists(seq_pinned_name):
            rv.commands.newProperty(seq_pinned_name, rv.commands.IntType, 1)
        rv.commands.setIntProperty(seq_pinned_name, self.pinned_items, True)
        
    
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

    def load_mini_cut(self, index, shot_offset=0):
        print "load_mini_cut: %d %d" % ( index.row(), shot_offset )
        
        # whatever we are looking at right now is the center
        self.mini_focus = self.load_version_id_from_session()

        self.last_mini_center = index
        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)
        rows = self.tray_proxyModel.rowCount()

        mini_sources = []
        mini_frames = []
        mini_ins = []
        mini_outs = []
        mini_source_names = []
        
        t = 1
        w = 0
        
        rs = max( 0, index.row() - self._mini_before_shots)
        re = min( index.row() + 1 + self._mini_after_shots, rows)
        shot_start = 0

        for x in range(rs, re):
            m_item = self.tray_proxyModel.index(x, 0)
            sg = shotgun_model.get_sg_data(m_item)

            if self.version_swap_out:
                if sg['id'] == self.version_swap_out['cutitem_id']:
                    # update sg_item with new fields.
                    # crap if version.Version is in there we need to map to that
                    tmp_dict = self.convert_sg_dict(self.version_swap_out)
                    for k in tmp_dict:
                        sg[k] = tmp_dict[k]


            if 'version.Version.sg_path_to_frames' in sg:
                source_name = self.loaded_sources[sg['version.Version.sg_path_to_frames']]
            else:
                source_name = self.loaded_sources[sg['sg_path_to_frames']]
            (num_plus, _) = source_name.split('_')
            mini_source_names.append(num_plus)
 
            mini_sources.append(w)
            w = w + 1
            
            # playlist
            if 'cut_item_in' not in sg:
                sg['cut_item_in'] = sg['sg_first_frame']
                sg['cut_item_out'] = sg['sg_last_frame']

            mini_ins.append( sg['cut_item_in'] )
            mini_outs.append( sg['cut_item_out'] )
            
            if x == index.row():
                shot_start = t
            mini_frames.append(t)
            t = sg['cut_item_out'] - sg['cut_item_in'] + 1 + t
        
        mini_sources.append(0)
        mini_ins.append(0)
        mini_outs.append(0)
        mini_frames.append(t)

        if not self.mini_cut_seq_node:
            self.mini_cut_seq_node = rv.commands.newNode("RVSequenceGroup")
        self._mini_cut_seq_name = rv.extra_commands.nodesInGroupOfType(self.mini_cut_seq_node, 'RVSequence')[0]

        rv.extra_commands.setUIName(self.mini_cut_seq_node, "MiniCut-" + self._mini_cut_seq_name)     
        
        rv.commands.setIntProperty('%s.edl.source' % self._mini_cut_seq_name, mini_sources, True)
        rv.commands.setIntProperty('%s.edl.frame' % self._mini_cut_seq_name, mini_frames, True)
        rv.commands.setIntProperty('%s.edl.in' % self._mini_cut_seq_name, mini_ins, True)
        rv.commands.setIntProperty('%s.edl.out' % self._mini_cut_seq_name, mini_outs, True)
        
        rv.commands.setIntProperty("%s.mode.autoEDL" % self._mini_cut_seq_name, [0])
        rv.commands.setIntProperty("%s.mode.useCutInfo" % self._mini_cut_seq_name, [0])

        rv.commands.setNodeInputs(self.mini_cut_seq_node, mini_source_names)
        rv.commands.setViewNode(self.mini_cut_seq_node)
        rv.commands.setFrame(shot_start + shot_offset)

    def tray_clicked(self, index):

        sg_item = shotgun_model.get_sg_data(index)
        sg_item = self.convert_sg_dict(sg_item) 
        
        # the version the playhead is parked on
        ph_version = self.load_version_id_from_session()
        if 'version.Version.id' not in ph_version:
            ph_version['version.Version.id'] = ph_version['id']
        #print "CLICK"
        #print "\nph: %r" % ph_version
        
        f = sg_item['version.Version.sg_path_to_frames']
        source_name = self.loaded_sources[f]
        sel_version = self.load_version_id_from_session(source_name)
        #print "sel: %r\n" % sel_version
        if sel_version:
            if sel_version['version.Version.id'] != ph_version['version.Version.id']:
                tl = None
                fno = 0
                if self.mini_cut:
                    tl =  rv.commands.getIntProperty('%s.edl.frame' % self._mini_cut_seq_name)
                    x = index.row() - (self.last_mini_center.row() - self._mini_before_shots)
                    fno = tl[x]
                else:    
                    tl =  rv.commands.getIntProperty('%s.edl.frame' % self.cut_seq_name)
                    fno = tl[sel_version['ui_index']]
                rv.commands.setFrame(fno)

        self.tray_list.repaint()





