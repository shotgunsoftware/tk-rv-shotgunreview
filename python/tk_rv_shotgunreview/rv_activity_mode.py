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

import rv.rvtypes as rvt
import rv.commands as rvc
import rv.extra_commands as rve
import rv.qtutils as rvqt

shotgun_view = tank.platform.import_framework("tk-framework-qtwidgets", "views")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_data = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")

from .tray_delegate import RvTrayDelegate
from .details_panel_widget import DetailsPanelWidget
from .popup_utils import PopupUtils

import sgtk

import pprint
pp = pprint.PrettyPrinter(indent=4)

def groupMemberOfType(node, memberType):
    for n in rvc.nodesInGroup(node):
        if rvc.nodeType(n) == memberType:
            return n
    return None

class Preferences:
    def __init__(self):
        self.group = "sg_review_mode"
        g = self.group

        self.preferred_media_type   = rvc.readSettings(g, "preferred_media_type",   "Movie")
        self.preferred_compare_mode = rvc.readSettings(g, "preferred_compare_mode", "Grid")
        self.startup_view_details   = rvc.readSettings(g, "startup_view_details",   False)
        self.startup_view_tray      = rvc.readSettings(g, "startup_view_tray",      False)
        self.auto_show_tray         = rvc.readSettings(g, "auto_show_tray",         True)
        self.auto_show_details      = rvc.readSettings(g, "auto_show_details",      True)
        self.pin_details            = rvc.readSettings(g, "pin_details",            True)
        self.auto_play              = rvc.readSettings(g, "auto_play",              True)
        self.mini_left_count        = rvc.readSettings(g, "mini_left_count",        2)
        self.mini_right_count       = rvc.readSettings(g, "mini_right_count",       2)

        # pipeline filter is odd because a valid input into the query preset is [] meaning 'latest in pipeline'
        # so it has 3 states. a list with stuff, an empty list (latest in pipe) and None.
        self.pipeline_filter_json   = rvc.readSettings(g, "pipeline_filter",        "None")
        self.status_filter_json     = rvc.readSettings(g, "status_filter",          "[]")

        self.pipeline_filter = None
        s = json.loads(self.pipeline_filter_json)
        # there is no None in JSON, so we store a "None" string to mean this.
        if s == "None":
            self.pipeline_filter = None
        else:
            self.pipeline_filter = s

        self.status_filter = []
        s = json.loads(self.status_filter_json)
        if s == "None":
            self.status_filter = []
        else:
            self.status_filter = s

        print "PREFS: %r %r" % ( self.status_filter, self.pipeline_filter)

    def save(self):
        g = self.group

        rvc.writeSettings(g, "preferred_compare_mode", self.preferred_compare_mode)
        rvc.writeSettings(g, "preferred_media_type",   self.preferred_media_type)
        rvc.writeSettings(g, "startup_view_details",   self.startup_view_details)
        rvc.writeSettings(g, "startup_view_tray",      self.startup_view_tray)
        rvc.writeSettings(g, "auto_show_details",      self.auto_show_details)
        rvc.writeSettings(g, "auto_show_tray",         self.auto_show_tray)
        rvc.writeSettings(g, "pin_details",            self.pin_details)
        rvc.writeSettings(g, "auto_play",              self.auto_play)
        rvc.writeSettings(g, "mini_left_count",        self.mini_left_count)
        rvc.writeSettings(g, "mini_right_count",       self.mini_right_count)

        # json doesnt take None as input.
        if self.pipeline_filter == None:
            self.pipeline_filter = "None"
        json_pipeline = json.dumps(self.pipeline_filter)
        rvc.writeSettings(g, "pipeline_filter",        json_pipeline)

        if self.status_filter == None:
            self.status_filter = "None"
        json_status = json.dumps(self.status_filter)
        rvc.writeSettings(g, "status_filter",          json_status)

class MediaType:
    def __init__(self, name, path_field, slate_field, aspect_field):
        self.name = name
        self.path_field = path_field
        self.slate_field = slate_field
        self.aspect_field = aspect_field

standard_media_types = dict(
        Movie=MediaType ("Movie",  "sg_path_to_movie",  "sg_movie_has_slate",   "sg_movie_aspect_ratio"),
        Frames=MediaType("Frames", "sg_path_to_frames", "sg_frames_have_slate", "sg_frames_aspect_ratio")
    )

class MiniCutData:
    def __init__(self, active, focus_clip=-1, first_clip=-1, last_clip=-1):
        self.active     = active
        self.focus_clip = focus_clip
        self.first_clip = first_clip
        self.last_clip  = last_clip

    def store_in_session(self, node):
        setProp(node + ".mini_cut.active",     int(self.active))
        setProp(node + ".mini_cut.focus_clip", self.focus_clip)
        setProp(node + ".mini_cut.first_clip", self.first_clip)
        setProp(node + ".mini_cut.last_clip",  self.last_clip)

    @staticmethod
    def load_from_session(seq_node=None):

        if seq_node == None:
            seq_group = rvc.viewNode()
            if rvc.nodeType(seq_group) == "RVSequenceGroup":
                seq_node = groupMemberOfType(seq_group, "RVSequence")

        if seq_node is None:
            return None
        
        active     = bool(getIntProp(seq_node + ".mini_cut.active",     False))
        focus_clip =      getIntProp(seq_node + ".mini_cut.focus_clip", -1)
        first_clip =      getIntProp(seq_node + ".mini_cut.first_clip", -1)
        last_clip  =      getIntProp(seq_node + ".mini_cut.last_clip",  -1)

        return MiniCutData(active, focus_clip, first_clip, last_clip)

required_version_fields = [
    "code",
    "id",
    "entity",
    "project",
    "sg_first_frame",
    "sg_last_frame",
    "sg_frames_aspect_ratio",
    "sg_frames_have_slate",
    "sg_movie_aspect_ratio",
    "sg_movie_has_slate",
    "sg_path_to_frames",
    "sg_path_to_movie",
    "sg_status_list",
    "sg_uploaded_movie_frame_rate"
    ]

def setProp(prop, value):
    '''
    Convenience function to set Int of String proprty, creating it first if
    necessary.  In coming value can be scalar or list of the appropriate type.
    '''
    if type(value) == int or (type(value) == list and len(value) and type(value[0]) == int):
        if not rvc.propertyExists(prop):
            rvc.newProperty(prop, rvc.IntType, 1)
        rvc.setIntProperty(prop, value if (type(value) == list) else [value], True)

    elif ((type(value) == str     or (type(value) == list and len(value) and type(value[0]) == str)) or 
          (type(value) == unicode or (type(value) == list and len(value) and type(value[0]) == unicode))):
        if not rvc.propertyExists(prop):
            rvc.newProperty(prop, rvc.StringType, 1)
        rvc.setStringProperty(prop, value if (type(value) == list) else [value], True)
            
def getIntProp(prop, default):
    '''
    Convenience function to get the value of an Int proprty, returning the
    given default value if the property does not exist or has no contents.  If
    the given default value is scalar only the first value of the properties
    content array is returned.
    '''
    val = default
    if rvc.propertyExists(prop):
        vals = rvc.getIntProperty(prop)
        if vals and len(vals):
            if type(default) == list:
                val = vals
            else:
                val = vals[0]
    return val
    
def getStringProp(prop, default):
    '''
    Convenience function to get the value of an String proprty, returning the
    given default value if the property does not exist or has no contents.  If
    the given default value is scalar only the first value of the properties
    content array is returned.
    '''
    val = default
    if rvc.propertyExists(prop):
        vals = rvc.getStringProperty(prop)
        if vals and len(vals):
            if type(default) == list:
                val = vals
            else:
                val = vals[0]
    return val
    
