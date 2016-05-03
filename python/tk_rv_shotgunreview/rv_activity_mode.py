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
        g = "sg_review_mode"
        self.group = g

        self.preferred_media_type = rvc.readSettings(g, "preferred_media_type", "Movie")
        self.startup_view_details = rvc.readSettings(g, "startup_view_details", True)
        self.startup_view_tray    = rvc.readSettings(g, "startup_view_tray", True)

    def save(self):
        g = self.group
        rvc.writeSettings(g, "preferred_media_type", self.preferred_media_type)
        rvc.writeSettings(g, "startup_view_details", self.startup_view_details)
        rvc.writeSettings(g, "startup_view_tray",    self.startup_view_tray)

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
            self.load_version_id_from_session()
 
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

    def version_data_from_source(self, group_name=None):
        
        if not group_name:
            group_name = self.current_source()
                
        if group_name:
            version_data_str = getStringProp(group_name + ".cut_support.version_data", None)
            if version_data_str:
                try:
                    return json.loads(version_data_str)
                except Exception as e:
                        print "ERROR: load_version_id_from_session JSON EXCEPTION %r" % e
                        print "JDATA: %r" % version_data_str
                        print "group_name: %r" % group_name

        return None

    def load_version_id_from_session(self, group_name=None):
        
        version_data = self.version_data_from_source(group_name)

        if version_data:
            if self.version_id != version_data["id"]:
                self.load_data({"type": "Version", "id": version_data["id"]})
        else:
            #  If we can't find the version_data property it probably means
            #  that this RVSourceGroup was not created "by us" (IE it does
            #  not have any shotgun data), so just clear the details pane
            #  and consider the details "clean" until further notice.
            #
            self.load_data({"type": "Version", "id": None})

        self.details_dirty = False

        return version_data

    # RV Events

    def replaceWithSelected(self, event):
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

    def compareWithCurrent(self, event):
        vlist = []
        try:
            # examine whats under the playhead, thats a source you want.
            ph_version = self.version_data_from_source()
            vlist.append(ph_version)
            # now whatever we got from the event
            vd = json.loads(event.contents())
            for v in vd:
                # XXX ? v["pinned"] = 1
                vlist.append(v)
            # XXX "load_layout" or whatever
            self.load_sequence_with_versions(vlist)
            
        except Exception as e:
            self._app.engine.log_error("compareWithCurrent %r" % e)

        finally:
            event.reject()

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
        self.details_dirty = True

    def frameChanged(self, event):
        if event:
            event.reject()
        try:
            if not self.tray_dock.isVisible():
                return
            idx = self.clip_index_from_frame()
            mini_data = MiniCutData.load_from_session()
            if mini_data and mini_data.active:
                idx = idx + mini_data.first_clip
            self.details_dirty = True
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
        # XXX auto-pinning should be controlled by a preference (default on)

        # Ignore the event if no DetailsPanel built yet, or if we are
        # "buffering" (ie playback paused to fill cache) or in "turn-around"
        # (ie looping)
        cont = event.contents()
        if (self.details_panel and cont != "buffering" and cont != "turn-around"):
            # We only auto-pin the details if they are not already pinned
            if   (event.name() == "play-start" and not self.details_panel.is_pinned):
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

    def version_submitted(self, event):
        event.reject()
        self.note_dock.show()

    def per_render_event(self, event):
        event.reject()
        if self._queued_frame_change != -1:
            rvc.setFrame(self._queued_frame_change)
            self._queued_frame_change = -1

    def set_default_media_type_movie(self, event):
        self._prefs.preferred_media_type = "Movie"
        self._prefs.save()

    def set_default_media_type_frames(self, event):
        self._prefs.preferred_media_type = "Frames"
        self._prefs.save()

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
        if (self.tray_dock):
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

    def make_note_attachments(self, event):
        '''
        Find the annotated frames for the given version, export them through RVIO, then submit them
        '''
        # Not sure if anyone else wants to use this,
        # but might as well let them
        event.reject() 

        # Look for unsaved annotation
        props = {}
        try:
            eventDict = eval(event.contents())
            group = self.loaded_sources[eventDict['id']]['group_name']
            props = self.get_unstored_frame_props(group)
        except Exception as exc:
            self._app.log_error("Unable to locate annotation strokes: " + exc.output)
        if len(props) <= 0:
            self._app.log_info("Found no new annotations to attach")
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
        if (lic != None):
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
            self._app.log_error("Unable to export annotation: " + exc.output)
        
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
            tgt = "%s/annot_version_%d_v2.%d.jpg" % (tempdir, eventDict['id'], sframe)

            shutil.move(src, tgt)
            attachments.append(tgt)
            saved.append(frame)

        # Delete the session file
        os.remove(session)

        # Submit the frames
        self.submit_note_attachments(attachments)

        # Update the graph to reflect which strokes have been submitted
        for frame in saved:
            for prop in props[frame]:
                rvc.newProperty(prop, rvc.IntType, 1)
                rvc.setIntProperty(prop, [1234], True) # XXX should be note id

    def set_media_type_property(self, source_group, media_type):
        setProp(source_group + ".cut_support.media_type", media_type)

    def get_media_type_of_source(self, source_group):
        return getStringProp(source_group + ".cut_support.media_type", None)

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
        Set the "cut_support.media_type" property of the source to
        match the current media type.
        """
        self._app.engine.log_info("set_media_of_source '%s' to '%s'" % 
            (source_group, media_type_name))

        current_media_type = self.get_media_type_of_source(source_group)

        if not version_data:
            version_data = self.version_data_from_source(source_group)

        m_type = self.media_type_fallback(version_data, media_type_name)
        # XXX warn if falling back

        if m_type and m_type != current_media_type: 
            path = version_data[standard_media_types[m_type].path_field]
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
        self._app.engine.log_info("swap_media_of_source '%s' to '%s'" % 
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
                    sources = []
                    for i in inputs:
                        if rvc.nodeType(i) == "RVSourceGroup":
                            sources.append(i)

                        # remove duplicates
                        sources = sorted(set(sources))

            for source in sources:
                self.swap_media_of_source(source, media_type_name)

        return swap_media

    def __init__(self, app):
        rvt.MinorMode.__init__(self)
        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138
        self._bundle = sgtk.platform.current_bundle()
        
        self.cuts_action = None
        self.note_dock = None
        self.tray_dock = None
        self.tab_widget = None
        self.mini_cut = False
        self.detail_version_id = None

        self.cached_mini_cut_data = MiniCutData(False)

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
                ('new_note_screenshot', self.make_note_attachments, ''),
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
                        ("View On Startup", None, None, lambda: rvc.DisabledMenuState),
                        ("    Details Pane",       self.toggle_startup_view_details, None, self.startup_view_details_state),
                        ("    Thumbnail Timeline", self.toggle_startup_view_tray,    None, self.startup_view_tray_state)
                        ]),
                    ("_", None)]
                )],
                None)
       
    def activate(self):
        rvt.MinorMode.activate(self)

    def deactivate(self):
        rvt.MinorMode.deactivate(self)
              

    ################################################################################### qt stuff down here. 

    def show_cuts_action(self, show=True):
        '''
        Adds a cuts clapper button to the far left of the RV toolbar.
        If show is false an attempt to remove any exisitng button is made.
        '''
        btb = rv.qtutils.sessionBottomToolBar()
        actions = btb.actions()
        text = "Enable Cuts"
        if show:
            cicon = QtGui.QIcon(":/tk-rv-shotgunreview/icon_player_cut_action_small_dark.png")
            self.cuts_action = QtGui.QAction(cicon, text, btb)
            self.cuts_action.triggered.connect(self.sample_cuts_action_listener)
            btb.insertAction(actions[0],self.cuts_action)
        else:
            if (actions[0].text() == text):
                btb.removeAction(actions[0])

    def enable_cuts_action(self, enable=True):
        '''
        Enables cuts toolbar button. If enable is false the button
        is disabled.
        '''
        self.cuts_action.setEnabled(enable)

    def sample_cuts_action_listener(self):
        '''
        Sample cuts toolbar button listener
        '''
        print("Clapper clicked!")

    def submit_note_attachments (self, attachments):
        '''
        Send the created and collected annotation exports off for saving
        '''
        self.details_panel.add_note_attachments(attachments)

    def load_data(self, entity):
        self._app.engine.log_info( "load_data with %r" % entity )
        self.version_id = entity['id']
        try:
            self._app.engine.log_info( "loading details panel with %r" % entity )
            self.details_panel.load_data(entity)
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
        self.details_panel = DetailsPanelWidget(self.note_dock)
        self.note_dock.setWidget(self.details_panel)
        
        self._app.engine._apply_external_styleshet(self._app, self.details_panel)

        self.tray_dock.setMinimumSize(QtCore.QSize(720,self._tray_height + 60))
        
        # ug, for now till i can clean up the methods
        from .tray_main_frame import TrayMainFrame
        self.tray_main_frame = TrayMainFrame(self.tray_dock)
        self.tray_main_frame.set_rv_mode(self)

        self.tray_hidden_this_session = False
        self.details_hidden_this_session = False

        # popup utils will try to handle all popup menu related things...
        self._popup_utils = PopupUtils(self)
        
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

        self.tray_main_frame.mini_right_spinner.valueChanged.connect(self.right_spinner_clicked)
        self.tray_main_frame.mini_left_spinner.valueChanged.connect(self.left_spinner_clicked)

        self.tray_button_entire_cut.clicked.connect(self.on_entire_cut)
        self.tray_button_mini_cut.clicked.connect(self.on_mini_cut)
        
        self.tray_model.filter_data_refreshed.connect(self.on_filter_refreshed)
        
        # self._popup_utils.related_cuts_ready.connect(self.create_related_cuts_from_models)

        # async cached request for pipeline steps.
        # XXX pipeline steps are 'global' to shotgun? so this only needs to happen once?
        self._popup_utils.get_pipeline_steps_with_model()

        self.details_timer = QTimer(rvqt.sessionWindow())
        self.note_dock.connect(self.details_timer, SIGNAL("timeout()"), self.check_details)
        self.details_timer.start(500)

        self.last_rel_cut_entity = None
        self.last_rel_shot_entity = None
        self.last_related_cuts = None

        self.tray_dock.setVisible(self._prefs.startup_view_tray)
        self.note_dock.setVisible(self._prefs.startup_view_details)

    def on_filter_refreshed(self, really_changed):
        self._app.engine.log_info("on_filter_refreshed: really_changed is %r" % really_changed)
        if really_changed:
            # XXX this will rely on self.target_entity still being set
            # correctly _and_ on us still looking at the corresponding node.
            # maybe we should be constructing a target_entity here from
            # whatever node we are looking at now ?   And not do anything if
            # it's not a Cut node, etc ...
            self.on_data_refreshed_internal(True, True)

    def right_spinner_clicked(self, event):
        self.on_mini_cut()

    def left_spinner_clicked(self, event):
        self.on_mini_cut()

    def get_version_from_id(self, id):
        self._app.engine.log_info('get_version_from_id %r' % QtCore.QThread.currentThread() )
        v_fields = [
            "sg_path_to_frames", "id",
            "sg_first_frame", "sg_last_frame",
            "sg_path_to_movie", "sg_movie_aspect_ratio",
            "sg_movie_has_slate", "sg_frames_aspect_ratio",
            "sg_frames_have_slate", "image", "code",
            "sg_uploaded_movie_frame_rate", "sg_uploaded_movie_mp4", 
        ]
        # get the version info we need
        version  = self._bundle.shotgun.find_one("Version", [["id", "is", id]], v_fields)
        if not version:
            self._app.engine.log_error('no version for id %r' % id)
            return None
        return self.convert_sg_dict(version)

    def on_id_from_gma(self, event):
        self._app.engine.log_info("on_id_from_gma  %r %r" % (event.contents(), QtCore.QThread.currentThread() ) )
        self.pinned_items = []
        self.version_swap_out = None
        self.no_cut_context = False
        self.tray_button_mini_cut.setStyleSheet('QPushButton { color: rgb(125,126,127); }')
        self.tray_button_entire_cut.setStyleSheet('QPushButton { color: rgb(255,255,255); }')

            
        target_entity = json.loads(event.contents())

        # XXX should check here that incoming server matches server to
        # which we are currently authenticated
        target_entity["server"] = self._app.tank.shotgun_url

        self.load_tray_with_something_new(target_entity)

        """
        except Exception as e:
            print "ERROR: on_id_from_gma %r" % e
            """

    def replace_version_in_sequence(self, versions):
        self._app.engine.log_info('replace_version_in_sequence %r' % QtCore.QThread.currentThread() )

        if len(versions) != 1:
            self._app.engine.log_error(
                "replace_version_in_sequence received %d versions!" % len(versions))
            return

        version_data = versions[0]
        seq_group = rvc.viewNode()

        if rvc.nodeType(seq_group) != "RVSequenceGroup":
            return

        seq_node      = groupMemberOfType(seq_group, "RVSequence")
        inputs        = rvc.nodeConnections(seq_group, False)[0]
        input_indices = rvc.getIntProperty(seq_node + ".edl.source")
        
        # make or find source group
        src_group = self.source_group_from_version_data(version_data)

        # Version/source of current clip is destination for this version, so
        # first find index of current clip 
        # XXX handle mini-cut.  
        clip_index = self.clip_index_from_frame()

        # replace input corresponding to input at clip index with new source
        inputs[input_indices[clip_index]] = src_group

        # reset inputs
        rvc.setNodeInputs(seq_group, inputs)

        # XXX handle pinning: note that more than one clip may be pinned as
        # result of the above.  Maybe pinning should be tracked by input ?

        # Details need to be updated
        self.details_dirty = True

        # XXX how does below pick up new thumbnail ?   Ans: it doesn't yet ..
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
        # shot_start = 0

        # ph_dict = self.load_version_id_from_session()
        # if ph_dict:            
        #     if 'ui_index' in ph_dict:
        #         self.pinned_items.append(ph_dict['ui_index'])
        for sgd in vlist:
            sg = self.convert_sg_dict(sgd)
            sg['pinned'] = 1
            f = self.get_media_path(sg)
            try:
                if f:
                    fk = sg['version.Version.id']
                    source_obj = {}   
                    if fk in self.loaded_sources:
                        source_obj = self.loaded_sources[fk]
                    else:
                        source_obj['source_name'] = rvc.addSourceVerbose([f])
                        source_obj['group_name'] = rvc.nodeGroup(source_obj['source_name'])
                        self.loaded_sources[fk] = source_obj
                    rve.setUIName(source_obj['group_name'], sg['version.Version.code'])
                
                else:
                    self._app.engine.log_info("load_sequence_with_versions: f is %r" % f)
                    continue
            except Exception as e:
                self._app.engine.log_error( "load_sequence_with_versions: %r" % e )

            source_prop_name = ("%s.cut_support.json_sg_data") % source_obj['group_name']
            try:
                if not rvc.propertyExists(source_prop_name):
                    rvc.newProperty(source_prop_name, rvc.StringType, 1)
                json_sg_item = json.dumps(sg)
                rvc.setStringProperty(source_prop_name, [json_sg_item], True)
            except Exception as e:
                self._app.engine.log_error("load_sequence_with_versions %r" % e)

            try:
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

            except Exception as e:
                self._app.engine.log_error("load_sequence_with_versions %r" % e)
        
        try:
            v_sources.append(0)
            v_ins.append(0)
            v_outs.append(0)
            v_frames.append(t)
      
            if self.want_stacked:
                if not self._stack_node:
                    self._stack_node = rvc.newNode('RVStackGroup')
                self._v_cut_seq_name = sg['version.Version.code']
                rve.setUIName(self._stack_node, self._v_cut_seq_name)     
                rvc.setNodeInputs(self._stack_node, v_source_names)
                rvc.setViewNode(self._stack_node)

            else:        
                if not self._layout_node:
                    self._layout_node = rvc.newNode("RVLayoutGroup")
                self._v_cut_seq_name = sg['version.Version.code']
                rve.setUIName(self._layout_node, self._v_cut_seq_name)
                rvc.setStringProperty("%s.layout.mode" % self._layout_node, ["grid"]);     
            
                rvc.setNodeInputs(self._layout_node, v_source_names)
                rvc.setViewNode(self._layout_node)

            # if ph_dict:
            #     if 'ui_index' in ph_dict:
            #         seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
            #         rvc.setIntProperty(seq_pinned_name, self.pinned_items, True)

            #         self.load_data(vlist[0])
            #         self.tray_list.repaint()
            # else:
            self.tray_dock.hide()
            self.tray_model.clear()
        except Exception as e:
            self._app.engine.log_error("load_sequence_with_versions %r" % e)

        # rvc.setFrame(shot_start + shot_offset)

    def load_tray_with_something_new(self, target_entity):

        # notify user we're loading ...
        type_string = target_entity["type"]
        if "ids" in target_entity and len(target_entity["ids"]) > 1:
            type_string += "s"
        rve.displayFeedback("Loading " + type_string +  " ...", 60.0)

        # XXX get rid of "id"
        if "id" in target_entity and "ids" not in target_entity:
            target_entity["ids"] = [ target_entity["id"] ]
        self.target_entity = target_entity

        t_type = target_entity["type"]

        if   t_type == "Version":
            self.load_tray_with_version_ids(target_entity["ids"])
            self.tray_main_frame.show_steps_and_statuses(False)
        elif t_type == "Playlist":
            self.load_tray_with_playlist_id(target_entity["ids"][0])
            self.tray_main_frame.show_steps_and_statuses(False)
        elif t_type == "Cut":
            self.load_tray_with_cut_id(target_entity["ids"][0])
            self.tray_main_frame.show_steps_and_statuses(True)
        else:
            self._app.engine.log_error("Tray does not support entity type '%s'." % t_type)
        
    def load_tray_with_version_ids(self, ids):
        vfilters = [["id", "in", ids]]
        vfields =  [ "project", "playlists", "image" ] + required_version_fields
        self.tray_model.load_data(entity_type="Version", filters=vfilters, fields=vfields)

    def load_tray_with_playlist_id(self, playlist_id=None):
        plist_filters = [["playlists", "is", {"type": "Playlist", "id": playlist_id}]]
        plist_fields =  [ "project", "playlists", "image" ] + required_version_fields
        self.tray_model.load_data(entity_type="Version", filters=plist_filters, fields=plist_fields)

    def load_tray_with_cut_id(self, cut_id=None):
        self._app.engine.log_info('load_tray_with_cut_id %r' % QtCore.QThread.currentThread() )

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
        
        # XXX figure this out
        # if self.mini_cut:
        #     self.on_entire_cut()

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

        self.load_mini_cut(index, offset)

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

    def set_session_prop(self, name, item):
        self._app.engine.log_info('set_session_prop %r' % QtCore.QThread.currentThread() )
        
        try:
            if not rvc.propertyExists(name):
                rvc.newProperty(name, rvc.StringType, 1)
            cut_json = json.dumps(item)
            rvc.setStringProperty(name, [cut_json], True)
        except Exception as e:
            print "ERROR: set_session_prop %r" % e

    def convert_sg_dict(self, sg_dict):
        if not sg_dict:
            self._app.engine.log_error('EMPTY dict passed to convert_sg_dict.')
            return sg_dict

        #sg_dict_new = copy.copy(sg_dict)
        if not 'version.Version.sg_path_to_frames' in sg_dict:

            f = [   "version.Version.sg_path_to_frames", "version.Version.id",
                    "version.Version.sg_first_frame", "version.Version.sg_last_frame",
                    "version.Version.sg_path_to_movie", "version.Version.sg_movie_aspect_ratio",
                    "version.Version.sg_movie_has_slate", "version.Version.sg_frames_aspect_ratio",
                    "version.Version.sg_frames_have_slate", "version.Version.image", "version.Version.code",
                    "version.Version.sg_uploaded_movie_frame_rate", "version.Version.sg_uploaded_movie_mp4", 
                ]

            for k in f:
                s = k.replace('version.Version.', '')
                if s in sg_dict:
                    sg_dict[k] = sg_dict[s]

        # check for missing media

        return sg_dict

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
                source_name = rvc.addSourceVerbose([f])
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
                source_name = rvc.addSourceVerbose([s])

            group_name = rvc.nodeGroup(source_name)

            if sg_item['version.Version.code']:
                rve.setUIName(group_name, sg_item['version.Version.code'])
            
            self.loaded_sources[fk] = {}
            self.loaded_sources[fk]['group_name'] = group_name
            self.loaded_sources[fk]['source_name'] = source_name
            self.loaded_sources[fk]['source_index'] = source_incr

            if 'movieproc' in f:
                # group_name returned an empty list here. source name works.
                overlays = rve.associatedNodes("RVOverlay",source_name)
                # node need to be a component name ...
                self.createText(overlays[0] + '.text:mytext', sg_item['version.Version.code'] + '\nis missing.', -0.5, 0.0)
            return True

    def sequence_group_from_target(self, target_entity, subTarget):
        """
        We keep a RVSequenceGroup around to represent each Playlist, and two
        for each Cut (one for entire-cut and one for min-cut).
        """
        # XXX handle subTarget, target_entity["server"]

        t_type = target_entity["type"]
        t_id   = target_entity["ids"][0]

        for s in rvc.nodesOfType("RVSequenceGroup"):
            # for Playlist and Cut, we stick with one Sequence node per entity.
            # But for the "scratch" usage of playing arbitrary group of
            # Versions, we just re-use a single sequence.
            if ( getStringProp(s + ".cut_support.target_type", None) == t_type and
                (getIntProp   (s + ".cut_support.target_id",   None) == t_id or 
                 t_type == "Version")):
                return s

        # We failed to find our RVSequenceGroup, so make one.

        s = rvc.newNode("RVSequenceGroup")

        setProp(s + ".cut_support.target_type", t_type)

        if (t_type != "Version"):
            setProp(s + ".cut_support.target_id",   t_id)

        return s

    def check_media_contents(self, path):

        if not path:
            return False

        files = rvc.existingFilesInSequence(path)
        
        return bool(files)

    def media_type_fallback(self, version_data, media_type):
        
        path = version_data.get(standard_media_types[media_type].path_field)

        if self.check_media_contents(path):
            return media_type

        other = "Movie" if (media_type == "Frames") else "Frames"
        path = version_data.get(standard_media_types[other].path_field)

        if self.check_media_contents(path):
            return other

        return None
            
    def find_group_from_version_id(self, version_id):

        group = None
        for s in rvc.nodesOfType("RVSourceGroup"):
            if getIntProp(s + ".cut_support.version_id", -1) == version_id:
                # XXX we should be storing/checking url too
                # XXX possibly this version data is stale, think about when we
                # might refresh ?
                group =  s

        return group

    def source_group_from_version_data(self, version_data, media_type=None):

        if (False):
            print "source_group_from_version_data() data:"
            pp.pprint(version_data)

        source_group = self.find_group_from_version_id(version_data["id"])
        if source_group:
            return source_group

        # We failed to find our RVSourceGroup, so make one.

        if media_type is None:
            media_type = self._prefs.preferred_media_type

        path = None
        m_type = self.media_type_fallback(version_data, media_type)
        if m_type: 
            path = version_data[standard_media_types[m_type].path_field]

        if not path:
            self._app.engine.log_error("Version '%s' has no local media" % version_data["code"])
            path = "black,start=1,end=24.movieproc"
            m_type = "Movie"

        try:
            source_node = rvc.addSourceVerbose([path])
        except:
            # XXX
            return

        source_group = rvc.nodeGroup(source_node)

        setProp(source_group + ".cut_support.version_id",   version_data["id"])
        setProp(source_group + ".cut_support.version_data", json.dumps(version_data))

        self.set_media_type_property(source_group, m_type)

        self.configure_source_media(source_group, version_data)

        rve.setUIName(source_group, version_data["code"])

        return source_group

    def sequence_data_from_query_item(self, sg_item, target_entity):
        data = {}

        data["target_entity"] = target_entity
        data["ui_name"]       = target_entity["type"]
        data["entity"]        = "No Entity"
        data["project"]       = "No Project"

        if   target_entity["type"] == "Cut":
            if sg_item:
                data["ui_name"] = sg_item["cut.Cut.cached_display_name"]
                data["entity"]  = sg_item["cut.Cut.entity"]

        elif target_entity["type"] == "Playlist":
            data["ui_name"]     = "Playlist %d" % target_entity["ids"][0]

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
        json_str = getStringProp(rvc.viewNode() + ".cut_support.sequence_data", None)
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

        return (version_data, edit_data)

    def data_from_version(self, sg):

        version_data = sg
        edit_data = {}
        edit_data["in"]  = sg.get("sg_first_frame", 1)
        edit_data["out"] = sg.get("sg_last_frame",  100)
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

    # signal from model so filter_query_finished is False (we need to run follow-on
    # query, if any)
    def on_data_refreshed(self, was_refreshed):
        self.on_data_refreshed_internal(was_refreshed, False)
        
    # the way data from shotgun gets into the tray
    def on_data_refreshed_internal(self, was_refreshed, filter_query_finished):
        """
        The tray_model has one item per clip in sequence; each clip's data
        comes from a CutItem (when loading a Cut) or straight from a Version
        (when loading a Playlist).
        """
        rows = self.tray_proxyModel.rowCount()
        if False:
            print "--------------------------------------- on_data_refreshed_internal() filter_query_finished", filter_query_finished, "rows", rows
            for index in range(0, rows):
                item = self.tray_proxyModel.index(index, 0)
                sg_item = shotgun_model.get_sg_data(item)
                rv_item = item.data(self._RV_DATA_ROLE)
                print "--------------------------------------- sg_item"
                pp.pprint(sg_item)
                print "--------------------------------------- rv_item"
                pp.pprint(rv_item)
            # return
        self._app.engine.log_info('on_data_refreshed_internal: %r' % str(QtCore.QThread.currentThread()))

        # Show GUI unless the user has explicitly hidden it this session
        if not self.tray_hidden_this_session:
            self.tray_dock.setVisible(True)
        if not self.details_hidden_this_session:
            self.note_dock.setVisible(True)

        # XXX eventually we want to enter min-cut mode directly in some cases,
        # in which case we want to start with corresponding Sequence node.
        subTarget = "entire-cut" # XXX should come from pref or previous run

        # we rely on tray selection being synced with frame
        (old_index, old_offset) = self.clip_index_and_offset_from_frame()

        # find or make RV sequence node for this target entity
        seq_group_node = self.sequence_group_from_target(self.target_entity, subTarget)
        seq_node = groupMemberOfType(seq_group_node, "RVSequence")

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

            # Now we have version data, find or create the corresponding
            # RVSourceGroup
            src_group = self.source_group_from_version_data(version_data)

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
            # self._popup_utils.set_project(self.project_entity)
        self._popup_utils.build_status_menu(self.project_entity)

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

        setProp(seq_node + ".shadow_edl.source", edl_source_nums)
        setProp(seq_node + ".shadow_edl.frame",  edl_frames)
        setProp(seq_node + ".shadow_edl.in",     edl_ins)
        setProp(seq_node + ".shadow_edl.out",    edl_outs)

        setProp(seq_group_node + ".cut_support.sequence_data", json.dumps(sequence_data))
        setProp(seq_group_node + ".cut_support.edit_data", edit_data_list)


        mini_data = MiniCutData.load_from_session(seq_node)
        if mini_data.active:
            # XXX no need ?
            # rvc.setViewNode(seq_group_node)
            f = rvc.frame()
            self.load_mini_cut(mini_data.focus_clip - mini_data.first_clip, 0)
            rvc.setFrame(f)
        else:
            # XXX 
            setProp(seq_node + ".edl.source", edl_source_nums)
            setProp(seq_node + ".edl.frame",  edl_frames)
            setProp(seq_node + ".edl.in",     edl_ins)
            setProp(seq_node + ".edl.out",    edl_outs)

            rvc.setNodeInputs(seq_group_node, seq_inputs)

            rvc.setViewNode(seq_group_node)

        # XXX
        ## if we had a selection coming in, we move to that
        ## not sure if these even works EXAMINE
        #if final_selection:
        #    self.tray_list.selectionModel().select(final_selection, self.tray_list.selectionModel().ClearAndSelect)
        #else:            
        #    zero_index = self.tray_model.createIndex(0, 0)
        #    self.tray_list.selectionModel().select(zero_index, self.tray_list.selectionModel().ClearAndSelect)
        #
        #self.tray_list.scrollTo(self.tray_proxyModel.index(0, 0), QtGui.QAbstractItemView.EnsureVisible)

        # XXX manage pinned_items for sequence
        # seq_pinned_name = ("%s.cut_support.pinned_items") % self.cut_seq_name
        # if not rvc.propertyExists(seq_pinned_name):
        #     rvc.newProperty(seq_pinned_name, rvc.IntType, 1)
        # rvc.setIntProperty(seq_pinned_name, self.pinned_items, True)

        # filter query logic
        # 
        # Test here if we need to run filtering query automatically. IE if we
        # have non-trivial filtering parameters and filter_query_finished is
        # false (because we are not _responding_ to a filter update).  If so,
        # initiate that query.  If not, display completion feedback 

        filter_query_required = self._popup_utils.filters_exist()
        if (not filter_query_finished and filter_query_required):
            # trigger filter query
            self._popup_utils.request_versions_for_statuses_and_steps(True)
        else :
            rve.displayFeedback("Loading complete", 2.0)

        # highlight the first clip
        self.frameChanged(None)

        if self.target_entity["type"] == "Cut":
            # self.create_related_cuts_menu(sequence_data["entity"], None)
            self._popup_utils.request_related_cuts_from_models()
        else:
            if self.related_cuts_menu:
                self.related_cuts_menu.clear()

        #self._popup_utils.build_status_menu()

    def edit_data_from_session(self):
        data = None

        seq_group = rvc.viewNode()

        if rvc.nodeType(seq_group) == "RVSequenceGroup":
            edit_prop = seq_group + ".cut_support.edit_data"
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
        return (
            self.tray_main_frame.mini_left_spinner.value(), 
            self.tray_main_frame.mini_right_spinner.value())

    def load_mini_cut(self, focus_index, offset=0):

        self._app.log_info("load_mini_cut() focus %d offset %d" % (focus_index, offset))

        seq_node = None
        seq_group = rvc.viewNode()
        if rvc.nodeType(seq_group) == "RVSequenceGroup":
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
        accumulated_frames = 1

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




