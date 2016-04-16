from PySide.QtCore import QTimer, SIGNAL
from PySide import QtGui, QtCore

import copy
import types
import os
import shutil
import math
import rv
import pymu
import subprocess
import tank
import tempfile
import json
import urllib
import time


shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

from .tray_delegate import RvTrayDelegate
from .details_panel_widget import DetailsPanelWidget

import sgtk

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
 
    def load_version_id_from_session(self, group_name=None):
        
        if not group_name:
            saf = rv.commands.sourcesAtFrame(rv.commands.frame())
            if saf:
                source_name = str(saf[0])
                group_name = rv.commands.nodeGroup(source_name)
                
        if group_name:
            source_prop_name = ("%s.cut_support.json_sg_data") % group_name
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
                        print "group_name: %r" % group_name
                        print "entity: %r" % entity
            else:
                self._app.engine.log_error("load_version_id_from_session: NO PROP NAMED %s" % group_name)

        return None

    # RV Events

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

    def graphStateChange(self, event):
        event.reject()
        self.details_dirty = True

    def sourceGroupComplete(self, event):
        event.reject()

        args         = event.contents().split(";;")
        # this source group was just created.
        if args[1] == "new":
            return
        else:
            print "################### sourceGroupComplete %r" % event
            print args[1]
            print event.contents()

    def on_play_state_change(self, event):

        # Auto-pin the DetailsPanel during playback, so that updating it does
        # not cause a hiccup.
        # XXX auto-pinning should be controlled by a preference (default on)

        # Ignore the event if no DetailsPanel built yet, or if we are
        # "buffering" (ie playback paused to fill cache) or in "turn-around"
        # (ie looping)
        cont = event.contents()
        if (self.details_panel and cont != "buffering" and cont != "turn-around"):
            # We only auto-pin the details if they are not already pinned
            # XXX _pinned should be publicly accessible
            if   (event.name() == "play-start" and not self.details_panel._pinned):
                self.details_panel.set_pinned(True)
                self.details_pinned_for_playback = True
            # We only auto-unpin the details on stop if we auto-pinned them in
            # the first place.
            elif (event.name() == "play-stop" and self.details_pinned_for_playback):
                self.details_panel.set_pinned(False)
                self.details_pinned_for_playback = False

    def on_view_size_changed(self, event):
        event.reject()
        traysize = self.tray_dock.size().width()
        self.tray_main_frame.resize(traysize - 10, self._tray_height)

    def launchSubmitTool(self, event):
        if (self.tray_dock):
            self.tray_dock.hide()
            
        rv.runtime.eval("""
            {
                require shotgun_mode;
                require shotgun_review_app;
                require shotgun_upload;

                if (! shotgun_mode.localModeReady())
                {
                    //  Silence the mode first, then activate it.
                    //  shotgun_mode.silent = true;
                    shotgun_mode.createLocalMode();
                }
                if (! shotgun_review_app.localModeReady())
                {
                    //  Silence the mode first, then activate it.
                    //  shotgun_review_app.silent = true;
                    shotgun_review_app.createLocalMode();
                }
                if (! shotgun_upload.localModeReady())
                {
                    //  Silence the mode first, then activate it.
                    //  shotgun_upload.silent = true;
                    shotgun_upload.createLocalMode();
                }

                shotgun_review_app.theMode().internalLaunchSubmitTool();
            }
            """, [])

    def getUnstoredFrameProps(self):
        unstoredFrames = {}
        frames = rv.extra_commands.findAnnotatedFrames()
        pnodes = rv.commands.nodesOfType("RVPaint")
        for pnode in pnodes:
            for frame in frames:
                sframe = rv.extra_commands.sourceFrame(frame)
                orderProp = pnode + '.frame:%d.order' % sframe
                if rv.commands.propertyExists(orderProp):
                    pcmds = rv.commands.getStringProperty(orderProp)
                    for pcmd in pcmds:
                        savedProp = pnode + '.%s.sgtk_stored' % pcmd
                        if rv.commands.propertyExists(savedProp):
                            continue
                        unstoredFrames.setdefault(frame, []).append(savedProp)
        return unstoredFrames

    def getUnstoredFrames(self):
        return self.getUnstoredFrameProps().keys()

    def makeNoteAttachments(self, event):
        # not sure if anyone else wants to use this,
        # but might as well let them
        event.reject() 

        props = self.getUnstoredFrameProps()
        if len(props) <= 0:
            return

        tempdir = tempfile.mkdtemp()
        rv.commands.rvioSetup()
        rvio = os.environ.get("RV_APP_RVIO", None)
        args = [rvio, "-v", "-err-to-out"]

        setDisp = pymu.MuSymbol("export_utils.setExportDisplayConvert")
        setDisp("default")
        session = os.path.join(tempdir, "export.rv")
        rv.commands.saveSession(session)
        args += [session]

        tempfiles = os.path.join(tempdir,"sequence.@.jpg")
        args += ["-o", tempfiles]

        frames = [ str(f) for f in props.keys() ]
        framesStr = ','.join(frames)
        args += ["-t", framesStr]

        lic = os.environ.get("RV_APP_USE_LICENSE_FILE", None)
        if (lic != None):
            args += ["-lic", lic]
        print(args)
        rvioExec = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(rvioExec.stderr.read(), rvioExec.stdout.read())

        attachments = []
        current = rv.commands.sourcesAtFrame(rv.commands.frame())[0] # will be replaced with event contents
        for frame,props in props.items():
            src = "%s/sequence.%d.jpg" % (tempdir,frame)

            if not (os.path.isfile(src)):
                print("ERROR: Can't find annotation for frame: %d at '%s'" % (frame, src))
                continue

            source = None
            sources = rv.commands.sourcesAtFrame(frame)
            if len(sources) > 0:
                source = sources[0]
            if source != current:
                continue # restrict to current source for now

            # load_version_id_from_source expects a group name
            group_name = rv.commands.nodeGroup(source)
            info = self.load_version_id_from_session(group_name)
            sframe = rv.extra_commands.sourceFrame(frame)

            if info:
                tgt = "%s/annotation_ver_%d.%d.jpg" % (tempdir, info['version.Version.id'], sframe)
            else:
                tgt = "%s/annotation.%d.jpg" % (tempdir, sframe)

            shutil.move(src, tgt)
            attachments.append(tgt)

            for prop in props:
                rv.commands.newProperty(prop, rv.commands.IntType, 1)
                rv.commands.setIntProperty(prop, [1234], True) # should be note id

        os.remove(session)