class RvActivityMode(rvt.MinorMode):
    
    def check_details(self):
        if self.details_dirty:
            version_id = self.load_version_id_from_session()
            if version_id and not rvc.isPlaying():
                if self.target_entity and self.target_entity['type'] != "Cut":
                    self.update_cuts_with()
                self._popup_utils.request_related_cuts_from_models()

    def current_source(self):
        """
        The "current source" is the "first" RVSourceGroup used to render this
        frame.  So in a simple Sequence, it will be the Source showing in the
        current clip of the EDL.  In a Stack it will be the "top" element.  In a
        standard tiled Layout it will be (often) the upper-left element.
        """
        group_name = None

        saf = rvc.sourcesAtFrame(rvc.frame())
        if saf:
            source_name = str(saf[0])
            group_name = rvc.nodeGroup(source_name)
            
        return group_name

    def version_id_from_source(self, group_name=None):
        
        if not group_name:
            group_name = self.current_source()
                
        if group_name:
            return getIntProp(group_name + ".sg_review.version_id", None)

        return None

    def version_data_from_source(self, group_name=None):
        
        if not group_name:
            group_name = self.current_source()
                
        if group_name:
            version_data_str = getStringProp(group_name + ".sg_review.version_data", None)
            if version_data_str:
                try:
                    return json.loads(version_data_str)
                except Exception as e:
                    self._app.engine.log_error("version_data_from_source: %r" % e)

        return None

    def load_version_id_from_session(self, group_name=None):
        
        version_id = self.version_id_from_source(group_name)

        # version_id might be None here, which is fine, since that will clear
        # the details pane.

        self.load_data({"type": "Version", "id": version_id})

        self.details_dirty = False

        return version_id

    # RV Events

    def replaceWithSelected(self, event):
        """
        Replace current tray contents with incoming version.  No tray state is
        preserved, except for filter settings if any.
        """
        try:
            data = json.loads(event.contents())[0]
            self.load_tray_with_something_new(data)
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

    def compare_with_current(self, event):
        event.reject()

        vd      = json.loads(event.contents())[0]
        source1 = self.current_source()
        source2 = self.source_group_from_version_data(vd)
        sources = [source1, source2]

        self.compare_sources(sources)
            
    def compare_selected(self, event):
        event.reject()

        vd      = json.loads(event.contents())
        sources = map(lambda x: self.source_group_from_version_data(x), vd)

        self.compare_sources(sources)
            
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
        self.set_details_dirty()

    def viewChange(self, event):
        # print "################### viewChange %r" % event
        # print "contents %r" % event.contents()
        event.reject()
        self.configure_visibility()
        self.set_details_dirty()

    def frameChanged(self, event):
        if event:
            event.reject()
        try:
            idx = self.clip_index_from_frame()
            mini_data = MiniCutData.load_from_session()

            if mini_data and mini_data.active:
                idx = idx + mini_data.first_clip

            self.set_details_dirty()

            if not self.tray_dock.isVisible():
                return

            sel_index = self.tray_model.index(idx, 0)
            sels = self.tray_list.selectionModel().selectedIndexes()

            if sel_index not in sels:
                sm = self.tray_list.selectionModel()           
                sm.select(sel_index, sm.ClearAndSelect)
                self.tray_list.scrollTo(sel_index, QtGui.QAbstractItemView.PositionAtCenter)            
                
        except Exception as e:
            print "ERROR: RV frameChanged EXCEPTION %r" % e

    def sourcePath(self, event):
        event.reject()
        # print "################### sourcePath %r" % event
        # print event.contents()

    def graphStateChange(self, event):
        event.reject()
        self.set_details_dirty()

    def sourceGroupComplete(self, event):
        event.reject()

        """
        args         = event.contents().split(";;")
        # this source group was just created.
        if args[1] == "new":
            return
        else:
            print "################### sourceGroupComplete %r" % event
            print args[1]
            print event.contents()
        """

    def on_play_state_change(self, event):

        # Auto-pin the DetailsPanel during playback, so that updating it does
        # not cause a hiccup.

        # Ignore the event if no DetailsPanel built yet, or if we are
        # "buffering" (ie playback paused to fill cache) or in "turn-around"
        # (ie looping)
        cont = event.contents()
        if self.details_panel and cont != "buffering" and cont != "turn-around":
            # We only auto-pin the details if they are not already pinned
            if   (  event.name() == "play-start" and 
                    not self.details_panel.is_pinned and
                    self._prefs.pin_details):
                self.details_panel.set_pinned(True)
                self.details_pinned_for_playback = True

                # if the Cuts button is conditionally enabled (because we're
                # looking at something other than a cut), then disable during
                # playback.
                if self.target_entity['type'] != "Cut":
                    self.enable_cuts_action(False, 'Stop to enable.')

            # We only auto-unpin the details on stop if we auto-pinned them in
            # the first place.
            elif event.name() == "play-stop":
                if self.details_pinned_for_playback:
                    self.details_panel.set_pinned(False)
                    self.details_pinned_for_playback = False

                # if the Cuts button is conditionally enabled (because we're
                # looking at something other than a cut), this is were we check
                # to see if this clip has a default cut and update the button
                # state accordingly.
                if self.target_entity['type'] != "Cut":
                    self.update_cuts_with()

                self._popup_utils.request_related_cuts_from_models()

    def update_cuts_with(self):
        cuts = self.get_cuts_with()
        if cuts == {}:
            # we've done this before, disable the clapper
            self.enable_cuts_action(False, 'No cut for this version')
            return
        if cuts != None:
            # we have a cut, enable the clapper
            self.enable_cuts_action(True, 'Review this version in the latest cut')
            return

        version_data = self.version_data_from_source()
        if version_data:
            if 'latest_cut_entity' in version_data:
                if version_data['latest_cut_entity']:
                    self.enable_cuts_action(True, 'Review this version in the latest cut')
                else:
                    self.enable_cuts_action(False, 'No cut for this version')
            else:
                # we need the shot and the project
                shot_entity = None
                if version_data.get("entity") and version_data.get("entity").get("type") == "Shot":
                    shot_entity = version_data.get("entity")
                
                project_entity = version_data.get("project")
                
                latest_cut_entity = self.find_latest_cut_for_version(shot_entity, version_data, project_entity)
                
                self.set_cuts_with(latest_cut_entity)

                if latest_cut_entity:
                    self.enable_cuts_action(True, 'Review this version in the latest cut')
                else:
                    self.enable_cuts_action(False, 'No cut for this version')

    def get_cuts_with(self):
        group_name = self.current_source()
        if group_name:      
            cut_str = getStringProp(group_name + ".sg_review.latest_cut_entity", None)
            if cut_str:
                try:
                    return json.loads(cut_str)
                except Exception as e:
                    self._app.engine.log_error("get_cuts_with: %r" % e)
        return None
        
    def set_cuts_with(self, cut_entity):
        if not cut_entity:
            cut_entity = {}
        group_name = self.current_source()       
        setProp(group_name + ".sg_review.latest_cut_entity", json.dumps(cut_entity))
    

    def on_view_size_changed(self, event):
        event.reject()
        traysize = self.tray_dock.size().width()
        self.tray_main_frame.resize(traysize - 10, self._tray_height)

    def version_submitted(self, event):
        event.reject()
        self.note_dock.show()
        # contents are standard json version payload, so others could hook up
        # to it.

    def per_render_event(self, event):
        event.reject()
        if self._queued_frame_change != -1:
            rvc.setFrame(self._queued_frame_change)
            self._queued_frame_change = -1

    def set_preferred_compare_mode_factory(self, mode_name):

        def set_func(event):
            self._prefs.preferred_compare_mode = mode_name
            self._prefs.save()

        return set_func

    def preferred_compare_mode_state_factory(self, mode_name):

        def state_func():
            return rvc.CheckedMenuState if self._prefs.preferred_compare_mode == mode_name else rvc.UncheckedMenuState

        return state_func

    def set_default_media_type_movie(self, event):
        self._prefs.preferred_media_type = "Movie"
        self._prefs.save()

    def set_default_media_type_frames(self, event):
        self._prefs.preferred_media_type = "Frames"
        self._prefs.save()

    # def set_default_status_menu(self):
    #     # j = json.dumps(self._popup_utils.get_status())
    #     # self._prefs.status_filter = j

    #     self._prefs.save()

    # def set_default_pipeline_menu(self):
    #     # p = self._popup_utils.get_pipeline()
    #     # if p == None:
    #     #     # need to store a string...
    #     #     p = "None"
    #     # j = json.dumps( p )
    #     # self._prefs.pipeline_filter = j
    #     self._prefs.save()

    def default_media_type_state_movie(self):
        return rvc.CheckedMenuState if self._prefs.preferred_media_type == "Movie" else rvc.UncheckedMenuState

    def default_media_type_state_frames(self):
        return rvc.CheckedMenuState if self._prefs.preferred_media_type == "Frames" else rvc.UncheckedMenuState

    def toggle_startup_view_details(self, event):
        self._prefs.startup_view_details = not self._prefs.startup_view_details
        self._prefs.save()

    def toggle_startup_view_tray(self, event):
        self._prefs.startup_view_tray = not self._prefs.startup_view_tray
        self._prefs.save()

    def startup_view_details_state(self):
        return rvc.CheckedMenuState if self._prefs.startup_view_details else rvc.UncheckedMenuState

    def startup_view_tray_state(self):
        return rvc.CheckedMenuState if self._prefs.startup_view_tray else rvc.UncheckedMenuState

    def toggle_auto_show_details(self, event):
        self._prefs.auto_show_details = not self._prefs.auto_show_details
        self._prefs.save()

    def toggle_auto_show_tray(self, event):
        self._prefs.auto_show_tray = not self._prefs.auto_show_tray
        self._prefs.save()

    def auto_show_tray_state(self):
        return rvc.CheckedMenuState if self._prefs.auto_show_tray else rvc.UncheckedMenuState

    def auto_show_details_state(self):
        return rvc.CheckedMenuState if self._prefs.auto_show_details else rvc.UncheckedMenuState

    def toggle_pin_details(self, event):
        self._prefs.pin_details = not self._prefs.pin_details
        self._prefs.save()

    def pin_details_state(self):
        return rvc.CheckedMenuState if self._prefs.pin_details else rvc.UncheckedMenuState

    def toggle_auto_play(self, event):
        self._prefs.auto_play = not self._prefs.auto_play
        self._prefs.save()

    def auto_play_state(self):
        return rvc.CheckedMenuState if self._prefs.auto_play else rvc.UncheckedMenuState

    def toggle_view_details(self, event):
        if not self.note_dock:
            return

        vis = not self.note_dock.isVisible()
        self.note_dock.setVisible(vis)
        if not vis:
            self.details_hidden_this_session = True

    def toggle_view_tray(self, event):
        if not self.tray_dock:
            return

        vis = not self.tray_dock.isVisible()
        self.tray_dock.setVisible(vis)
        if not vis:
            self.tray_hidden_this_session = True

    def view_state_details(self):
        return rvc.CheckedMenuState if (self.note_dock and self.note_dock.isVisible()) else rvc.UncheckedMenuState

    def view_state_tray(self):
        return rvc.CheckedMenuState if (self.tray_dock and self.tray_dock.isVisible()) else rvc.UncheckedMenuState

    def launchSubmitTool(self, event):
        if self.tray_dock:
            self.tray_dock.hide()
            
        self.tray_hidden_this_session = True
            
        # Flag the session as "sgreview.submitInProgress" so JS submit tool
        # code can tell this is not Screening Room.
        #
        setProp("#Session.sgreview.submitInProgress", 1)

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

    def get_unstored_frame_props(self, grpFilter=None):
        '''
        Collect a dictionary of frame : property list pairs.
        The properties are for unsaved annotation on the key frame.
        An optional filter string can be passed to restrict the search to strokes on one source
        '''
        # Build up a dictionary of frames : unsaved annotations
        unstoredFrames = {}
        frames = rve.findAnnotatedFrames()
        pnodes = rvc.nodesOfType("RVPaint")
        for pnode in pnodes:

            # If there is a filter make sure this paint node matches
            if grpFilter != None and grpFilter not in pnode:
                continue

            # For each paint node check the list of annotated frames for commands
            for frame in frames:
                sframe = rve.sourceFrame(frame)
                orderProp = pnode + '.frame:%d.order' % sframe
                if rvc.propertyExists(orderProp):
                    pcmds = rvc.getStringProperty(orderProp)
                    for pcmd in pcmds:
                        savedProp = pnode + '.%s.sgtk_stored' % pcmd
                        if rvc.propertyExists(savedProp):
                            continue

                        # If a command is found and it isn't sgtk_stored than add it to our list.
                        # Creating the properties this way allows us to easily set them later
                        # effectively marking the command as stored.
                        unstoredFrames.setdefault(frame, []).append(savedProp)
        return unstoredFrames

    def get_unstored_frames(self):
        '''
        Get the frame numbers for the frames with unsaved (not yet submitted) annotation strokes
        '''
        # The keys are the frames with unsaved annotation
        return self.get_unstored_frame_props().keys()

    def make_note_attachments(self, note_entity):
        '''
        Find the annotated frames for the given version, export them through RVIO, then submit them
        '''
        # Look for unsaved annotation
        version_entity = self.details_panel.current_entity

        if not version_entity:
            return

        props = {}

        try:
            group = self.find_group_from_version_id(version_entity["id"])
            props = self.get_unstored_frame_props(group)
        except Exception as exc:
            self._app.log_error("Unable to locate annotation strokes: " + str(exc))

        if len(props) <= 0:
            self._app.log_debug("Found no new annotations to attach")
            return

        # Start RVIO command construction
        tempdir = tempfile.mkdtemp()
        rvc.rvioSetup() # NOTE: Pass the license to the env
        rvio = os.environ.get("RV_APP_RVIO", None)
        args = [rvio, "-v", "-err-to-out"]

        # Make the temp session
        setDisp = pymu.MuSymbol("export_utils.setExportDisplayConvert")
        setDisp("default")
        session = os.path.join(tempdir, "export.rv")
        rvc.saveSession(session)
        args += [session]

        # Start with a generic output file sequence string
        tempfiles = os.path.join(tempdir,"sequence.@.jpg")
        args += ["-o", tempfiles]

        # Use the keys from the unsaved annotation search for frames
        frames = [ str(f) for f in props.keys() ]
        framesStr = ','.join(frames)
        args += ["-t", framesStr]

        # If a specific license was set use it instead
        lic = os.environ.get("RV_APP_USE_LICENSE_FILE", None)
        if lic != None:
            args += ["-lic", lic]
        
        # Tell the user what is going on
        displayString = "Rendering " + str(len(frames))
        if len(frames) > 1:
            displayString += " annotated frames..."
        else:
            displayString += " annotated frame..."
        rve.displayFeedback2(displayString, 3600.0)

        # Run the RVIO conversion
        try:
            out = subprocess.check_output(args)
        except subprocess.CalledProcessError as exc:
            self._app.log_error("Unable to export annotation: " + str(exc))
        
        # Close out the banner
        rve.displayFeedback2(displayString, 2.0)

        # Rename the annotation frame before submitting
        attachments = []
        saved = []
        for frame in props.keys():
            src = "%s/sequence.%d.jpg" % (tempdir,frame)

            if not (os.path.isfile(src)):
                self._app.log_error("Can't find annotation for frame: %d at '%s'" % (frame, src))
                continue

            sframe = rve.sourceFrame(frame)
            tgt = "%s/annot_version_%d_v2.%d.jpg" % (tempdir, version_entity['id'], sframe)

            shutil.move(src, tgt)
            attachments.append(tgt)
            saved.append(frame)

        # Delete the session file
        os.remove(session)

        # Submit the frames
        self.submit_note_attachments(attachments, note_entity)

        # Update the graph to reflect which strokes have been submitted
        for frame in saved:
            for prop in props[frame]:
                rvc.newProperty(prop, rvc.IntType, 1)
                rvc.setIntProperty(prop, [1234], True) # XXX should be note id

    def set_media_type_property(self, source_group, media_type):
        setProp(source_group + ".sg_review.media_type", media_type)

    def get_media_type_of_source(self, source_group):
        return getStringProp(source_group + ".sg_review.media_type", None)

    def configure_source_media(self, source_group, version_data=None):
        # XXX more to do here (stereo, fps, ...)

        if not version_data:
            version_data = self.version_data_from_source(source_group)

        media_type = self.get_media_type_of_source(source_group)
        file_source = groupMemberOfType(source_group, "RVFileSource")

        # Set up correct source frame mapping

        range_start_prop = file_source + ".group.rangeStart"
        first_frame = version_data["sg_first_frame"]
        has_slate = version_data[standard_media_types[media_type].slate_field]

        if first_frame is not None:
            # If this is not a Movie assume the default frame mapping works (as
            # it should for Frames)
            if   media_type != "Movie" and rvc.propertyExists(range_start_prop):
                rvc.deleteProperty(range_start_prop)

            # If it _is_ a movie, compensate for lack of timecode or wrong
            # timecode.
            elif media_type == "Movie" and has_slate is not None:
                setProp(range_start_prop, first_frame - int(has_slate))

    def set_media_of_source(self, source_group, media_type_name, version_data=None):
        """
        Given the name of an RVSourceGroup node, set the media held by that node to
        be of the given "media type". (IE at the moment "Movie" or "Frames").
        Set the "sg_review.media_type" property of the source to
        match the current media type.
        """
        self._app.engine.log_debug("set_media_of_source '%s' to '%s'" % 
            (source_group, media_type_name))

        current_media_type = self.get_media_type_of_source(source_group)

        if not version_data:
            version_data = self.version_data_from_source(source_group)

        m_type = self.media_type_fallback(version_data, media_type_name)
        # XXX warn if falling back

        if m_type and m_type != current_media_type: 
            path = version_data[standard_media_types[m_type].path_field]
            path = self.swap_in_home_dir(path)
            file_source = groupMemberOfType(source_group, "RVFileSource")
            rvc.setSourceMedia(file_source, [path], "shotgun")
            self.set_media_type_property(source_group, m_type)
            self.configure_source_media(source_group, version_data)

        #self._app.engine.log_warning("Version '%s' has no local media" % version_data["code"])


    def swap_media_of_source(self, source_node, media_type_name):
        """
        Given the name of an RVSourceGroup node, swap the media held by that node to
        be of the given "media type".  Silently ignore sources with no Shotgun
        data and nodes that already hold the right type of media.
        """
        if not source_node:
            return

        self._app.engine.log_debug("swap_media_of_source '%s' to '%s'" % 
            (source_node, media_type_name))

        old_media_type = self.get_media_type_of_source(source_node)

        if old_media_type and (old_media_type != media_type_name):
            self.set_media_of_source(source_node, media_type_name)

    def swap_media_factory(self, media_type_name, one_or_all):

        def swap_media(event):

            if one_or_all == "one":
                sources = [ self.current_source() ]
            else:
                # Collect all RVSourceGroup nodes that could be input to the
                # current view node.  In the common case, this will be all the
                # Versions that appear in the current RVSequence.
                view = rvc.viewNode()
                if rvc.nodeType(view) == "RVSourceGroup":
                    sources = [ view ]
                else:
                    # XXX Since the view is not an RVSourceGroup, assuming the
                    # _inputs_ of the view are ...
                    inputs = rvc.nodeConnections(view, False)[0]
                    sources = filter(lambda x: rvc.nodeType(x) == "RVSourceGroup", inputs)

                    # remove duplicates
                    sources = sorted(set(sources))

            for source in sources:
                self.swap_media_of_source(source, media_type_name)

        return swap_media

    def __init__(self, app):
        rvt.MinorMode.__init__(self)
        
        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138
        self._ORIGINAL_THUMBNAIL = QtCore.Qt.UserRole + 1702
        self._FILTER_THUMBNAIL = QtCore.Qt.UserRole + 1703
        self._PINNED_THUMBNAIL = QtCore.Qt.UserRole + 1704

        self._bundle = sgtk.platform.current_bundle()
        
        self.cuts_action = None
        self.note_dock = None
        self.tray_dock = None
        self.detail_version_id = None

        self.cached_mini_cut_data = MiniCutData(False)

        self._tray_height = 96
        self.target_entity = None
        self.playback_queued = False
        
        # keep track of where we just were to enable 'cuts off' mode
        self.last_target_entity = None

        self.main_query_active = False
        self.details_panel_last_loaded = None

        self.no_media_check = (os.getenv("RV_TK_NO_MEDIA_CHECK",None) is not None)

        self.details_panel = None
        self.details_pinned_for_playback = False
        self.details_dirty = False

        # RV specific
        # the current sequence node
        self.cut_seq_node = None
        self.cut_seq_name = None
        self._layout_node = None
        self.mod_seq_node = None
        self.want_stacked = False

        self.project_entity = None

        # related cuts menu
        self.related_cuts_entity = None
        self.related_cuts = None

        # filter menus
        self.pipeline_steps = None
        self.status_list = None

        # models for ad-hoc queries
        self._shot_model = shotgun_model.SimpleShotgunModel(rvqt.sessionWindow())
        self._cuts_model = shotgun_model.SimpleShotgunModel(rvqt.sessionWindow())

        self._app = app
        self._queued_frame_change = -1

        self._prefs = Preferences()
        self.incoming_pinned = {}
        self.incoming_mini_cut_focus = None


        self.init("RvActivityMode", None,
                [ 
                ("after-session-read", self.afterSessionRead, ""),
                ("before-session-read", self.beforeSessionRead, ""),
                # ("source-group-complete", self.sourceSetup, ""),
                ("after-graph-view-change", self.viewChange, ""),
                ("frame-changed", self.frameChanged, ""),
                ("graph-node-inputs-changed", self.inputsChanged, ""),
                ("compare_with_current", self.compare_with_current, ""),
                ("compare_selected", self.compare_selected, ""),
                ("swap_into_sequence", self.swapIntoSequence, ""),
                ("source-group-complete", self.sourceGroupComplete, ""),
                ("replace_with_selected", self.replaceWithSelected, ""),
                ("graph-state-change", self.graphStateChange, ""),
                ('id_from_gma', self.on_id_from_gma, ""),
                ('compare_ids_from_gma', self.on_compare_ids_from_gma, ""),
                ('play-start', self.on_play_state_change, ""),
                ('play-stop', self.on_play_state_change, ""),
                ('view-size-changed', self.on_view_size_changed, ''),
                ('per-render-event-processing', self.per_render_event, ''),
                ('submit-tool-submission-complete', self.version_submitted, ''),
                ],
                [("SG Review", [
                    ("Swap Media - Current Clip", None, None, lambda: rvc.DisabledMenuState),
                    ("    Movie",  self.swap_media_factory("Movie", "one"),  None, lambda: rvc.UncheckedMenuState),
                    ("    Frames", self.swap_media_factory("Frames", "one"), None, lambda: rvc.UncheckedMenuState),

                    ("Swap Media - All Clips", None, None, lambda: rvc.DisabledMenuState),
                    ("    Movie",  self.swap_media_factory("Movie", "all"),  None, lambda: rvc.UncheckedMenuState),
                    ("    Frames", self.swap_media_factory("Frames", "all"), None, lambda: rvc.UncheckedMenuState),

                    ("_", None),
                    ("View", None, None, lambda: rvc.DisabledMenuState),
                    ("    Details Pane",       self.toggle_view_details, None, self.view_state_details),
                    ("    Thumbnail Timeline", self.toggle_view_tray,    None, self.view_state_tray),

                    ("_", None),
                    ("Submit Tool", self.launchSubmitTool, None, lambda: rvc.UncheckedMenuState),

                    ("_", None),
                    ("Preferences", [
                        ("Default Media Type", None, None, lambda: rvc.DisabledMenuState),
                        ("    Movie",  self.set_default_media_type_movie,  None, self.default_media_type_state_movie),
                        ("    Frames", self.set_default_media_type_frames, None, self.default_media_type_state_frames),

                        ("Default Compare Mode", None, None, lambda: rvc.DisabledMenuState),
                        ("    Grid",             self.set_preferred_compare_mode_factory("Grid"),  None, self.preferred_compare_mode_state_factory("Grid")),
                        ("    Stack",            self.set_preferred_compare_mode_factory("Stack"), None, self.preferred_compare_mode_state_factory("Stack")),
                        ("    Stack with Wipes", self.set_preferred_compare_mode_factory("Wipe"),  None, self.preferred_compare_mode_state_factory("Wipe")),

                        ("Show On Startup", None, None, lambda: rvc.DisabledMenuState),
                        ("    Details Pane",       self.toggle_startup_view_details, None, self.startup_view_details_state),
                        ("    Thumbnail Timeline", self.toggle_startup_view_tray,    None, self.startup_view_tray_state),

                        ("Auto-Show", None, None, lambda: rvc.DisabledMenuState),
                        ("    Details Pane",       self.toggle_auto_show_details, None, self.auto_show_details_state),
                        ("    Thumbnail Timeline", self.toggle_auto_show_tray,    None, self.auto_show_tray_state),

                        ("_", None),
                        ("Pin Details Pane During Playback", self.toggle_pin_details, None, self.pin_details_state),
                        ("Auto-Play After Each Load",        self.toggle_auto_play,   None, self.auto_play_state),

                        ]),
                    ("_", None)]
                )],
                None)
       
    def activate(self):
        rvt.MinorMode.activate(self)

    def deactivate(self):
        self.details_panel.save_preferences()
        rvt.MinorMode.deactivate(self)
              

    ################################################################################### qt stuff down here. 

    def show_cuts_action(self, show=True):
        '''
        Adds a cuts clapper button to the far left of the RV toolbar.
        If show is false an attempt to remove any exisitng button is made.
        '''
        btb = rv.qtutils.sessionBottomToolBar()
        
        actions = btb.actions()
 
        text = 'No cut for this version'
 
        if show:
            cicon = QtGui.QIcon(":/tk-rv-shotgunreview/icon_player_cut_action_small_dark.png")
            self.cuts_action = QtGui.QAction(cicon, text, btb)
            self.cuts_action.triggered.connect(self.cuts_button_pushed)
            btb.insertAction(actions[0],self.cuts_action)
            self.cuts_action.setEnabled(False)
        else:
            if (actions[0].text() == text):
                btb.removeAction(actions[0])

    def enable_cuts_action(self, enable=True, tooltip=None, enable_blue=False):
        '''
        Enables cuts toolbar button; when enabled it may be blue. If enable is
        false the button is disabled (and not blue).
        '''
        if (enable and enable_blue):
            cicon = QtGui.QIcon(":/tk-rv-shotgunreview/icon_player_cut_action_small_active.png")
            self.cuts_action.setIcon(cicon)
        else:
            cicon = QtGui.QIcon(":/tk-rv-shotgunreview/icon_player_cut_action_small_dark.png")
            self.cuts_action.setIcon(cicon)
        self.cuts_action.setEnabled(enable)
        self.cuts_action.setToolTip(tooltip)

    def cuts_button_pushed(self):
        '''
        cuts toolbar button listener
        '''
        if self.target_entity and self.target_entity['type'] == "Cut":
            if self.last_target_entity:
                # we're loading a non-cut, so no mini-cut state, pinned state, etc.
                self.load_tray_with_something_new(self.last_target_entity)
            else:
                # load the version we are on
                version_data = self.version_data_from_source()
                if version_data:
                    self.load_tray_with_something_new({"id":version_data["id"], "type":"Version"})

            self._app.engine.log_info('Clapper disabled for Cut entities. Back to last non-cut target_entity.')
            return

        # data is waiting for us:
        cut = self.get_cuts_with()
        if not cut:
            return

        version_data = self.version_data_from_source()
        if version_data:
            shot_id = self.shot_id_str_from_version_data(version_data)
            pinned = { shot_id:version_data } if shot_id else {}          

            self.load_tray_with_something_new(cut,
                    incoming_pinned=pinned, 
                    incoming_mini_focus=version_data)

            self.tray_list.repaint()

    def submit_note_attachments(self, attachments, note_entity):
        """
        Send the created and collected annotation exports off for saving.

        :param attachments: A list of file paths to attach.
        :param note_entity: A Note entity in the form of a dictionary as returned
                            by the Shotgun Python API.
        """
        self.details_panel.add_note_attachments(attachments, note_entity)

    def load_data(self, entity):
        try:
            # self._app.engine.log_info( "loading details panel with %r" % entity )
            if self.details_panel_last_loaded != entity:
                self._app.engine.log_info( "load_data with %r" % entity )
                self.details_panel.load_data(entity)
                self.details_panel_last_loaded = entity
        except Exception as e:
            self._app.engine.log_error("DETAILS PANEL: sent %r got %r" % (entity, e))

        # saw False even if we fail? endless loop? delay?
        self.details_dirty = False
 
    def init_ui(self, note_dock, tray_dock, version_id):
        self.note_dock = note_dock
        self.tray_dock = tray_dock

        self.related_cuts_menu = None
        self.pipeline_steps_menu = None
        # self.status_menu = None
        
        # Add a cuts button to the bottom toolbar
        self.show_cuts_action(True)

        # Setup the details panel.
        self.details_panel = DetailsPanelWidget(
            parent=self.note_dock,
            bg_task_manager=self._app.engine.bg_task_manager,
        )
        self.note_dock.setWidget(self.details_panel)
        
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

        self.tray_dock.setMinimumSize(QtCore.QSize(720,self._tray_height + 60))
        
        # ug, for now till i can clean up the methods
        from .tray_main_frame import TrayMainFrame
        self.tray_main_frame = TrayMainFrame(self.tray_dock, self)
        #self.tray_main_frame.set_rv_mode(self)

        self.tray_hidden_this_session = False
        self.details_hidden_this_session = False

        # popup utils will try to handle all popup menu related things...
        self._popup_utils = PopupUtils(self)
        # self._popup_utils.set_status(self._prefs.status_filter)
        self._popup_utils.mark_pipeline_selections()

        
        # just map these back for the moment...
        self.tray_model = self.tray_main_frame.tray_model
        self.tray_proxyModel = self.tray_main_frame.tray_proxyModel
        self.tray_delegate = self.tray_main_frame.tray_delegate
        self.tray_list = self.tray_main_frame.tray_list
        self.tray_button_entire_cut = self.tray_main_frame.tray_button_entire_cut
        self.tray_button_mini_cut = self.tray_main_frame.tray_button_mini_cut
        self.tray_button_browse_cut = self.tray_main_frame.tray_button_browse_cut
        self.tray_bar_button = self.tray_main_frame.tray_bar_button
        self.tray_left_spinner = self.tray_main_frame.mini_left_spinner
        self.tray_right_spinner = self.tray_main_frame.mini_right_spinner
        self.tray_left_label = self.tray_main_frame.tray_left_label
        self.tray_right_label = self.tray_main_frame.tray_right_label

        # init spinner values
        self.tray_left_spinner.setValue (self._prefs.mini_left_count)
        self.tray_right_spinner.setValue(self._prefs.mini_right_count)

        # CONNECTIONS
        self.tray_model.data_refreshed.connect(self.on_data_refreshed)
        self.tray_model.cache_loaded.connect(self.on_cache_loaded)
        self.tray_list.clicked.connect(self.tray_clicked)        
        self.tray_list.doubleClicked.connect(self.tray_double_clicked)

        self.tray_main_frame.mini_right_spinner.valueChanged.connect(self.right_spinner_clicked)
        self.tray_main_frame.mini_left_spinner.valueChanged.connect(self.left_spinner_clicked)

        self.tray_button_entire_cut.clicked.connect(self.on_entire_cut)
        self.tray_button_mini_cut.clicked.connect(self.on_mini_cut)
        
        self.tray_model.filter_data_refreshed.connect(self.on_filter_refreshed)

        self.details_panel.entity_created.connect(self.make_note_attachments)
        
        # self._popup_utils.related_cuts_ready.connect(self.create_related_cuts_from_models)

        # async cached request for pipeline steps.
        # XXX pipeline steps are 'global' to shotgun? so this only needs to happen once?
        self._popup_utils.get_pipeline_steps_with_model()

        self.details_timer = QTimer(rvqt.sessionWindow())
        self.note_dock.connect(self.details_timer, SIGNAL("timeout()"), self.check_details)
        self.details_timer.setSingleShot(True)
        self.details_timer.setInterval(100)

        self.last_rel_cut_entity = None
        self.last_rel_shot_entity = None
        self.last_related_cuts = None

        self.tray_dock.setVisible(self._prefs.startup_view_tray)
        self.note_dock.setVisible(self._prefs.startup_view_details)

        # setting to NoContextMenu DOESNT WORK!!!
        # so add a no-op
        self.tray_dock.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tray_dock.customContextMenuRequested.connect( self.dont_show_tray_context_menu)
 
    def dont_show_tray_context_menu(self):
        pass

    def on_filter_refreshed(self, really_changed):
        self._app.engine.log_debug("on_filter_refreshed: really_changed is %r" % really_changed)
        if really_changed:
            # XXX this will rely on self.target_entity still being set
            # correctly _and_ on us still looking at the corresponding node.
            # maybe we should be constructing a target_entity here from
            # whatever node we are looking at now ?   And not do anything if
            # it's not a Cut node, etc ...
            self.on_data_refreshed_internal(True, incremental_update=True)

    def right_spinner_clicked(self, event):
        self.on_mini_cut()

    def left_spinner_clicked(self, event):
        self.on_mini_cut()

    def on_compare_ids_from_gma(self, event):
        self._app.engine.log_info("on_compare_ids_from_gma  %r %r" % (event.contents(), QtCore.QThread.currentThread() ) )
        self.compare_active = True
        target_entity = json.loads(event.contents())

        # XXX should check here that incoming server matches server to
        # which we are currently authenticated
        #
        target_entity["server"] = self._app.tank.shotgun_url

        vfilters = [["id", "in", target_entity["ids"]]]
        vfields =  [ "image" ] + required_version_fields
        self.tray_model.load_data(entity_type="Version", filters=vfilters, fields=vfields)

    def on_id_from_gma(self, event):
        self._app.engine.log_info("on_id_from_gma  %r %r" % (event.contents(), QtCore.QThread.currentThread() ) )
        self.compare_active = False
        target_entity = json.loads(event.contents())

        # XXX should check here that incoming server matches server to
        # which we are currently authenticated
        target_entity["server"] = self._app.tank.shotgun_url

        self.load_tray_with_something_new(target_entity, load_from_gma=True)

        """
        except Exception as e:
            print "ERROR: on_id_from_gma %r" % e
            """

    def set_details_dirty(self):
        self.details_dirty = True
        self.details_timer.start()

    def refresh_tray_thumbnails(self):
        rows = self.tray_proxyModel.rowCount()
        for index in range(0, rows):
            item = self.tray_proxyModel.index(index, 0)
            
            orig = item.data(self._ORIGINAL_THUMBNAIL)
            pinned = item.data(self._PINNED_THUMBNAIL)
            filtered = item.data(self._FILTER_THUMBNAIL)

            thumb = None
            if pinned:
                thumb = QtGui.QIcon(pinned)
            if not pinned and filtered:
                thumb = QtGui.QIcon(filtered)
            if not pinned and not filtered:
                thumb = QtGui.QIcon(orig)
            if thumb:
                self.tray_proxyModel.setData(item, thumb, QtCore.Qt.DecorationRole)

        self.tray_list.repaint()


    def update_pinned_thumbnail(self, v_data):
        # version_data['__image_path'] holds the local cache path thumbnail for the pinned icon
        # version_data['entity'] has our shot.
        # drop this path into every item that has this shot
        if '__image_path' not in v_data:
            self._app.engine.log_warning('no image path passed into update_pinned_thumbnail.')
            return

        path = v_data['__image_path']
        rows = self.tray_proxyModel.rowCount()
        for index in range(0, rows):
            item = self.tray_proxyModel.index(index, 0)
            sg = shotgun_model.get_sg_data(item)
 
            # sometimes the shot comes back as None XXX - sb
            if 'shot' in sg and sg['shot']:
                if sg['shot']['id'] == v_data['entity']['id']:
                    self.tray_proxyModel.setData(item, path, self._PINNED_THUMBNAIL)
             
        self.refresh_tray_thumbnails()


    def replace_version_in_sequence(self, versions):
        #XXX go over this in mini-cut case, etc
        self._app.engine.log_info('replace_version_in_sequence %r' % QtCore.QThread.currentThread() )

        if len(versions) != 1:
            self._app.engine.log_error(
                "replace_version_in_sequence received %d versions!" % len(versions))
            return

        version_data = versions[0]
        seq_group = rvc.viewNode()
        
        try:
            self.update_pinned_thumbnail(version_data)    
        except Exception as e:
            self._app.engine.log_error("update_pinned_thumbnail: %r" % e)

        if rvc.nodeType(seq_group) != "RVSequenceGroup":
            return

        seq_node      = groupMemberOfType(seq_group, "RVSequence")
        inputs        = rvc.nodeConnections(seq_group, False)[0]
        input_indices = getIntProp(seq_node + ".edl.source", [])
        
        # make or find source group
        src_group = self.source_group_from_version_data(version_data)

        # Version/source of current clip is destination for this version, so
        # first find index of current clip 
        clip_index = self.clip_index_from_frame()

        # replace input corresponding to input at clip index with new source
        inputs[input_indices[clip_index]] = src_group

        # update shadow sequence (offset with mini cut data)

        mini_data = MiniCutData.load_from_session(seq_node)
        if mini_data.active:
            clip_index += mini_data.first_clip

        shadow_source = getIntProp(seq_node + ".shadow_edl.source", [])
        shadow_inputs = getStringProp(seq_node + ".shadow_edl.inputs", [])
        shadow_inputs[shadow_source[clip_index]] = src_group
        setProp(seq_node + ".shadow_edl.inputs", shadow_inputs)

        # reset inputs
        rvc.setNodeInputs(seq_group, inputs)

        # update pinned data for this sequence.  this version will be pinned
        # into any clip that uses this shot.
        self.update_pinned_in_sequence(seq_group, version_data)

        # Details need to be updated
        self.set_details_dirty()

        # XXX how does below pick up new thumbnail ?   Ans: it doesn't yet ..
        self.tray_list.repaint()

    def find_or_create_compare_node(self, num_sources):
        
        mode = self._prefs.preferred_compare_mode

        if   mode == "Grid":
            ui_name = "Grid of %d Versions"  % num_sources
            group_type = "RVLayoutGroup"

        elif mode == "Stack": 
            ui_name = "Stack of %d Versions" % num_sources
            group_type = "RVStackGroup"

        elif mode == "Wipe":
            ui_name = "Wipe of %d Versions"  % num_sources
            group_type = "RVStackGroup"

        for n in rvc.nodesOfType(group_type):
            if bool(getIntProp(n + ".sg_review.compare_node", int(False))):
                rve.setUIName(n, ui_name)
                return n

        # could not find compare node, so make one
        group = rvc.newNode(group_type)

        rve.setUIName(group, ui_name)
        setProp(group + ".sg_review.compare_node", int(True))

        # some config for particular compare modes
        if   mode == "Grid":
            setProp(group + ".layout.mode", "grid")
        elif mode == "Wipe":
            setProp(group + ".ui.wipes", 1)

        return group
        
    def compare_sources (self, sources):

        compNode = self.find_or_create_compare_node(len(sources))

        rvc.setNodeInputs(compNode, sources)
        rvc.setViewNode(compNode)

    def version_data_from_mini_focus_clip(self):
        """
        Assuming current view node is an RVSequenceGroup representing a Cut,
        and it's in mini-cut mode, find the Version and held by the focus
        clip/cut-item and return the corresponding version_data.
        """
        seq_node = None
        seq_group = rvc.viewNode()

        if getStringProp(seq_group + ".sg_review.target_type", None) != "Cut":
            return None
        
        if rvc.nodeType(seq_group) == "RVSequenceGroup":
            seq_node = groupMemberOfType(seq_group, "RVSequence")

        if seq_node is None:
            return None

        # load current mini-cut state for this sequence node
        mini_data = MiniCutData.load_from_session(seq_node)

        if not mini_data.active:
            return None

        mini_index = mini_data.focus_clip - mini_data.first_clip
        edl_source = getIntProp(seq_node + ".edl.source", [])
        inputs     = rvc.nodeConnections(seq_group, False)[0]

        source_group = inputs[edl_source[mini_index]]

        return self.version_data_from_source(source_group)

    def load_tray_with_something_new(self, target_entity, 
            load_from_gma       = False, 
            preserve_pinned     = False, 
            preserve_mini       = False, 
            incoming_pinned     = {}, 
            incoming_mini_focus = None):

        self.incoming_pinned         = {}
        self.incoming_mini_cut_focus = None
        self.cached_mini_cut_data    = MiniCutData(False)

        # ok, this is the place we want to save the original thumbnail of the incoming pinned.
        self.tray_model.add_pinned_item(incoming_pinned)

        # grab whats pinned now
        self.tray_model.set_pinned_items(self.pinned_from_sequence())

        # notify user we're loading ...
        type_string = target_entity["type"]
        if "ids" in target_entity and len(target_entity["ids"]) > 1:
            type_string += "s"
        rve.displayFeedback("Loading " + type_string +  " ...", 60.0)
        self.main_query_active = True

        # XXX assume entire-cut at this point, ok ?
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')

        # XXX get rid of "id"
        if "id" in target_entity and "ids" not in target_entity:
            target_entity["ids"] = [ target_entity["id"] ]

        self.target_entity = target_entity

        t_type = target_entity["type"]

        if   t_type == "Version":
            self.last_target_entity = target_entity
            self.load_tray_with_version_ids(target_entity["ids"])
            self.tray_main_frame.show_steps_and_statuses(False)    
        elif t_type == "Playlist":
            self.last_target_entity = target_entity
            self.load_tray_with_playlist_id(target_entity["ids"][0])
            self.tray_main_frame.show_steps_and_statuses(False)
        elif t_type == "CutItem":
            cut = target_entity.get("cut")
            if cut:
                if load_from_gma:
                    self.last_target_entity = None
                self.target_entity = cut
                self.target_entity["ids"] = [cut["id"]]

                self.incoming_pinned         = {}
                self.incoming_mini_cut_focus = target_entity
                self.cached_mini_cut_data    = MiniCutData(False)

                self.load_tray_with_cut_id(cut["id"])
                self.tray_main_frame.show_steps_and_statuses(True)

        elif t_type == "Cut":
            if load_from_gma:
                self.last_target_entity = None

            # We only care about "pinned" shots/versions if we are loading a
            # Cut.  If caller asks that pinned state be preserved (we are
            # "switching cuts"), get current state for sequence and set in mode
            # for when query returns.  Otherwise caller may provide pinned data
            # explicitly (switching from Version to Cut or "turning on Cut
            # mode").
            if preserve_pinned:
                incoming_pinned = self.pinned_from_sequence()

            if preserve_mini:
                # get version of current focus clip and pass it on
                incoming_mini_focus = self.version_data_from_mini_focus_clip()
                
            self.incoming_pinned         = incoming_pinned
            self.incoming_mini_cut_focus = incoming_mini_focus
            self.cached_mini_cut_data    = MiniCutData(False)

            self.load_tray_with_cut_id(target_entity["ids"][0])
            self.tray_main_frame.show_steps_and_statuses(True)

        else:
            self._app.engine.log_error("Tray does not support entity type '%s'." % t_type)
            self.main_query_active = False
        
    def load_tray_with_version_ids(self, ids):
        vfilters = [["id", "in", ids]]
        vfields =  [ "playlists", "image" ] + required_version_fields
        self.tray_model.load_data(entity_type="Version", filters=vfilters, fields=vfields)

    def load_tray_with_playlist_id(self, playlist_id=None):
        plist_filters = [["playlists", "is", {"type": "Playlist", "id": playlist_id}]]
        plist_fields =  [ "playlists", "image", "playlists.PlaylistVersionConnection.sg_sort_order", 
                "playlists.PlaylistVersionConnection.id" ] + required_version_fields
        self.tray_model.load_data(entity_type="Version", filters=plist_filters, fields=plist_fields)

    def load_tray_with_cut_id(self, cut_id=None):
        self._app.engine.log_debug('load_tray_with_cut_id %r' % QtCore.QThread.currentThread() )

        # XXX we shouldn't be storing this here, come back to this
        if cut_id:
            self.tray_cut_id = cut_id
        
        # we need to know the project id to make the menus happen,

        tray_filters = [ ['cut','is', {'type':'Cut', 'id': self.tray_cut_id }] ]

        tray_fields= ["cut_item_in", "cut_item_out", "cut_order",
                "edit_in", "edit_out", "code", "entity", "shot", "project",
                "version.Version.image",
                "cut.Cut.code", "cut.Cut.id", "cut.Cut.version", "cut.Cut.fps", "cut.Cut.revision_number",
                "cut.Cut.cached_display_name", "cut.Cut.entity", "cut.Cut.image",
                "cut.Cut.version.Version.image"] 

        tray_fields += ["version.Version."         + f for f in required_version_fields]
        tray_fields += ["cut.Cut.version.Version." + f for f in required_version_fields]

        orders = [{'field_name':'cut_order','direction':'asc'}]
        self.tray_model.load_data(entity_type="CutItem", filters=tray_filters, fields=tray_fields, order=orders)
        

    def save_mini_cut_data(self, mini_data, node):
        mini_data.store_in_session(node)
        self.cached_mini_cut_data = mini_data

    def on_entire_cut(self):

        seq_node = None
        seq_group = rvc.viewNode()
        if rvc.nodeType(seq_group) == "RVSequenceGroup":
            seq_node = groupMemberOfType(seq_group, "RVSequence")

        if seq_node is None:
            self._app.engine.log_error("Entire-cut load on non-sequence (%s)." % rvc.viewNode())
            return
        
        # load current mini-cut state for this sequence node
        mini_data = MiniCutData.load_from_session(seq_node)

        if not mini_data.active:
            self._app.engine.log_error("Entire-cut load, but sequence is not mini-cut.")
            return

        # we rely on tray selection being synced with frame
        (clip_index, offset) = self.clip_index_and_offset_from_frame()

        # compensate for current mini-cut state
        clip_index = clip_index + mini_data.first_clip

        # get "entire cut" edl data and node inputs
        shadow_source = getIntProp   (seq_node + ".shadow_edl.source", [])
        shadow_frame  = getIntProp   (seq_node + ".shadow_edl.frame",  [])
        shadow_in     = getIntProp   (seq_node + ".shadow_edl.in",     [])
        shadow_out    = getIntProp   (seq_node + ".shadow_edl.out",    [])
        shadow_inputs = getStringProp(seq_node + ".shadow_edl.inputs", [])

        # configure sequence node
        setProp(seq_node + ".edl.source", shadow_source)
        setProp(seq_node + ".edl.frame",  shadow_frame)
        setProp(seq_node + ".edl.in",     shadow_in)
        setProp(seq_node + ".edl.out",    shadow_out)

        rvc.setNodeInputs(seq_group, shadow_inputs)

        # new mini_data to reflect new state, store in sequence node
        self.save_mini_cut_data(MiniCutData(False), seq_node)

        # restore frame location (setting frame here directly doesn't work (I
        # think because sequence node recomputes it's internal EDL lazily).
        self._queued_frame_change = shadow_frame[clip_index] + offset

        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')

        self.tray_list.repaint()

    def on_mini_cut(self):
        # XXX handle non-Cut situations
        # XXX are we looking at the right node ?

        # we rely on tray selection being synced with frame
        (index, offset) = self.clip_index_and_offset_from_frame()

        self.load_mini_cut(index, offset=offset)

        self.tray_list.repaint()

    def on_cache_loaded(self):
        pass
        #print "CACHE LOADED."

    def createText(self, node, text, hpos, vpos):

        rvc.newProperty('%s.position' % node, rvc.FloatType, 2)
        rvc.newProperty('%s.color' % node, rvc.FloatType, 4)
        rvc.newProperty('%s.spacing' % node, rvc.FloatType, 1)
        rvc.newProperty('%s.size' % node, rvc.FloatType, 1)
        rvc.newProperty('%s.scale' % node, rvc.FloatType, 1)
        rvc.newProperty('%s.rotation' % node, rvc.FloatType, 1)
        rvc.newProperty("%s.font" % node, rvc.StringType, 1)
        rvc.newProperty("%s.text" % node, rvc.StringType, 1)
        rvc.newProperty('%s.debug' % node, rvc.IntType, 1)

        rvc.setFloatProperty('%s.position' % node, [ float(hpos), float(vpos) ], True)
        rvc.setFloatProperty('%s.color' % node, [ 1.0, 1.0, 1.0, 1.0 ], True)
        rvc.setFloatProperty('%s.spacing' % node, [ 1.0 ], True)
        rvc.setFloatProperty('%s.size' % node, [ 0.004 ], True)
        rvc.setFloatProperty('%s.scale' % node, [ 1.0 ], True)
        rvc.setFloatProperty('%s.rotation' % node, [ 0.0 ], True)
        rvc.setStringProperty("%s.font" % node, [""], True)
        rvc.setStringProperty("%s.text" % node, [text], True)
        rvc.setIntProperty('%s.debug' % node, [ 0 ], True)

    def find_latest_cut_for_version(self, shot_entity, version_data, project_entity):
        
        """
        original JS query here:
        https://github.com/shotgunsoftware/shotgun/blob/develop/cut_support_2016/public/javascripts/util/cuts_helper.js#L167

        returns the latest cut entity for this version or None.
        
        """

        version_entity = {}
        version_entity['id'] = version_data['id']
        version_entity['type'] = "Version"
        version_entity['name'] = version_data['code']

        cut_fields = ['id', 'created_at', 'cached_display_name']

        # for reference, what it looks like if you have shot and project...
        # cut_filters = [
        #     ['project', 'is', project_entity],  
        #     {
        #         "filter_operator": "any",
        #         "filters": [
        #             ['cut_items.CutItem.version', 'is', version_entity], 
        #             ['version', 'is', version_entity],
        #             ['cut_items.CutItem.shot', 'is', shot_entity]
        #         ]
        #     },
        # ]

        cut_filters = [
            {
                "filter_operator": "any",
                "filters": [
                    ['cut_items.CutItem.version', 'is', version_entity], 
                    ['version', 'is', version_entity]
                ]
            }
        ]

        if shot_entity:
            cut_filters[0]['filters'].append(['cut_items.CutItem.shot', 'is', shot_entity])

        if project_entity:
            cut_filters.insert(0, ['project', 'is', project_entity] )

        cut_order = [ {'field_name':'created_at','direction':'desc'} ]

        cut_presets = [
                { "preset_name": "LATEST", "latest_by": "REVISION_NUMBER" }
        ]

        cuts = self._bundle.shotgun.find(
            'Cut',
            fields=cut_fields,
            filters=cut_filters,
            additional_filter_presets=cut_presets,
            order=cut_order
        )

        if cuts:
            return { "id" : cuts[0]['id'], "cached_display_name" : cuts[0]['cached_display_name'], "type" : "Cut" }
 
        return None               

    def sequence_group_from_target(self, target_entity):
        """
        We keep a RVSequenceGroup around to represent each Playlist, and two
        for each Cut (one for entire-cut and one for min-cut).
        """
        # XXX handle target_entity["server"]

        t_type = target_entity["type"]
        t_id   = target_entity["ids"][0]

        for s in rvc.nodesOfType("RVSequenceGroup"):
            # for Playlist and Cut, we stick with one Sequence node per entity.
            # But for the "scratch" usage of playing arbitrary group of
            # Versions, we just re-use a single sequence.
            if ( getStringProp(s + ".sg_review.target_type", None) == t_type and
                (getIntProp   (s + ".sg_review.target_id",   None) == t_id or 
                 t_type == "Version")):
                return s

        # We failed to find our RVSequenceGroup, so make one.

        s = rvc.newNode("RVSequenceGroup")

        setProp(s + ".sg_review.target_type", t_type)

        if (t_type != "Version"):
            setProp(s + ".sg_review.target_id",   t_id)

        return s

    def check_media_contents(self, path):

        if not path:
            return False

        return (True if self.no_media_check else bool(rvc.existingFilesInSequence(path)))

    def swap_in_home_dir(self, path):

        if path and len(path) > 2 and path[0:2] == "~/":
            path = QtCore.QDir.homePath() + path[1:]

        return path

    def media_type_fallback(self, version_data, media_type):
        
        path = version_data.get(standard_media_types[media_type].path_field)
        path = self.swap_in_home_dir(path)

        if self.check_media_contents(path):
            return media_type

        other = "Movie" if (media_type == "Frames") else "Frames"
        path = version_data.get(standard_media_types[other].path_field)
        path = self.swap_in_home_dir(path)

        if self.check_media_contents(path):
            return other

        return None
            
    def find_group_from_version_id(self, version_id):

        group = None
        for s in rvc.nodesOfType("RVSourceGroup"):
            if getIntProp(s + ".sg_review.version_id", -1) == version_id:
                # XXX we should be storing/checking url too
                # XXX possibly this version data is stale, think about when we
                # might refresh ?
                group =  s

        return group

    def source_group_from_version_data(self, version_data, media_type=None):

        if False:
            print "source_group_from_version_data() data:"
            pp.pprint(version_data)

        source_group = self.find_group_from_version_id(version_data["id"])
        if source_group:
            return source_group

        # We failed to find our RVSourceGroup, so make one.

        if media_type is None:
            media_type = self._prefs.preferred_media_type

        path = None
        no_media = False
        m_type = self.media_type_fallback(version_data, media_type)
        if m_type: 
            path = version_data[standard_media_types[m_type].path_field]
            path = self.swap_in_home_dir(path)

        if not path:
            self._app.engine.log_error("Version '%s' has no local media" % version_data["code"])
            path = "black,start=1,end=24.movieproc"
            m_type = "Movie"
            no_media = True

        try:
            source_node = rvc.addSourceVerbose([path])
        except:
            # XXX
            return

        source_group = rvc.nodeGroup(source_node)

        if no_media:
            overlay_node = groupMemberOfType(source_group, "RVOverlay")
            self.createText(overlay_node + '.text:sg_review_error', 
                    version_data["code"] + '\nhas no playable local media.', -0.5, 0.0)

        setProp(source_group + ".sg_review.version_id",   version_data["id"])
        setProp(source_group + ".sg_review.version_data", json.dumps(version_data))
        setProp(source_group + ".sg_review.timestamp", int(time.time()) )

        self.set_media_type_property(source_group, m_type)

        self.configure_source_media(source_group, version_data)

        rve.setUIName(source_group, version_data.get("code", "No Version Name"))

        return source_group

    def sequence_data_from_query_item(self, sg_item, target_entity):
        data = {}

        data["target_entity"] = target_entity
        data["ui_name"]       = target_entity["type"]
        data["entity"]        = None
        data["project"]       = None

        if   target_entity["type"] == "Cut":
            if sg_item:
                data["ui_name"] = sg_item["cut.Cut.cached_display_name"]
                data["entity"]  = sg_item["cut.Cut.entity"]

        elif target_entity["type"] == "Playlist":
            data["ui_name"]     = "Playlist %d" % target_entity["ids"][0]
            if sg_item and sg_item.get("playlists"):
                for p in sg_item.get("playlists"):
                    if p["id"] == target_entity["ids"][0]:
                        data["ui_name"] = p["name"]

        elif target_entity["type"] == "Version":
            data["ui_name"]     = "%d Versions" % len(target_entity.get("ids", [1]))

        if sg_item:
            data["project"]     = sg_item["project"]

        return data

    def clip_index_and_offset_from_frame(self):

        index = -1
        offset = 0
        if rvc.nodeType(rvc.viewNode()) == "RVSequenceGroup":
            current_frame = rvc.frame()
            seq_node = groupMemberOfType(rvc.viewNode(), "RVSequence")
            frames = rvc.getIntProperty(seq_node + ".edl.frame")
            last_frame = 0
            for f in frames:
                if current_frame < f:
                    offset = current_frame - last_frame
                    break
                index += 1
                last_frame = f

        return (index, offset)

    def clip_index_from_frame(self):
        (index, offset) = self.clip_index_and_offset_from_frame()
        return index

    def sequence_data_from_session(self):
        json_str = getStringProp(rvc.viewNode() + ".sg_review.sequence_data", None)
        if json_str:
            return json.loads(json_str)

        return None

    def data_from_cut_item(self, sg, rv):
        version_data = {}
        edit_data = {}

        # We prefer the Version that resulted from filtering, fall back to the
        # one attached to the CutItem, then fallback to the one attached to the
        # Cut. 

        if   rv and rv.get("id"):

            for f in required_version_fields:
                version_data[f] = rv.get(f)

            edit_data["in"]    = sg.get("cut_item_in")
            edit_data["out"]   = sg.get("cut_item_out")

        elif sg and sg.get("version.Version.id"):

            for f in required_version_fields:
                version_data[f] = sg.get("version.Version." + f)

            edit_data["in"]    = sg.get("cut_item_in")
            edit_data["out"]   = sg.get("cut_item_out")

        else:
            for f in required_version_fields:
                version_data[f] = sg.get("cut.Cut.version.Version." + f)

            edit_data["in"]    = sg.get("edit_in")
            edit_data["out"]   = sg.get("edit_out")

        edit_data["shot"] = sg.get("shot")

        if version_data["id"] is None:
            self._app.engine.log_error("No Version data for CutItem id=%d." % sg.get("id"))
            version_data["id"]   = 100000 + sg.get("cut.Cut.id", 0)
            version_data["code"] = "Missing Version"

        return (version_data, edit_data)

    def data_from_version(self, sg):
        version_data = sg
        edit_data = {}
        edit_data["in"]  = sg.get("sg_first_frame", 1)
        edit_data["out"] = sg.get("sg_last_frame",  100)
        edit_data["shot"] = None
        
        if sg.get("entity"):
            if sg.get("entity").get("type") == "Shot":
                edit_data["shot"] = sg.get("entity")

        return (version_data, edit_data)

    def data_from_query_item(self, sg_item, rv_item, target_entity):
        if target_entity["type"] == "Cut":
            (version_data, edit_data) = self.data_from_cut_item(sg_item, rv_item)
        else:
            (version_data, edit_data) = self.data_from_version(sg_item)

        #  Try to recover from cases with missing data
        #
        if edit_data["in"] is None:
            edit_data["in"] = 1
        if edit_data["out"] is None:
            edit_data["out"] = edit_data["in"] + 24

        return (version_data, edit_data)

    def pinned_from_sequence(self, seq_group=None):
        """
        Return shot-keyed dict of pinned version associated with this sequence (cut).
        """
        if not seq_group:
            seq_group = rvc.viewNode()
            if rvc.nodeType(seq_group) != "RVSequenceGroup":
                return {}

        pinned_str = getStringProp(seq_group + ".sg_review.pinned", "")
        if pinned_str:
            return json.loads(pinned_str)

        return {}
        
    def shot_id_str_from_version_data(self, version_data):

        if not version_data:
            return None

        entity = version_data.get("entity")
        if not entity:
            return None

        if entity.get("type") != "Shot":
            return None

        return str(entity.get("id"))

    def update_pinned_in_sequence(self, seq_group, version_data):

        shot = self.shot_id_str_from_version_data(version_data)
        if not shot:
            return

        pinned = self.pinned_from_sequence(seq_group)

        # note that if there was previously another Versioned pinned for clips
        # referencing this shot, this Version will replace it.
        pinned[shot] = version_data

        setProp(seq_group + ".sg_review.pinned", json.dumps(pinned))

    def index_is_pinned(self, index):

        seq_group = rvc.viewNode()
        if rvc.nodeType(seq_group) != "RVSequenceGroup":
            return False

        pinned = self.pinned_from_sequence(seq_group)
        
        # get source of this index

        seq_node      = groupMemberOfType(seq_group, "RVSequence")
        inputs        = rvc.nodeConnections(seq_group, False)[0]
        shadow_source = getIntProp(seq_node + ".shadow_edl.source", [])
        shadow_inputs = getStringProp(seq_node + ".shadow_edl.inputs", [])

        # allow for half-build data structures:

        if index not in range(len(shadow_source)):
            return False

        if shadow_source[index] not in range(len(shadow_inputs)):
            return False

        source_group = shadow_inputs[shadow_source[index]]

        # get shot from version_data of this source and look up in pinned

        version_data = self.version_data_from_source(source_group)

        shot = self.shot_id_str_from_version_data(version_data)

        return True if shot and shot in pinned else False
        
    def reset_pinned(self, seq_group, incoming_pinned):
        # Initialize pinned state (eg when we go from version to cut, in which
        # case the version should be pinned, or from one cut to another, in
        # which case we should "rememeber" the pinned state).

        setProp(seq_group + ".sg_review.pinned", json.dumps(incoming_pinned))

    # signal from model so incremental_update is False (we need to run follow-on
    # query, if any)
    def on_data_refreshed(self, was_refreshed):
        self.main_query_active = False
        if not self.compare_active:
            self.on_data_refreshed_internal(was_refreshed, incremental_update=False)
        else:
            sources = []
            rows = self.tray_proxyModel.rowCount()
            for index in range(0, rows):
                item = self.tray_proxyModel.index(index, 0)
                sg_item = shotgun_model.get_sg_data(item)
                (version_data, edit_data) = self.data_from_version(sg_item)
                if version_data:
                    sources.append(self.source_group_from_version_data(version_data))

            self.compare_sources(sources)
            self.load_version_id_from_session()
            if self._prefs.auto_play:
                rvc.play()

        # update pinned list with pinned thumbs we saved from the last load
        self.tray_model.update_pinned_items(self.pinned_from_sequence())
        self.tray_list.repaint()

        self.compare_active = False
        
    # the way data from shotgun gets into the tray
    def on_data_refreshed_internal(self, was_refreshed, incremental_update=False):
        """
        The tray_model has one item per clip in sequence; each clip's data
        comes from a CutItem (when loading a Cut) or straight from a Version
        (when loading a Playlist).
        """
        rows = self.tray_proxyModel.rowCount()
        if False:
            print "--------------------------------------- on_data_refreshed_internal() incremental_update", incremental_update, "rows", rows
            print "--------------------------------------- target"
            pp.pprint(self.target_entity)
            for index in range(0, rows):
                item = self.tray_proxyModel.index(index, 0)
                sg_item = shotgun_model.get_sg_data(item)
                rv_item = item.data(self._RV_DATA_ROLE)
                print "--------------------------------------- sg_item"
                pp.pprint(sg_item)
                print "--------------------------------------- rv_item"
                pp.pprint(rv_item)
            # return
        self._app.engine.log_debug('on_data_refreshed_internal: %r' % str(QtCore.QThread.currentThread()))

        # find or make RV sequence node for this target entity
        seq_group_node = self.sequence_group_from_target(self.target_entity)
        seq_node = groupMemberOfType(seq_group_node, "RVSequence")

        # If this is the first entry, check self.incoming_pinned otherwise
        # retrieve previous pinned state from sequence.
        #
        # Likewise check to see if caller intends that we start in mini-cut
        # mode.
        #
        look_for_mini_focus_clip = False
        mini_focus_clip_from_item = -1
        mini_focus_clip_from_version = -1
        mini_focus_clip_from_shot = -1
        if not incremental_update:
            self.reset_pinned(seq_group_node, self.incoming_pinned)
            self.incoming_pinned = {}
            if self.incoming_mini_cut_focus:
                look_for_mini_focus_clip = True
                mini_focus_clip_version_target = -1
                mini_focus_clip_shot_target = -1
                mini_focus_clip_item_target = -1
                if self.incoming_mini_cut_focus.get("type") == "CutItem":
                    mini_focus_clip_item_target = self.incoming_mini_cut_focus["id"]
                else:
                    mini_focus_clip_version_target = self.incoming_mini_cut_focus["id"]
                    if self.incoming_mini_cut_focus.get("shot"):
                        mini_focus_clip_shot_target = self.incoming_mini_cut_focus["shot"]["id"]
                # XXX handle case when focus target is from cut-item (playing a cut-item)
            else:
                # Note also if we come back to this with new query, we need
                # to clear any previous mini-cut state !
                self.save_mini_cut_data(MiniCutData(False), seq_node)

        # get shot-keyed dict of pinned versions
        pinned = self.pinned_from_sequence(seq_group_node)

        # tray proxy model sorting in cut order
        self.tray_proxyModel.sort(0, QtCore.Qt.AscendingOrder)

        sequence_data = self.sequence_data_from_query_item(None, self.target_entity)
        input_map = {}
        seq_inputs = []
        edit_data_list = []
        accumulated_frames = 0

        edl_source_nums = []
        edl_frames = []
        edl_ins = []
        edl_outs = []

        rows = self.tray_proxyModel.rowCount()
        # XXX handle sequence_data for queries that return no rows? - sb
        # I think just Error and return

        for index in range(0, rows):
            item = self.tray_proxyModel.index(index, 0)
            sg_item = shotgun_model.get_sg_data(item)
            rv_item = item.data(self._RV_DATA_ROLE)

            # Collect some data to attach to the sequence level
            if index == 0:
                sequence_data = self.sequence_data_from_query_item(
                        sg_item, self.target_entity)

            # Build unique version_data and edit_data dictionaries for
            # this row.  This contains all the logic for using different
            # Versions etc.
            (version_data, edit_data) = self.data_from_query_item(
                    sg_item, rv_item, self.target_entity)

            # store edit_data
            edit_data_list.append(json.dumps(edit_data))

            # If displaying a Cut and the shot of this CutItem corresponds to a
            # pinned version, use that instead.
            if self.target_entity.get("type") == "Cut":
                shot_id = edit_data["shot"].get("id") if edit_data["shot"] else None;
                pinned_version_data = pinned.get(str(shot_id))
                if pinned_version_data:
                    version_data = pinned_version_data
                    # XXX ok, we just swapped version_data out, but the old
                    # version might have been the "base layer" in which case
                    # the edit_data is wrong for this version ...

            # Now we have version data, find or create the corresponding
            # RVSourceGroup
            src_group = self.source_group_from_version_data(version_data)

            # If looking for mini-cut focus, check all possible methods of
            # matching the clip.
            if look_for_mini_focus_clip:
                if (    mini_focus_clip_version_target != -1 and 
                        mini_focus_clip_version_target == version_data["id"] and
                        mini_focus_clip_from_version == -1):
                    mini_focus_clip_from_version = len(edl_frames)
                    # XXX this is not going to work for cases where the "right"
                    # version will not appear until after secondary query is
                    # finished ...

                if (    mini_focus_clip_shot_target != -1 and
                        edit_data["shot"] and edit_data["shot"]["id"]== mini_focus_clip_shot_target and
                        mini_focus_clip_from_shot == -1):
                    mini_focus_clip_from_shot = len(edl_frames)

                if (    mini_focus_clip_item_target != -1 and
                        mini_focus_clip_item_target == sg_item["id"] and
                        mini_focus_clip_from_item == -1):
                    mini_focus_clip_from_item = len(edl_frames)

            # input_num for this clip is just the nth input, unless we already have it.
            if src_group in input_map:
                input_num = input_map[src_group]
            else:
                input_num = len(seq_inputs)
                input_map[src_group] = input_num
                seq_inputs.append(src_group)

            edl_source_nums.append(input_num)
            edl_ins.        append(edit_data["in"])
            edl_outs.       append(edit_data["out"])
            edl_frames.     append(accumulated_frames + 1)

            # keep track of total frames
            accumulated_frames += edit_data["out"] - edit_data["in"] + 1

            # XXX - re-implement
            ## if we had a version selected before the query we try to select it again when this cut is loaded
            #if 'version.Version.id' in sg_item:
            #    if sg_item['version.Version.id'] == v_id:
            #        final_selection = item


        # XXX error if sequence_data is None

        # needed for menus.
        # XXX may be problem later if we have to handle multiple Projects
        # XXX build status menu ONCE per project. - sb
        if not self.project_entity:
            self.project_entity = sequence_data["project"]

        self._popup_utils.build_status_menu(self.project_entity)
        self._popup_utils.check_pipeline_menu()
         # write the current state if filters and statues to prefs
        self._prefs.save()

        # Set or reset the UI Name of the sequence node
        rve.setUIName(seq_group_node, sequence_data["ui_name"])
        self.tray_main_frame.tray_button_browse_cut.setText(sequence_data["ui_name"])

        # make sure RV doesn't automatically create the EDL
        rvc.setIntProperty(seq_node + ".mode.autoEDL",    [0])
        rvc.setIntProperty(seq_node + ".mode.useCutInfo", [0])

        setProp(seq_node + ".shadow_edl.inputs", seq_inputs)

        edl_source_nums.append(0)
        edl_ins.append(0)
        edl_outs.append(0)
        edl_frames.append(accumulated_frames + 1)

        # We set the "shadow" edl props no matter what, since they apply to
        # both "mini-cut" and "entire-cut" modes.

        setProp(seq_node + ".shadow_edl.source", edl_source_nums)
        setProp(seq_node + ".shadow_edl.frame",  edl_frames)
        setProp(seq_node + ".shadow_edl.in",     edl_ins)
        setProp(seq_node + ".shadow_edl.out",    edl_outs)

        setProp(seq_group_node + ".sg_review.sequence_data", json.dumps(sequence_data))
        setProp(seq_group_node + ".sg_review.edit_data", edit_data_list)

        if look_for_mini_focus_clip and (
                mini_focus_clip_from_version != -1 or
                mini_focus_clip_from_shot    != -1 or
                mini_focus_clip_from_item    != -1):

            # use "best" mini-cut focus clip detected above

            if   mini_focus_clip_from_item != -1:
                focus_index = mini_focus_clip_from_item

            elif mini_focus_clip_from_version != -1:
                focus_index = mini_focus_clip_from_version

            else:
                focus_index = mini_focus_clip_from_shot

            # get spinner values from GUI
            (left_num, right_num) = self.get_mini_values()

            # trim left/right neighbor nums by EDL limits
            first_index = max(0,                focus_index - left_num)
            last_index  = min(len(edl_ins) - 2, focus_index + right_num)

            mini_data = MiniCutData(True, focus_index, first_index, last_index)

            self.save_mini_cut_data(mini_data, seq_node)

        else:
            mini_data = MiniCutData.load_from_session(seq_node)


        if mini_data.active:
            # XXX f = rvc.frame()
            self.load_mini_cut(mini_data.focus_clip - mini_data.first_clip, seq_group=seq_group_node)
            # XXX rvc.setFrame(f)

            # XXX might not be needed
            # self.configure_visibility()
        else:
            # XXX 
            setProp(seq_node + ".edl.source", edl_source_nums)
            setProp(seq_node + ".edl.frame",  edl_frames)
            setProp(seq_node + ".edl.in",     edl_ins)
            setProp(seq_node + ".edl.out",    edl_outs)

            rvc.setNodeInputs(seq_group_node, seq_inputs)

        rvc.setViewNode(seq_group_node)

        # filter query logic
        # 
        # Test here if we need to run filtering query automatically. IE if we
        # have non-trivial filtering parameters and incremental_update is
        # false (because we are not _responding_ to a filter update).  If so,
        # initiate that query.  If not, display completion feedback 

        filter_query_required = self._popup_utils.filters_exist()

        # If we want to auto play in general, we can deduce that we want to in
        # this case from playback_queued, or from the fact that this is a
        # "first load" and no filter_query is scheduled.

        trigger_playback = self._prefs.auto_play and (self.playback_queued or (
                not incremental_update and not filter_query_required))

        if not incremental_update and filter_query_required:
            # trigger filter query
            self._popup_utils.request_versions_for_statuses_and_steps(True)
            self.playback_queued = self._prefs.auto_play
        else :
            rve.displayFeedback("Loading complete", 2.0)

        # highlight the first clip
        self.frameChanged(None)

        self.load_version_id_from_session()
        rvc.redraw()
        
        if trigger_playback:
            rvc.play()
            self.playback_queued = False

        if self.target_entity["type"] == "Cut":
            # self.create_related_cuts_menu(sequence_data["entity"], None)
            
            # we want this to happen now, so that the menu will be ready
            # self._popup_utils.request_related_cuts_from_models()
            # creating just the menu alone leads to in progress refresh
            # self._popup_utils.create_related_cuts_from_models()
            pass
        else:
            if self.related_cuts_menu:
                self.related_cuts_menu.clear()




    def set_cut_control_visibility(self, vis):
        self.tray_button_mini_cut.setVisible(vis)
        self.tray_button_entire_cut.setVisible(vis)
        self.tray_bar_button.setVisible(vis)
        self.tray_left_spinner.setVisible(vis)
        self.tray_right_spinner.setVisible(vis)
        self.tray_left_label.setVisible(vis)
        self.tray_right_label.setVisible(vis)

    def configure_visibility(self):
        """
        Central location for all logic determining visibility of gui elements:
        dock widgets, menus, etc.
        """

        # if main query is running just wait, update will happen after
        if self.main_query_active:
            return

        # are we looking at a sequence that we manage ?

        query_target_entity = None
        seq_data = self.sequence_data_from_session()
        if seq_data:
            query_target_entity = seq_data.get("target_entity")

        if query_target_entity and query_target_entity == self.target_entity:
            # this is some kind of RVSequenceGroup managed by us, with matching
            # query results in tray modelk.
            # so make tray AND details visible unless user has hidden them, or
            # the user wants them never to be shown automatically
            #
            if not self.tray_hidden_this_session and self._prefs.auto_show_tray: 
                self.tray_dock.show() 
            if not self.details_hidden_this_session and self._prefs.auto_show_details: 
                self.note_dock.show()

            # it's a sequence of some kind, but maybe not a Cut; set menu and
            # control visibility accordingly
            its_a_cut = query_target_entity.get("type") == "Cut"
            self.set_cut_control_visibility(its_a_cut)

            # preliminary configuration of cut mode button: if we disable here
            # we may enable later once we are stopped on a clip that has a
            # default cut.
            if its_a_cut:
                self.enable_cuts_action(enable=True, tooltip='Turn off cuts mode', enable_blue=True)
            else:
                self.enable_cuts_action(enable=False, tooltip='', enable_blue=False)


        else:
            # it's not a Cut or a Playlist or a Version sequence.  But maybe
            # it's a "version source" or some view that has a "version source"
            # as an input
            possible_sources = rvc.nodeConnections(rvc.viewNode(), False)[0] + [rvc.viewNode()]
            sources = filter(lambda x: rvc.nodeType(x) == "RVSourceGroup", possible_sources)

            found_version = False
            for s in sources:
                if self.version_id_from_source(s):
                    found_version = True
                    break

            if found_version:
                # we're looking at a source representing a Version, so
                # maybe make details visible, but always hide tray
                if not self.details_hidden_this_session:
                    self.note_dock.show()
                self.tray_dock.hide()

            else:
                # totally untracked, hide everything
                self.note_dock.hide()
                self.tray_dock.hide()

    def edit_data_from_session(self):
        data = None

        seq_group = rvc.viewNode()

        if rvc.nodeType(seq_group) == "RVSequenceGroup":
            edit_prop = seq_group + ".sg_review.edit_data"
            if rvc.propertyExists(edit_prop):
                edit_data_list = getStringProperty(edit_prop)
                clip_index = self.clip_index_from_frame()
                if clip_index < len(edit_data_list):
                    data = json.loads(edit_data_list[clip_index])

        return data

           
    def tray_double_clicked(self, index):
        # XXX go over
        return
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
        rvc.setIntProperty('%s.edl.frame' % self.cut_seq_name, single_frames, True)
        rvc.setIntProperty('%s.edl.in' % self.cut_seq_name, single_ins, True)
        rvc.setIntProperty('%s.edl.out' % self.cut_seq_name, single_outs, True)
        
        rvc.setIntProperty("%s.mode.autoEDL" % self.cut_seq_name, [0])
        rvc.setIntProperty("%s.mode.useCutInfo" % self.cut_seq_name, [0])

        sources = rvc.nodesOfType("RVSourceGroup")
        single = [ sources[index.row()] ]
        rvc.setNodeInputs(self.cut_seq, single)
        rvc.setViewNode(self.cut_seq)
        rvc.setFrame(1)
        rvc.play()

    def get_mini_values(self):
        self._prefs.mini_left_count  = self.tray_main_frame.mini_left_spinner.value() 
        self._prefs.mini_right_count = self.tray_main_frame.mini_right_spinner.value() 
        self._prefs.save()

        return (
            self._prefs.mini_left_count,
            self._prefs.mini_right_count)

    def load_mini_cut(self, focus_index, seq_group=None, offset=0):
        self._app.log_info("load_mini_cut() focus %d seq_group %s offset %d" % (focus_index, seq_group, offset))

        seq_node = None
        if not seq_group:
            seq_group = rvc.viewNode()

        if seq_group and rvc.nodeType(seq_group) == "RVSequenceGroup":
            seq_node = groupMemberOfType(seq_group, "RVSequence")

        if seq_node is None:
            self._app.engine.log_error("Mini-cut load on non-sequence (%s)." % rvc.viewNode())
            return
        
        # load current mini-cut state for this sequence node
        mini_data = MiniCutData.load_from_session(seq_node)

        # compensate for current mini-cut state
        if mini_data.active:
            focus_index = focus_index + mini_data.first_clip

        # get "entire cut" edl data and node inputs
        shadow_source = getIntProp   (seq_node + ".shadow_edl.source", [])
        shadow_frame  = getIntProp   (seq_node + ".shadow_edl.frame",  [])
        shadow_in     = getIntProp   (seq_node + ".shadow_edl.in",     [])
        shadow_out    = getIntProp   (seq_node + ".shadow_edl.out",    [])
        shadow_inputs = getStringProp(seq_node + ".shadow_edl.inputs", [])

        mini_source = []
        mini_frame = []
        mini_in = []
        mini_out = []
        mini_inputs = []
        accumulated_frames = 0

        input_map = {}

        # get spinner values from GUI
        (left_num, right_num) = self.get_mini_values()

        # trim left/right neighbor nums by EDL limits
        first_index = max(0,                  focus_index - left_num)
        last_index  = min(len(shadow_in) - 2, focus_index + right_num)

        for i in range(first_index, last_index + 1):

            # input_num for this clip is just the nth input, unless we already
            # have it.  Either way it is already in the shadow_inputs list at
            # the source index for this clip

            src_group = shadow_inputs[shadow_source[i]]
            
            if src_group in input_map:
                input_num = input_map[src_group]
            else:
                input_num = len(mini_inputs)
                input_map[src_group] = input_num
                mini_inputs.append(src_group)

            mini_source.append(input_num)
            mini_in.    append(shadow_in[i])
            mini_out.   append(shadow_out[i])
            mini_frame. append(accumulated_frames + 1)

            # keep track of total frames
            accumulated_frames += shadow_out[i] - shadow_in[i] + 1

        # add terminiators
        mini_source.append(0)
        mini_in.append(0)
        mini_out.append(0)
        mini_frame.append(accumulated_frames + 1)

        # configure sequence node
        setProp(seq_node + ".edl.source", mini_source)
        setProp(seq_node + ".edl.frame",  mini_frame)
        setProp(seq_node + ".edl.in",     mini_in)
        setProp(seq_node + ".edl.out",    mini_out)

        rvc.setNodeInputs(seq_group, mini_inputs)

        # new mini_data to reflect new state, store in sequence node
        self.save_mini_cut_data(MiniCutData(True, focus_index, first_index, last_index), seq_node)

        # restore frame location
        rvc.setFrame(mini_frame[focus_index - first_index] + offset)

        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')

        self.tray_list.repaint()

    def tray_clicked(self, index):

        if rvc.nodeType(rvc.viewNode()) == "RVSequenceGroup":
            seq_node = groupMemberOfType(rvc.viewNode(), "RVSequence")
            if seq_node:
                mini_data = MiniCutData.load_from_session()
                row = index.row()
                frame_index = row
                if mini_data.active:
                    if     (frame_index < mini_data.first_clip or
                            frame_index > mini_data.last_clip):
                        frame_index = min(max(mini_data.first_clip,frame_index), mini_data.last_clip)
                        index = self.tray_model.index(frame_index, 0)
                    frame_index = frame_index - mini_data.first_clip 
                frame = rvc.getIntProperty(seq_node + ".edl.frame")
                rvc.setFrame(frame[frame_index])
                sm = self.tray_list.selectionModel()           
                sm.select(index, sm.ClearAndSelect)
                # self.tray_list.scrollTo(index, QtGui.QAbstractItemView.PositionAtCenter)

                # XXX below should work according to docs
                # self.tray_list.scrollTo(index, QtGui.QAbstractItemView.EnsureVisible)

        self.tray_list.repaint()