#         shutil.rmtree(os.path.dirname(session))
        self.submit_note_attachments(attachments)

    def __init__(self, app):
        rv.rvtypes.MinorMode.__init__(self)
        self._bundle = sgtk.platform.current_bundle()
        
        self.note_dock = None
        self.tray_dock = None
        self.tab_widget = None
        self.mini_cut = False
        self.detail_version_id = None

        self._tray_height = 96

        self.last_mini_center = None
        self._mini_before_shots = 2
        self._mini_after_shots = 2
        self._mini_cut_seq_name = None
        self.mini_cut_seq_node = None

        self.details_panel = None
        self.details_pinned_for_playback = False
        self.details_dirty = False

        self.pinned_items = []

        # RV specific
        # the current sequence node
        self.cut_seq_node = None
        self.cut_seq_name = None
        self.loaded_sources = {}
        self._layout_node = None
        self.mod_seq_node = None
        self.want_stacked = False
        self.version_swap_out = None
        self.no_cut_context = False

        self.version_id = -1
        self.entity_from_gma = None
        self.project_entity = None

        # related cuts menu
        self.related_cuts_entity = None
        self.related_cuts = None

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
                ('play-start', self.on_play_state_change, ""),
                ('play-stop', self.on_play_state_change, ""),
                ('view-size-changed', self.on_view_size_changed, ''),
                ('new_note_screenshot', self.makeNoteAttachments, ''),
                ],
                [("SG Review", [
                    ("Submit Tool", self.launchSubmitTool, None, lambda: rv.commands.UncheckedMenuState),
                    ("_", None)]
                )],
                None);
       
    def activate(self):
        rv.rvtypes.MinorMode.activate(self)

    def deactivate(self):
        rv.rvtypes.MinorMode.deactivate(self)
              

    ################################################################################### qt stuff down here. 

    def submit_note_attachments (self, attachments):
        self.details_panel.add_note_attachments(attachments)

    def load_data(self, entity):
        self._app.engine.log_info( "load_data with %r" % entity )
        self.version_id = entity['id']
        try:
            self.details_panel.load_data(entity)
        except Exception as e:
            self._app.engine.log_error("DETAILS PANEL: sent %r got %r" % (entity, e))
        # saw False even if we fail? endless loop? delay?
        self.details_dirty = False
 
    def init_ui(self, note_dock, tray_dock, version_id):
        self.note_dock = note_dock
        self.tray_dock = tray_dock
        
        # Setup the details panel.
        self.details_panel = DetailsPanelWidget()
        self.note_dock.setWidget(self.details_panel)
        
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

        self.tray_dock.setMinimumSize(QtCore.QSize(720,self._tray_height + 60))
        
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
        
        # CONNECTIONS
        self.tray_model.data_refreshed.connect(self.on_data_refreshed)
        self.tray_model.cache_loaded.connect(self.on_cache_loaded)
        self.tray_list.clicked.connect(self.tray_clicked)        
        self.tray_list.doubleClicked.connect(self.tray_double_clicked)

        self.tray_button_entire_cut.clicked.connect(self.on_entire_cut)
        self.tray_button_mini_cut.clicked.connect(self.on_mini_cut)
        
        self.tray_main_frame.tray_button_latest_pipeline.clicked.connect(self.load_sequence_with_versions)

        self.details_timer = QTimer(rv.qtutils.sessionWindow())
        self.note_dock.connect(self.details_timer, SIGNAL("timeout()"), self.check_details)
        self.details_timer.start(1000)

        # self.create_related_cuts_menu(None)
        # stuff = None
        # self.popup_test(stuff)


    def get_version_from_id(self, id):
        self._app.engine.log_info('get_version_from_id %r' % QtCore.QThread.currentThread() )
        v_fields = [
            "sg_path_to_frames", "id",
            "sg_first_frame", "sg_last_frame",
            "sg_path_to_movie", "sg_movie_aspect_ratio",
            "sg_movie_as_slate", "sg_frames_aspect_ratio",
            "sg_frames_has_slate", "image", "code",
            "sg_uploaded_movie_frame_rate", "sg_uploaded_movie_mp4", 
        ]
        # get the version info we need
        version  = self._bundle.shotgun.find_one("Version", [["id", "is", id]], v_fields)
        if not version:
            self._app.engine.log_error('no version for id %r' % id)
            return None
        return self.convert_sg_dict(version)

    def on_id_from_gma(self, event):
        self._app.engine.log_info("on_id_from_gma  %r" % (QtCore.QThread.currentThread() ) )
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
                self.tray_dock.show()
                self.load_tray_with_cut_id(d['id'])
            if d['type'] == "Version":
                self.tray_dock.hide()
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
                self.tray_dock.show()
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
        self._app.engine.log_info('replace_version_in_sequence %r' % QtCore.QThread.currentThread() )
        
        fno = rv.commands.frame()    
        for version in versions:
            version = self.convert_sg_dict(version)
 
            # ok, selected cutitem in tray is destination for this version
            ph_version = self.load_version_id_from_session()
            if 'ui_index' not in ph_version:
                self._app.engine.log_error('ui_index missing from %r' % ph_version)

            f = self.get_media_path(version)

            try:
                
                source_obj = {}                                                        
                if version['version.Version.id'] in self.loaded_sources:
                    source_obj = self.loaded_sources[version['version.Version.id']]
                else:
                    source_name = rv.commands.addSourceVerbose([f])
                    fk = version['version.Version.id']
                    source_obj['group_name'] = rv.commands.nodeGroup(source_name)
                    self.loaded_sources[fk] = source_obj
                source_prop_name = ("%s.cut_support.json_sg_data") % source_obj['group_name']

                if version['version.Version.code']:
                    rv.extra_commands.setUIName(source_obj['group_name'], version['version.Version.code'])
                

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
        self._app.engine.log_info('load_sequence_with_versions %r' % QtCore.QThread.currentThread() )
        
        
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
            f = self.get_media_path(sg)

            # if not f:
            #     f =  'black,start=%d,end=%d.movieproc' % (sg['sg_first_frame'], sg['sg_last_frame'])

            try:
                if f:
                    fk = sg['version.Version.id']
                    source_obj = {}   
                    if fk in self.loaded_sources:
                        source_obj = self.loaded_sources[fk]
                    else:
                        source_obj['source_name'] = rv.commands.addSourceVerbose([f])
                        source_obj['group_name'] = rv.commands.nodeGroup(source_obj['source_name'])
                        self.loaded_sources[fk] = source_obj
                    rv.extra_commands.setUIName(source_obj['group_name'], sg['version.Version.code'])
                
                else:
                    self._app.engine.log_info("load_sequence_with_versions: f is %r" % f)
                    continue
            except Exception as e:
                self._app.engine.log_error( "load_sequence_with_versions: %r" % e )

            source_prop_name = ("%s.cut_support.json_sg_data") % source_obj['group_name']
            try:
                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)
                json_sg_item = json.dumps(sg)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                self._app.engine.log_error("load_sequence_with_versions %r" % e)
                # print "%r" % sg

            #(num_plus, _) = source_name.split('_')
            v_source_names.append(source_obj['group_name'])
 
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
        self.tray_dock.hide()
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
        self._app.engine.log_info('load_tray_with_cut_id %r' % QtCore.QThread.currentThread() )
        
        if cut_id:
            self.tray_cut_id = cut_id
        
        # we need to know the project id to make the menus happen,

        tray_filters = [ ['cut','is', {'type':'Cut', 'id': self.tray_cut_id }] ]

        tray_fields= ["cut_item_in", "cut_item_out", "cut_order",
                "edit_in", "edit_out", "code", "entity", "shot",
                "version.Version.sg_path_to_frames", "version.Version.id",
                "version.Version.sg_first_frame", "version.Version.sg_last_frame",
                "version.Version.sg_path_to_movie", "version.Version.sg_movie_aspect_ratio",
                "version.Version.sg_movie_as_slate", "version.Version.sg_frames_aspect_ratio",
                "version.Version.sg_frames_has_slate", "version.Version.image",
                "version.Version.code", "version.Version.sg_status_list", "version.Version.entity",
                "version.Version.sg_uploaded_movie_frame_rate", "version.Version.sg_uploaded_movie_mp4", 
                "cut.Cut.code", "cut.Cut.id", "cut.Cut.version", "cut.Cut.fps", "cut.Cut.revision_numnber",
                "cut.Cut.cached_display_name", "cut.Cut.entity", "cut.Cut.project", "cut.Cut.version.Version.id", 
                "cut.Cut.version.Version.sg_first_frame", "cut.Cut.version.Version.sg_last_frame",
                "cut.Cut.version.Version.sg_path_to_movie", "cut.Cut.version.Version.sg_path_to_frames"]

        orders = [{'field_name':'cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CutItem", filters=tray_filters, fields=tray_fields, order=orders)
        
        if self.mini_cut:
            self.on_entire_cut()


    def on_entire_cut(self):
        if self.no_cut_context or not self.cut_seq_name:
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
        
        if not self.tray_list.selectionModel().selectedIndexes():
            self._app.engine.log_error("No shot selected for minicut.")
            return

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

    def get_media_path(self, sg, preferred_type=None):
        # sg is a dict that represents a row
        # preferred_type is movie or frames
        # refactor to pick that one first
        # if theres no frame play movie and vice versa

        if not sg:
            self._app.engine.log_error("%r passed into get_media_path." % sg)
            return None

        if 'version.Version.sg_path_to_frames' not in sg:
            sg = self.convert_sg_dict(sg)
        
        if not sg['version.Version.id']:
            #sub in the base version
            if sg['cut.Cut.version.Version.sg_path_to_frames']:
                return sg['cut.Cut.version.Version.sg_path_to_frames']
            if sg['cut.Cut.version.Version.sg_path_to_movie']:
                return sg['cut.Cut.version.Version.sg_path_to_movie']
        else:
            # prefer frames
            if sg['version.Version.sg_path_to_frames']:
                return sg['version.Version.sg_path_to_frames']
            if sg['version.Version.sg_path_to_movie']:
                return sg['version.Version.sg_path_to_movie']
 
        # if theres a cut_item_in use that?
        if 'cut_item_in' in sg:
            s = 'black,start=%d,end=%d.movieproc' % (sg['cut_item_in'], sg['cut_item_out'])
            return s

        start = 1
        end = 100
        
        if not sg['version.Version.id']:
            if sg['cut.Cut.version.Version.sg_first_frame']:
                start = sg['cut.Cut.version.Version.sg_first_frame']
      
            if sg['cut.Cut.version.Version.sg_last_frame']:
                end = sg['cut.Cut.version.Version.sg_last_frame']
        else:
            if sg['version.Version.sg_first_frame']:
                start = sg['version.Version.sg_first_frame']
      
            if sg['version.Version.sg_last_frame']:
                end = sg['version.Version.sg_last_frame']
 
        s = 'black,start=%d,end=%d.movieproc' % (start, end)
 
        return s
     
    def createText(self, node, text, hpos, vpos):

        rv.commands.newProperty('%s.position' % node, rv.commands.FloatType, 2)
        rv.commands.newProperty('%s.color' % node, rv.commands.FloatType, 4)
        rv.commands.newProperty('%s.spacing' % node, rv.commands.FloatType, 1)
        rv.commands.newProperty('%s.size' % node, rv.commands.FloatType, 1)
        rv.commands.newProperty('%s.scale' % node, rv.commands.FloatType, 1)
        rv.commands.newProperty('%s.rotation' % node, rv.commands.FloatType, 1)
        rv.commands.newProperty("%s.font" % node, rv.commands.StringType, 1)
        rv.commands.newProperty("%s.text" % node, rv.commands.StringType, 1)
        rv.commands.newProperty('%s.debug' % node, rv.commands.IntType, 1)

        rv.commands.setFloatProperty('%s.position' % node, [ float(hpos), float(vpos) ], True)
        rv.commands.setFloatProperty('%s.color' % node, [ 1.0, 1.0, 1.0, 1.0 ], True)
        rv.commands.setFloatProperty('%s.spacing' % node, [ 1.0 ], True)
        rv.commands.setFloatProperty('%s.size' % node, [ 0.004 ], True)
        rv.commands.setFloatProperty('%s.scale' % node, [ 1.0 ], True)
        rv.commands.setFloatProperty('%s.rotation' % node, [ 0.0 ], True)
        rv.commands.setStringProperty("%s.font" % node, [""], True)
        rv.commands.setStringProperty("%s.text" % node, [text], True)
        rv.commands.setIntProperty('%s.debug' % node, [ 0 ], True)

    def set_session_prop(self, name, item):
        self._app.engine.log_info('set_session_prop %r' % QtCore.QThread.currentThread() )
        
        try:
            if not rv.commands.propertyExists(name):
                rv.commands.newProperty(name, rv.commands.StringType, 1)
            cut_json = json.dumps(item)
            rv.commands.setStringProperty(name, [cut_json], True)
        except Exception as e:
            print "ERROR: set_session_prop %r" % e

    def convert_sg_dict(self, sg_dict):
        if not sg_dict:
            self._app.engine.log_error('EMPTY dict passed to convert_sg_dict.')
            return sg_dict

        sg_dict_new = copy.copy(sg_dict)
        #if not 'version.Version.sg_path_to_frames' in sg_dict:

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
                sg_dict_new[k] = sg_dict[s]

        # check for missing media

        return sg_dict_new

    # used by the related cuts menu
    def request_cuts_from_entity(self, conditions):
        self._app.engine.log_info('request_cuts_from_entity %r %r' % ( QtCore.QThread.currentThread(), conditions) )
        
        # conditions: ['entity', 'is', {'type': 'Sequence', 'id': 31, 'name': '08_a-team'}]
        
        if not self.project_entity:
            self._app.engine.log_error('project entity does not exist!')
            return None

        cuts = self._bundle.shotgun.find('Cut',
                        filters=[ conditions, ['project', 'is', { 'id': self.project_entity['id'], 'type': 'Project' } ]],
                        fields=['id', 'entity', 'code', 'cached_display_name'],
                        order=[
                            # {'field_name': 'entity', 'direction': 'asc'}, 
                            {'field_name': 'code', 'direction': 'asc'}, 
                            {'field_name': 'cached_display_name', 'direction': 'asc'}
                            ])

        last_entity_group = -1
        groups = []

        for cut in cuts:

            if (last_entity_group == -1) or (groups[last_entity_group]['entity'] != cut['entity']):
                last_entity_group = last_entity_group+1
                last_cut_group = -1
                groups.append( { 'entity': cut['entity'], 'cuts': [] } )

            rev_cuts = groups[last_entity_group]['cuts']
            if (last_cut_group == -1) or ( rev_cuts[last_cut_group]['code'] != cut['code'] ):
                last_cut_group = last_cut_group + 1
                rev_cuts.append( { 'code': cut['code'], 'revisions': [] } )

            revisions = rev_cuts[last_cut_group]['revisions']

            revisions.append( { 'id': cut['id'], 'cached_display_name': cut['cached_display_name'] } )

        return groups

    def on_browse_cut(self):
        sg_data = self.load_version_id_from_session()

        # are we stopped? on a selected item? mix in second related shots
        # print "on_browse_cut: %r %r" % (sg_data['cut.Cut.entity'], sg_data['version.Version.entity'])
        if sg_data['version.Version.entity']:
            if sg_data['version.Version.entity']['type'] == "Shot":
                self.create_related_cuts_menu(sg_data['cut.Cut.entity'], sg_data['version.Version.entity'])
                return

        if sg_data['cut.Cut.entity']['type'] == "Scene":
            self.create_related_cuts_menu(sg_data['cut.Cut.entity'], sg_data['shot'])
            return

        # self.create_related_cuts_menu(sg_data['cut.Cut.entity'], sg_data['version.Version.entity'])
        # forcing a test....
        # entity = {}
        # entity['id'] = 6
        # entity['type'] = 'Cut'

        # version
        # entity['id'] = 7406
        # entity['type'] = 'Version'

        # entity['id'] = 62
        # entity['type'] = "Playlist"
        # rv.commands.sendInternalEvent('id_from_gma', json.dumps(entity))        


    def handle_menu(self, action=None):
        self._app.engine.log_info("handle_menu called with action %r" % action)
        if action:
            self.load_tray_with_cut_id(action.data()['id'])
            self._app.engine.log_info("action.data: %r" % action.data()) 

    def create_related_cuts_menu(self, entity_in, shot_entity=None):
        # entity_in is in most cases as Sequence entity, currently whatever is in cut.Cut.entity
        self._app.engine.log_info( "create_related_cuts_menu: %r %r" % (entity_in, shot_entity))
        # conditions: ['entity', 'is', {'type': 'Sequence', 'id': 31, 'name': '08_a-team'}]
        conditions = ['entity', 'is', entity_in]

        # to know if we need to refresh
        if self.related_cuts_entity:
            if self.related_cuts_entity['id'] != entity_in['id']:
                self.related_cuts_entity = entity_in
                # hang on to the answer
                self.related_cuts = self.request_cuts_from_entity(conditions)
        else:
                self.related_cuts_entity = entity_in
                # hang on to the answer
                self.related_cuts = self.request_cuts_from_entity(conditions)
            
        # make a working copy
        results = copy.copy(self.related_cuts)
        # merge the shots stuff into results
        cut_map = {}
        if shot_entity:
            # look up related shots
            shot_id = shot_entity['id']
            shot_results = self.request_cuts_from_entity(['cut_items.CutItem.shot', 'is', { 'id': shot_id, 'type': 'Shot' }])
            print "shot_results: %r" % shot_results
            shot_cut_ids = []
            for x in shot_results[0]['cuts']:
                for c in x['revisions']:
                    cut_map[c['id']] = c
                    shot_cut_ids.append(c['id'])
            # print "cut_map: %r" % cut_map

            cut_ids = []
            for x in results[0]['cuts']:
                for c in x['revisions']:
                    cut_ids.append(c['id'])

            # print "cut_ids: %r" % cut_ids
            # print "shot_cut_ids: %r" % shot_cut_ids
            for n in shot_cut_ids:
                if n not in cut_ids:
                    print "WE FOUND A CUT TO INSERT %r" % cut_map[n]
                    for x in results[0]['cuts']:
                        for c in x['revisions']:
                            if cut_map[n]['cached_display_name'] <= c['cached_display_name']:
                                # insert this cut_map into the revisions array
                                x['revisions'].append(cut_map[n])
                                break

        menu = QtGui.QMenu(self.tray_button_browse_cut)
        menu.aboutToShow.connect(self.on_browse_cut)
        menu.triggered.connect(self.handle_menu)
        action = QtGui.QAction(self.tray_button_browse_cut)
        action.setText('Related Cuts')
        menu.addAction(action)
        menu.addSeparator()

        last_menu = menu
        for x in results[0]['cuts']:
            if 'code' not in x:
                # print "%r" % x
                x['code'] = x['name']
            action = QtGui.QAction(self.tray_button_browse_cut)
            action.setText(x['code'])
            en = {}
            en['id'] = x['revisions'][0]['id']
            en['type'] = 'Cut'
            action.setData(en)
            if len(x['revisions']) > 1:
                last_menu = last_menu.addMenu(x['code'])
                for n in x['revisions']:
                    action = QtGui.QAction(self.tray_button_browse_cut)
                    action.setText(n['cached_display_name'])
                    sub_en = {}
                    sub_en['id'] = n['id']
                    sub_en['type'] = 'Cut'
                    action.setData(sub_en)
                    last_menu.addAction(action)
                last_menu = menu
            else:
                last_menu = menu
                last_menu.addAction(action)


        self.tray_button_browse_cut.setMenu(menu)        

    def find_base_version_for_cut(self, entity):
        self._app.engine.log_info('find_base_version_for_cut not IMPLEMENTED! %r' % entity)
        pass
        # cut.Cut.version
        #sg_data = self.get_version_from_id(entity['id'])
        #print "BASE Version: %r" % sg_data
        #return sg_data

    def create_source_from_version(self, sg_item, source_incr):
        """
        creates a new source and returns True if we havent seen it before
        """
        if not sg_item:
            self._app.engine.log_error("create_source_from_version: %r" % sg_item)
            return False

        sg_item = self.convert_sg_dict(sg_item)


        fk = sg_item['version.Version.id']
        if not fk:
            # if there's no version, see if we've loaded the base version already
            if sg_item['cut.Cut.version.Version.id'] in self.loaded_sources:
                return False
            
        if fk in self.loaded_sources:
            # group_name = self.loaded_sources[fk]['group_name']
            return False
        else:
            f = self.get_media_path(sg_item)
            source_name = None
            try:
                source_name = rv.commands.addSourceVerbose([f])
            except Exception as e:
                self._app.engine.log_error( '%r' %  e )
                self._app.engine.log_info('trying to create black with data from version: %r' % sg_item['version.Version.id'])
                if sg_item['version.Version.sg_first_frame'] and sg_item['version.Version.sg_last_frame']:
                    s = 'black,start=%d,end=%d.movieproc' % (sg_item['version.Version.sg_first_frame'], sg_item['version.Version.sg_last_frame'])
                else:
                    self._app.engine.log_info('First and last frame not found for version: %r. using 1-100.' % sg_item['version.Version.id'])
                    s = 'black,start=%d,end=%d.movieproc' % (1, 100)
                    sg_item['version.Version.sg_first_frame'] = 1
                    sg_item['version.Version.sg_last_frame'] = 100

                self._app.engine.log_info("trying: %r instead" % s)
                source_name = rv.commands.addSourceVerbose([s])

            group_name = rv.commands.nodeGroup(source_name)

            if sg_item['version.Version.code']:
                rv.extra_commands.setUIName(group_name, sg_item['version.Version.code'])
            
            self.loaded_sources[fk] = {}
            self.loaded_sources[fk]['group_name'] = group_name
            self.loaded_sources[fk]['source_name'] = source_name
            self.loaded_sources[fk]['source_index'] = source_incr

            if 'movieproc' in f:
                # group_name returned an empty list here. source name works.
                overlays = rv.extra_commands.associatedNodes("RVOverlay",source_name)
                # node need to be a component name ...
                self.createText(overlays[0] + '.text:mytext', sg_item['version.Version.code'] + '\nis missing.', -0.5, 0.0)
            return True

    # the way data from shotgun gets into the tray
    def on_data_refreshed(self, was_refreshed):
        self._app.engine.log_info('on_data_refreshed: %r' % str(QtCore.QThread.currentThread()))
        # tray is cleared by ShotgunModel _load_data

        self.swapped_sources = None
        self.project_entity = None

        v_id = -1

        # first see if we have a selection
        # this was an attempt to make sure we end up in the same place
        cur_index = self.tray_list.currentIndex()
        if cur_index:
            sg_item = shotgun_model.get_sg_data(cur_index)
            if sg_item:
                v_id = sg_item['version.Version.id']

        # tray proxy model sorting in cut order
        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)
        rows = self.tray_proxyModel.rowCount()
 
        # this should be impossible since all id's are fed in...?
        if rows < 1:
            self._app.engine.log_error('Query returned no rows.')
            # clear tray and draw something on screen
            # label into tray saying 'no cut items'
            return
 
        self.rv_source_nums = []
        self.rv_frames = []
        self.rv_ins = []
        self.rv_outs = []
        self.tray_sources = []

        source_incr = 0
        timeline_incr = 1

        tray_seq_name = None
        final_selection = None

        # keys and array to hold values detrived from result set into sequence level node.
        cut_items = []
        cutitem_keys = ["cut_item_in", "cut_item_out", "cut_order", "edit_in", "edit_out", "id", "code"]

        for x in range(0, rows):
            item = self.tray_proxyModel.index(x, 0)
            sg_item_orig = shotgun_model.get_sg_data(item)
            # print "%d is %r %r %r " % (x, sg_item_orig['cut.Cut.version'], sg_item_orig['cut.Cut.version.Version.id'], sg_item_orig['cut.Cut.version.Version.sg_first_frame'])
            if not sg_item_orig:
                # put an error message into the tray for that item
                self._app.engine.log_error("What do I do when there is no data at all for item %d" % item.row())
                sg_item_orig = {}
                sg_item_orig['sg_first_frame'] = 1
                sg_item_orig['sg_last_frame'] = 100
                sg_item_orig['sg_path_to_movie'] = '/tmp/foodles.mov'

            # adapting pure version queries to match key naming in results from cut queries.
            sg_item = self.convert_sg_dict(sg_item_orig)
            #print "%d is %r" % (x, sg_item)
            
            # needed for the related cuts menu.
            if not self.project_entity:
                #print "PROJECT: %r" % sg_item
                #print "tray cut id %d" % self.tray_cut_id 
                self.project_entity = sg_item['cut.Cut.project']
                       
            # finding keys we want on the source node
            if 'cut_item_in' in sg_item:
                cutitem_dict = dict ( [(k, sg_item[k]) for k in cutitem_keys])
                cut_items.append(cutitem_dict)

            # this is used for a currently disabled feature:
            # when a version is viewed, lookup the latest cut and 
            # swap that version into it.
            if self.version_swap_out:
                if cutitem_dict['id'] == self.version_swap_out['cutitem_id']:
                    # update sg_item with new fields.
                    tmp_dict = self.convert_sg_dict(self.version_swap_out)
                    for k in tmp_dict:
                        sg_item[k] = tmp_dict[k]
            
            # if version id is none then lookup base version id with
            # cut.Cut.version entity
            
            # moving to create source
            #if not sg_item['version.Version.id']:
            #    self._app.engine.log_info("finding base version with cut.Cut.version: %r" % sg_item['cut.Cut.version'])
            #    sg_item = self.find_base_version_for_cut(sg_item['cut.Cut.version'])

            
            if self.create_source_from_version(sg_item, source_incr):
                source_incr = source_incr + 1

            if not sg_item:
                self._app.engine.log_error('sg_item is null for item %d' % x)
                continue

            fk = sg_item['version.Version.id']
                 
            source_prop_name = ("%s.cut_support.json_sg_data") % self.loaded_sources[fk]['group_name']
            
            # Add source/version to list of future inputs for this sequence
            # node
            self.tray_sources.append(self.loaded_sources[fk]['group_name'])
 
            try:
                # these should be at the cut item (sequence) level
                # this should also move into the 'only if new source' block

                # XXX ui_index is the index of this source/version in the list
                # of inputs for this sequence.
                # sg_item['ui_index'] = self.loaded_sources[fk]['source_index']
                sg_item['ui_index'] = len(self.tray_sources) - 1

                sg_item['tl_index'] = timeline_incr
                if not rv.commands.propertyExists(source_prop_name):
                    rv.commands.newProperty(source_prop_name, rv.commands.StringType, 1)
                json_sg_item = json.dumps(sg_item)
                rv.commands.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                print "ERROR: on_data_refreshed %r" % e

            # need to remember source numbers so that we can reuse a version if it appears multiple times
            # source numbers are the index into the inputs array, being created as we move thru this loop

            # XXX  The line above that is modifying tray_sources is adding what
            # will become an input for every CutItem.  That means that the
            # edl.sources array (which contains indices into the inputs array)
            # will just be 1-to-1 with those indices.  IE be 0,1,2...n where
            # n-1 is size of inputs array.  It's only if we re-use inputs that
            # there will be more than one of the same index in the edl.sources
            # array. For example if we have 4 cut items, and #1 and #3 refer to
            # the same version/input, we could have edl.sources == 0,1,2,1.
            #
            # self.rv_source_nums.append(self.loaded_sources[fk]['source_index'])
            self.rv_source_nums.append(len(self.tray_sources) - 1)

            # would be looked up instead of icremented if source exists
            

            # playlist code? 
            # address difference between playlist versions and cutitem with no version (use base version)
            # in base layer case we use edit_in and edit_out instead of cut_item_in, etc.
            #print "WTF: %r" % sg_item
            # print sg_item['code']
            if 'cut_item_in' not in sg_item:
                sg_item['cut_item_in'] = sg_item['version.Version.sg_first_frame']
                sg_item['cut_item_out'] = sg_item['version.Version.sg_last_frame']
                print "HERE: %d %d" % (sg_item['version.Version.sg_first_frame'], sg_item['version.Version.sg_last_frame'])

            if not sg_item['cut_item_in'] or not sg_item['cut_item_out']:
                print "THERE?"
                # this logic was added to make certain incomplete cuts work...
                if 'edit_in' and 'edit_out' in sg_item:
                    if sg_item['edit_in'] and sg_item['edit_out']:
                        sg_item['cut_item_in'] = sg_item['edit_in']
                        sg_item['cut_item_out'] = sg_item['edit_out']
                else: 
                    sg_item['cut_item_in'] = sg_item['version.Version.sg_first_frame']
                    sg_item['cut_item_out'] = sg_item['version.Version.sg_last_frame']

            self.rv_ins.append( sg_item['cut_item_in'] )
            self.rv_outs.append( sg_item['cut_item_out'] )
            self.rv_frames.append(timeline_incr)
            
            timeline_incr = sg_item['cut_item_out'] - sg_item['cut_item_in'] + 1 + timeline_incr

            # if we had a version selected before the query we try to select it again when this cut is loaded
            if 'version.Version.id' in sg_item:
                if sg_item['version.Version.id'] == v_id:
                    final_selection = item
        
        tray_seq_name = 'unknown'

        # draw something in the tray
        if not sg_item:
            self._app.engine.log_error('SG_ITEM is null.')
            return

        # cached_display_name has the _002 suffix to indicate cut revision...
        if 'cut.Cut.code' in sg_item:
            tray_seq_name = sg_item['cut.Cut.cached_display_name']
        
        # these zeros ( and a 1 ) initialize the arrays for RV
        self.rv_source_nums.append(0)
        self.rv_ins.append(0)
        self.rv_outs.append(0)
        self.rv_frames.append(timeline_incr)

        # newNode for everything except sources
        # this lets us store multiple cuts in a session file later
        # and lets you flip between cuts via session browser
        self.cut_seq_node = rv.commands.newNode("RVSequenceGroup")

        # create a sequence level dict from sg_item
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

        #k = "%s.mode.autoEDL" % str(self.cut_seq_name)
        #if not rv.commands.propertyExists(k):
        #    rv.commands.newProperty(k, rv.commands.IntType, 1)

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

        # if we had a selection coming in, we move to that
        # not sure if these even works EXAMINE
        if final_selection:
            self.tray_list.selectionModel().select(final_selection, self.tray_list.selectionModel().ClearAndSelect)
        else:            
            zero_index = self.tray_model.createIndex(0, 0)
            self.tray_list.selectionModel().select(zero_index, self.tray_list.selectionModel().ClearAndSelect)
        
        self.tray_list.scrollTo(self.tray_proxyModel.index(0, 0), QtGui.QAbstractItemView.EnsureVisible)
        # triggers the details pane
        self.load_version_id_from_session()

        seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
        if not rv.commands.propertyExists(seq_pinned_name):
            rv.commands.newProperty(seq_pinned_name, rv.commands.IntType, 1)
        rv.commands.setIntProperty(seq_pinned_name, self.pinned_items, True)

        self.create_related_cuts_menu(sg_item['cut.Cut.entity'])
           
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

    def get_mini_values(self):
        self._mini_before_shots = self.tray_main_frame.mini_left_spinner.value()
        self._mini_after_shots = self.tray_main_frame.mini_right_spinner.value()
        print "MINI vals: %d %d" % (self._mini_before_shots, self._mini_after_shots)

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
        
        self.get_mini_values()

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

            f = self.get_media_path(sg)
            fk = sg['version.Version.id']
            source_obj = self.loaded_sources[fk]

            #(num_plus, _) = source_name.split('_')
            mini_source_names.append(source_obj['group_name'])
 
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
        
        f = self.get_media_path(sg_item)
        fk = sg_item['version.Version.id']
        # fk = urllib.quote_plus(f)
        source_obj = self.loaded_sources[fk]
        sel_version = self.load_version_id_from_session(source_obj['group_name'])
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



    # popup right side menu stuff from eric ... tested but not integrated yet.

    ##########################################################
    # the following came from cuts_helpers.js
    ##########################################################
    def get_default_version_entity_for_cut_item(self, cut_item, parent_cut):
        version = cut_item.get('version')
        if ( version == None ):
            if ( parent_cut and parent_cut.type == 'Cut' ):
                # If there is a cut, let's see if it has a version
                version = parent_cut.get('version')
                if version != None:
                    # for some reason the javascript code already has the status set in the entity hash!
                    # but in python we don't :-(
                    # The following will probably not work since we didnt query for that field on the parent cut!
                    # version['status'] = parent_cut.get('version.Version.sg_status_list')
                    version['status'] = 'Unknown'
        else:
            # for some reason the javascript code already has the status set in the entity hash!
            # but in python we don't :-(
            version['status'] = cut_item.get('version.Version.sg_status_list')

        return version


    # I dont really use this one but...
    def get_version_image_for_record(self, record, parent_record):
        # If no valid version is in record, return -1
        image = None

        if ( record.get('type') == 'Version' ):
            image = record.get('image')
        elif ( record.get('type') == 'CutItem' ):
            # the version image is in the version field
            version = record.get('version')
            if ( version ):
                image = record.get('version.Version.image')
            elif ( parent_record ):
                version = parent_record.get('version')
                if ( version ):
                    #hum not sure this will work if we didnt query for that field while doing the query for the cut
                    image = parent_record.get('version.Version.image')
        return image

    def find_filter(self, shot_filters, filter_path):
        for filter in shot_filters:
            if filter[0] == filter_path:
                if len(filter)>2:
                    return filter[2]
                else:
                    return None
        return None

    def show_menus(self, shot_filters):
        sg = self._bundle.shotgun
        project_id = 76
        print 'Status Menu:'
        print ''
        print '[ ] Any Status'
        print '-------------------'

        schema = sg.schema_field_read('Version', field_name='sg_status_list', project_entity={ 'id': project_id, 'type': 'Project' } )

        schema = schema.get('sg_status_list')
        schema = schema.get('properties')

        values = schema.get('valid_values').get('value')
        display_values = schema.get('display_values').get('value')

        filter = self.find_filter(shot_filters, 'sg_status_list')

        for value in values:
            display_value = display_values.get(value)
            if filter and value in filter:
                print '[x] %s (%s)' %(display_value, value)
            else:
                print '[ ] %s (%s)' %(display_value, value)

        print ''

        print 'Step Menu:'
        print ''
        print 'PIPELINE STEP PRIORITY'
        print '---------------------------'

        filter = self.find_filter(shot_filters, 'sg_task.Task.step')

        if len(filter) == 0:
            print '[x] Latest in Pipeline'
        else:
            print '[ ] Latest in Pipeline'

        shot_steps = sg.find('Step', 
            filters=[['entity_type', 'is', 'Shot' ]], 
            fields=['code', 'list_order', 'short_name', 'id'], 
            order=[{'field_name': 'list_order', 'direction': 'desc'}])

        for step in shot_steps:
            found = False
            if filter:
                for current_step in filter:
                    if current_step.get('id') == step.get('id'):
                        found = True
                        break
            if found:
                print '[x] %s' %step.get('code')
            else:
                print '[ ] %s' %step.get('code')

        print ''

    def request_data(self, shot_filters):

        print 'Here are the default versions used by that cut in the cut order:'
        print 'They should all be the ANIM ones, 15, 14, ..., 2, 1'
        print ''


        sg = self._bundle.shotgun
        cut_id = 6
        cut = sg.find_one('Cut', [['id', 'is', cut_id]], fields=['code', 'cached_display_name', 'entity'])

        cut_items = sg.find('CutItem',
                            filters=[['cut', 'is', [{ 'id': cut_id, 'type': 'Cut' }]]],
                            # there might be too many fields requested here but that will do for now
                            fields=['code', 'cut_item_in', 'cut_item_out', 'cut_order', 'shot', 'version', 'version.Version.sg_status_list', 'version.Version.image'],
                            order=[{'field_name': 'cut_order', 'direction': 'asc'}])

        map = {}

        if shot_filters != None:

            # project_entity = { 'id': project_id, 'type': 'Project' }

            shots = []

            for cut_item in cut_items:
                shot = cut_item.get('shot')
                if shot != None:
                    shots.append( { 'id': shot.get('id'), 'type': 'Shot' } )

            full_filters = self.build_version_filters( self.project_entity, shot_filters, shots)

            versions = sg.find('Version',
                                filters=full_filters,
                                fields=['id', 'code', 'image', 'sg_status_list', 'entity'],
                                additional_filter_presets = [
                                    {"preset_name": "LATEST", "latest_by": "BY_PIPELINE_STEP_NUMBER_AND_ENTITIES_CREATED_AT" }
                                ]
                                )

            for version in versions:
                shot = version.get('entity')
                if shot != None:
                    map[shot.get('id')] = version

        for cut_item in cut_items:
            shot = cut_item.get('shot')
            shot_id = None
            if shot != None:
                shot_id = shot.get('id')

            if shot_id in map:
                version = map[shot_id]
                version_entity = { 'id': version.get('id'), 'name': version.get('code'), 'type': 'Version', 'status': version.get('sg_status_list') }
                version_image = version.get('image')
            else:
                version_entity = self.get_default_version_entity_for_cut_item(cut_item, cut)
                version_image = self.get_version_image_for_record(cut_item, cut)

            status = version_entity.get('status')
            if status == None:
                status = "unknown"

            print 'version: name=%s, id=%s, status=%s' %(version_entity.get('name'), version_entity.get('id'), status )


    ##########################################################
    # the following came from review_app_data_manager.js
    ##########################################################
    def build_version_filters(self, project, shot_version_filters, shots):
        conditions = []
        # this.shot_version_filters is always defined when we get here but let's check anyway
        if ( shot_version_filters ):
            # let's use this.shot_version_filters but first let's remove the "ANY" filter

            for filter in shot_version_filters:
                # filter is like [ 'sg_task.Task.step', 'in', [ { 'id': 6, 'name': 'FX', 'type': 'Step' } ]

                # By convention an empty array for sub-array means ANY like "any status" or "latest in pipeline" etc
                # so let's just ignore this filter since it's any!
                if len(filter) > 2 and len(filter[2]) > 0:
                    conditions.append(filter)

        conditions.append(['entity', 'in', shots])

        if ( project ):
            conditions.append( [ 'project', 'is', [ { 'id': project.get('id'), 'type': 'Project' } ] ] )

        return conditions


    def popup_test(self, shot_filters):

        self.request_data(shot_filters)

        print ''
        print 'Now we will use the following shot filters:'
        print ''

        shot_filters = [ [ 'sg_task.Task.step', 'in', [ { 'id': 7, 'name': 'Light', 'type': 'Step' } ] ],
                         [ 'sg_status_list', 'in', ['rev'] ] ]


        self.show_menus(shot_filters)

        print 'Here are shot versions found in the cut order: '
        print 'Only a few LIGHT (aka TD) ones will be found because we also check for status=reviewed!'
        print 'when the query does not find anything we use the default version'

        print ''

        self.request_data(shot_filters)

        print ''
        print 'Finally we will use the latest-in-pipeline step:'
        print ''

        shot_filters = [ [ 'sg_task.Task.step', 'in', [] ],
                         [ 'sg_status_list', 'in', ['rev'] ] ]

        self.show_menus(shot_filters)

        print ''

        self.request_data(shot_filters)

