
import json
import tank

from tank.platform.qt import QtCore, QtGui

task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

from .filter_steps_model import FilterStepsModel
from .rel_cuts_model import RelCutsModel
from .rel_shots_model import RelShotsModel
from .filtered_versions_model import FilteredVersionsModel
from .steps_sort_filter import StepsSortFilter

import rv.extra_commands as rve

import pprint
pp = pprint.PrettyPrinter(indent=4)

# XXX not sure how to share this? copied from the mode
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


class PopupUtils(QtCore.QObject):

    related_cuts_ready = QtCore.Signal()

    def __init__(self, rv_mode):
        QtCore.QObject.__init__(self)
        self._engine = rv_mode._app.engine
        self._shotgun = rv_mode._bundle.shotgun
        self._project_entity = rv_mode.project_entity
        self._sequence_cuts = []
        self._sequence_entity = None
        self._shot_steps = None
        self._status_schema = None
        self._tray_frame = rv_mode.tray_main_frame
        self._status_menu = None
        self._status_list = []
        self._rv_mode = rv_mode
        self._pipeline_steps_menu = None
        self._pipeline_steps = None
        self._related_cuts_menu = None
        self._last_related_cuts = None
        self._last_rel_shot_entity = None
        self._last_rel_cut_entity = None
        self._last_rel_version_id = -1
        self._last_rel_cut_id = -1

        self._query_ip = False

        # sequence data IS UPDATED too late for us, so this tells us intent for related 
        # cuts menu loading or clearing.
        self._target_entity = None

        self._RV_DATA_ROLE = QtCore.Qt.UserRole + 1138
        self._CUT_THUMB_ROLE = QtCore.Qt.UserRole + 1701


        # models
        self._steps_model = FilterStepsModel(None, self._rv_mode._app.engine.bg_task_manager)
        self._steps_proxyModel =  StepsSortFilter(None)
        self._steps_proxyModel.setSourceModel(self._steps_model)

        self._rel_cuts_model = RelCutsModel(None, self._rv_mode._app.engine.bg_task_manager)
        self._rel_shots_model = RelShotsModel(None, self._rv_mode._app.engine.bg_task_manager)
        
        self._filtered_versions_model = FilteredVersionsModel(None, self._rv_mode._app.engine.bg_task_manager, self._tray_frame.tray_model)

        # connections
        
        self._rel_cuts_model.data_refreshed.connect(self.on_rel_cuts_refreshed)
        self._rel_shots_model.data_refreshed.connect(self.on_rel_shots_refreshed)
        
        self._steps_model.data_refreshed.connect(self.handle_pipeline_steps_refreshed)
        self.related_cuts_ready.connect(self.create_related_cuts_from_models)

        self._filtered_versions_model.data_refreshed.connect(self.filter_tray)

    # related cuts menu menthods

    def get_status(self):
        if self._incoming_status:
            return self._incoming_status
        return self._status_list

    def set_status(self, incoming_json):
        incoming_status = json.loads(incoming_json)
        self._incoming_status = incoming_status

    def get_pipeline(self):
        if self._incoming_pipeline != None:
            return self._incoming_pipeline
        return self._pipeline_steps

    def set_pipeline(self, incoming_json):
        incoming_pipeline = json.loads(incoming_json)
        self._incoming_pipeline = incoming_pipeline
        self._preset_pipeline = True
        self.check_pipeline_menu()

    def find_rel_cuts_with_model(self, entity_in, shot_entity=None):
        """
        This initiates two queries, one for all related cuts, and the other
        for all related cuts that the shot_entity is in.
        
        XXX we might call this without the shot_entity if we are playing?
        """
        # conditions is an array, with 3 vals
        # [ <field>, 'is', dict ]
        # ['entity', 'is', {'type': 'Sequence', 'id': 31, 'name': '08_a-team'}]
        # ['cut_items.CutItem.shot', 'is', {'type': 'Shot', 'id': 1237}]
        self._rel_cuts_done = False
        self._rel_shots_done = False
        self._query_ip = True

        conditions = ['entity', 'is', entity_in]
        if self._project_entity and self._project_entity['id']:
            cut_filters = [ conditions, ['project', 'is', { 'id': self._project_entity['id'], 'type': 'Project' } ]]
        else:
            cut_filters = [ conditions ]
        cut_fields = ['id', 'entity', 'code', 'cached_display_name']
        cut_orders = [
            {'field_name': 'code', 'direction': 'asc'}, 
            {'field_name': 'cached_display_name', 'direction': 'asc'}
            ]
        self._rel_cuts_model.load_data(entity_type="Cut", filters=cut_filters, fields=cut_fields, order=cut_orders)        

        if not shot_entity:
            # XXX if there is no shot, then clear the shot model and set the shots done
            self._rel_shots_model.clear()
            self._rel_shots_done = True
            return

        shot_conditions = ['cut_items.CutItem.shot', 'is', { 'id': shot_entity['id'], 'type': 'Shot' }]
        shot_filters = [ shot_conditions, ['project', 'is', { 'id': self._project_entity['id'], 'type': 'Project' } ]]
        shot_fields = ['id', 'entity', 'code', 'cached_display_name']
        shot_orders = [
            {'field_name': 'code', 'direction': 'asc'}, 
            {'field_name': 'cached_display_name', 'direction': 'asc'}
            ]

        self._rel_shots_model.load_data(entity_type="Cut", filters=shot_filters, fields=shot_fields, order=shot_orders)        
        #self._related_timer.start(20)

    def request_related_cuts_from_models(self):
        """
        this method is called at aboutToShow time by the menu button
        """
        
        seq_data = self._rv_mode.sequence_data_from_session()

        if (not seq_data or seq_data["target_entity"]["type"] != "Cut"):
            self._engine.log_warning('request_related_cuts_from_models: No cut info available')
            self.clear_rel_cuts_menu(remove_menu=True)
            return

        cut_link = seq_data['entity']
        cut_id   = seq_data["target_entity"]["ids"][0]

        version_data = self._rv_mode.version_data_from_source()
        # this probably shouldnt happen but seeing it when erroring on robustness tests
        if not version_data:
            self._engine.log_warning("request_related_cuts_from_models - No version data found in session.")
            self.clear_rel_cuts_menu(remove_menu=True)
            return

        # if this is the same as last time, then we can bail, its already rebuilt.
        # pp.pprint(version_data)
        # print "actions: %d" % len(self._related_cuts_menu.actions())
        if self._last_rel_version_id == version_data['id'] and self._last_rel_cut_id == cut_id and self._related_cuts_menu and len(self._related_cuts_menu.actions()) > 0:
           self._engine.log_warning('still on version %d, not rebuilding rel cuts menu' % version_data['id'])
           return
        
        self._last_rel_version_id = version_data['id']
        self._last_rel_cut_id = cut_id

        if version_data:
            # mix in second related shots
            version_link = version_data['entity']
            if version_link:
                # version_link might not be a Shot (because version is
                # base-layer, etc)
                if version_link['type'] != "Shot":
                    version_link = None

                # XXX does this allow for cut_link == None ?
                # XXX no it doesnt, what do we do with a cut with no entity link? - sb
                if cut_link != self._last_rel_cut_entity or version_link != self._last_rel_shot_entity:
                    self.find_rel_cuts_with_model(cut_link, version_link)
                    self._last_rel_cut_entity = cut_link
                    self._last_rel_shot_entity = version_link
                    return
                else:
                    # we already have it cached.
                    if not self._query_ip:
                        self.related_cuts_ready.emit()
                    return

        # XXX don't get this ? -- alan
        # XXX is this another impossible workflow? - sb.
        if cut_link['type'] == "Scene":
            self._engine.log_warning("cant find relative cuts for a scene? using shot linked to version?")
            if version_link:
                self.find_rel_cuts_with_model(cut_link, version_link['shot'])
            return

    def handle_related_menu(self, action=None):
        self._engine.log_info("handle_related_menu called with action %r" % action)
        if action and action.data():
            self._engine.log_info("action.data: %r" % action.data()) 
            self._rv_mode.load_tray_with_something_new(
                {"type":"Cut", "ids":[action.data()['id']]}, 
                preserve_pinned=True,
                preserve_mini=True)

    def on_rel_cuts_refreshed(self):
        self._rel_cuts_done = True
        if self._rel_cuts_done and self._rel_shots_done:
            self._rel_shots_done = False
            self._rel_cuts_done = False
            self._query_ip = False
            self.related_cuts_ready.emit()

    def on_rel_shots_refreshed(self):
        self._rel_shots_done = True
        if self._rel_cuts_done and self._rel_shots_done:
            self._rel_shots_done = False
            self._rel_cuts_done = False
            self._query_ip = False
            self.related_cuts_ready.emit()
        
    # def set_project(self, entity):
    #     # XXX invalidate queries? auto-load status? 
    #     self._project_entity = entity


    def merge_rel_models_for_menu(self):
        """
        - examine the contents of the shot model and build a map keyed on related shot cut id,
          and an array of related shot cut ids.
        - build an array from the contents of the cuts model,
          and an array of cut ids.
        - if there are ids in the related shots model not present in the related cuts, add them.
        - sort the merged cuts array by the 'cached_display_name' field.
        - examine the sorted array for duplicate 'code' fields. this indicates that several cuts
          are 'revisions' and need to be grouped by this code. add a 'count' column to the dict
          so that the menu creation code can group these together in a sub-menu.
        """
        shot_map = {}
        shot_ids = []

        shot_rows = self._rel_shots_model.rowCount()
        if shot_rows:
            for x in range( 0, shot_rows ):
                item = self._rel_shots_model.index(x, 0)
                sg = shotgun_model.get_sg_data(item)
                shot_ids.append(sg['id'])
                shot_map[sg['id']] = sg
        
        seq_ids = []
        cut_rows = self._rel_cuts_model.rowCount()
        seq_cuts = []
        for x in range(0, cut_rows):
            item = self._rel_cuts_model.index(x, 0)
            sg = shotgun_model.get_sg_data(item)  
            seq_ids.append(sg['id'])
            seq_cuts.append(sg)
        for n in shot_ids:
            if n not in seq_ids:
                seq_cuts.append(shot_map[n])

        sorted_cuts = sorted(seq_cuts, key=lambda x: x['cached_display_name'].lower(), reverse=False)
 
        dup_map = {}
        for x in sorted_cuts:
            if x['code'] not in dup_map:
                dup_map[x['code']] = 1
            else:
                dup_map[x['code']] = dup_map[x['code']] + 1
        for x in sorted_cuts:
            x['count'] = dup_map[x['code']]

        return sorted_cuts
 
    def clear_rel_cuts_menu(self, remove_menu=False, target_entity=None):
        
        if target_entity and (target_entity['type'] == "Version" or target_entity['type'] == "Playlist"):
            self._target_entity = target_entity
        else:
            self._target_entity = None

        if self._related_cuts_menu:
            self._related_cuts_menu.clear()
            self._last_related_cuts = None
        if remove_menu:
            self._related_cuts_menu = None
            self._tray_frame.tray_button_browse_cut.setMenu(self._related_cuts_menu) 

    def create_related_cuts_from_models(self):
        if not self._related_cuts_menu and not self._target_entity:
            self._engine.log_info("create_related_cuts_from_models, CREATING MENU")
            self._related_cuts_menu = QtGui.QMenu(self._tray_frame.tray_button_browse_cut)
            self._tray_frame.tray_button_browse_cut.setMenu(self._related_cuts_menu)        
 
            # Sadly, because this button didn't have a menu at the time that
            # the app-level styling was applied, it won't inherit menu-indicator
            # styling there. We have to set it here as a result.
            self._tray_frame.tray_button_browse_cut.setStyleSheet(
                """QPushButton::menu-indicator {
                        image: url(:tk-rv-shotgunreview/arrow.png);
                        subcontrol-position: right center;
                        subcontrol-origin: padding;
                        width: 10px;
                        right: -2px;
                        top: -1px;
                    }
                """
            )
            self._related_cuts_menu.triggered.connect(self.handle_related_menu)
            # self._related_cuts_menu.aboutToShow.connect(self.handle_related_menu)
        else:
            # if we have a menu, and target_entity is None, then we are moving from
            # cut to cut. if no menu and there is a target, then its a version or
            # playlist so we can bail.
            if not self._related_cuts_menu:
                return

        seq_data = self._rv_mode.sequence_data_from_session()
        cut_id = seq_data["target_entity"]["ids"][0] if seq_data else None
        
        self._engine.log_info("create_related_cuts_from_models, cut_id: %r" % cut_id)

        seq_cuts = self.merge_rel_models_for_menu()
        #  pp.pprint(seq_cuts)
        if seq_cuts == self._last_related_cuts:
            actions = self._related_cuts_menu.actions()
            for a in actions:
                a.setChecked(False)
                x = a.data()
                if x:
                    if x['id'] == cut_id:
                        a.setChecked(True)

                if a.menu(): # as in a sub-menu
                    a.setChecked(False)
                    sub_acts = a.menu().actions()
                    for b in sub_acts:
                        b.setChecked(False)
                        bd = b.data()
                        if bd['id'] == cut_id:
                            b.setChecked(True)
                            a.setChecked(True)
            self._engine.log_warning("create_related_cuts_from_models, updating check marks only, %d" % len(seq_cuts) )

            return

        self._last_related_cuts = seq_cuts
        self._related_cuts_menu.clear()

        menu = self._related_cuts_menu
        action = QtGui.QAction(self._tray_frame.tray_button_browse_cut)
        action.setText('Related Cuts')
        menu.addAction(action)
        menu.addSeparator()

        last_menu = menu
        parent_menu = None
        last_code = None
        en = {}
        self._engine.log_info("create_related_cuts_from_models, seq_cuts: %r" % len(seq_cuts))

        for x in seq_cuts:
            action = QtGui.QAction(self._tray_frame.tray_button_browse_cut)
            action.setCheckable(True)
            action.setChecked(False)
            en['id'] = x['id']
            en['type'] = 'Cut'

            if last_code != x['code']: # this is the first time weve seen this code
                if x['count'] > 1: # make a submenu
                    last_menu = last_menu.addMenu(x['code'])
                    a = last_menu.menuAction()
                    a.setCheckable(True)
                    a.setChecked(False)
                    parent_menu = last_menu
                else:
                    last_menu = menu
                    parent_menu = None
 
            if x['id'] == cut_id:
                action.setChecked(True)
                if parent_menu:
                    a = parent_menu.menuAction()
                    a.setCheckable(True)
                    a.setChecked(True)
            else:
                action.setChecked(False)
 
            if last_menu == menu:
                action.setText(x['code'])
            else:
                action.setText(x['cached_display_name'])

            action.setData(en)
 
            last_menu.addAction(action)
            last_code = x['code']

        self._engine.log_info("DONE create_related_cuts_from_models, cut_id: %r" % cut_id)

    # approval status menu methods

    def get_status_list(self, project_entity=None):
        """
        This query needs to be run only when the project changes.
        We cache the last query in memory.
        """
        # XXX - cache all queries in a map for bouncing between projects?
        if not project_entity:
            project_entity = self._project_entity

        if project_entity == 'No Project':
            self._engine.log_error('received %r for project_entity' % project_entity)
            return None

        if not self._status_schema or project_entity['id'] != self._project_entity['id']:
            self._project_entity = project_entity
            # print "PROJECT  %r" % project_entity
            project_id = self._project_entity['id']
            self._status_schema = self._shotgun.schema_field_read('Version', field_name='sg_status_list', project_entity={ 'id': project_id, 'type': 'Project' } )
                
        return self._status_schema

    def get_status_menu(self, project_entity=None):
        """
            status_schema is a large, complicated dictionary of dictionaries.
            this method extracts the bits we are interested in, and builds
            a list of them. 
            below are some examples of interesting things in the schema:
        """
        #print "status_list: %r\n\n" % self._status_schema
        # print "properties: %r" % self._status_schema['sg_status_list']['properties']
        # print "values: %r" % self._status_schema['sg_status_list']['properties']['valid_values']['value']
        # for x in self._status_schema['sg_status_list']:
            #print "%r" % x
        #print "display: %r\n\n" % self._status_schema['sg_status_list']['properties']['display_values']
        
        s = self.get_status_list(project_entity)
        d = s['sg_status_list']['properties']['display_values']['value']
        ordered_list = s['sg_status_list']['properties']['valid_values']['value']

        status_list = []

        for n in ordered_list:
            e = {}
            e[n] = d[n]            
            status_list.append(e)

        return status_list

    def build_status_menu(self, project_entity=None):

        # might as well make the menu if its not there yet.
        if not self._status_menu:
            self._status_menu = QtGui.QMenu(self._tray_frame.status_filter_button)
            self._tray_frame.status_filter_button.setMenu(self._status_menu)

            # Sadly, because this button didn't have a menu at the time that
            # the app-level styling was applied, it won't inherit menu-indicator
            # styling there. We have to set it here as a result.
            self._tray_frame.status_filter_button.setStyleSheet(
                """QPushButton::menu-indicator {
                        image: url(:tk-rv-shotgunreview/arrow.png);
                        subcontrol-position: right center;
                        subcontrol-origin: padding;
                        width: 10px;
                        right: -2px;
                        top: -1px;
                    }
                """
            )       
            self._status_menu.triggered.connect(self.handle_status_menu)

        # theres nothing we can do without getting a project entity.
        if not project_entity:
            self._engine.log_warning('no project entity set.')
            return

        # no need to rebuild if its the same project
        if self._project_entity:
            if project_entity['id'] == self._project_entity['id']:
                return

        # we have a new project! build the menu for reals.
        self._project_entity = project_entity
        menu = self._status_menu
        menu.clear()
        action = QtGui.QAction(self._tray_frame.status_filter_button)
        action.setCheckable(True)
        action.setChecked(False)
        action.setText('Any Status')
        action.setData(None)
        menu.addAction(action)
        menu.addSeparator()
        self._status_reload = False

        statii = self.get_status_menu(self._project_entity)
        count = 0
        name = None
        for status in statii:
            action = QtGui.QAction(self._tray_frame.status_filter_button)
            action.setCheckable(True)
            for x in status:
                action.setText(status[x])
                if x in self._incoming_status:
                    action.setChecked(True)
                    count = count + 1
                    name = status[x]
            action.setData(status)
            menu.addAction(action)

        if count == 0:
            self._tray_frame.status_filter_button.setText("Filter by Status")
        if count == 1:
            self._tray_frame.status_filter_button.setText(name)
        if count > 1:
            self._tray_frame.status_filter_button.setText("%d Statuses" % count)
       

    def handle_status_menu(self, event):
        # if 'any status' is picked, then the other
        # choices are zeroed out. event.data will be None for any status

        if self._incoming_status:
            self._status_list = self._incoming_status
        else:
            self._status_list = []
        
        actions = self._status_menu.actions()
        if not event.data():
            for a in actions:
                a.setChecked(False)
            self._status_list = []
            self._tray_frame.status_filter_button.setText("Filter by Status")
            self.request_versions_for_statuses_and_steps()
            return

        name = 'Error'
        count = 0
 
        for a in actions:
            if a.isChecked():
                e = a.data()
                for k in e:
                    self._status_list.append(k)
                    name = e[k]
                    count = count + 1
 
        if count == 0:
            self._tray_frame.status_filter_button.setText("Filter by Status")
        if count == 1:
            self._tray_frame.status_filter_button.setText(name)
        if count > 1:
            self._tray_frame.status_filter_button.setText("%d Statuses" % count)
        
        self.request_versions_for_statuses_and_steps()

    # pipeline steps menu

    def get_pipeline_steps_with_model(self):
        step_filters = [['entity_type', 'is', 'Shot' ]]
        step_fields = ['code', 'list_order', 'short_name', 'id', 'cached_display_name']
        step_orders = [ {'field_name': 'list_order', 'direction': 'desc'} ]
        self._steps_model.load_data(entity_type="Step", filters=step_filters, fields=step_fields, order=step_orders)        

    def handle_pipeline_steps_refreshed(self, refreshed):
        """
        This loads the menu with values returned when the _steps_model returns data_refreshed
        """
        if not self._pipeline_steps_menu:
            self._pipeline_steps_menu = QtGui.QMenu(self._tray_frame.pipeline_filter_button)
            self._tray_frame.pipeline_filter_button.setMenu(self._pipeline_steps_menu)

            # Sadly, because this button didn't have a menu at the time that
            # the app-level styling was applied, it won't inherit menu-indicator
            # styling there. We have to set it here as a result.
            self._tray_frame.pipeline_filter_button.setStyleSheet(
                """QPushButton::menu-indicator {
                        image: url(:tk-rv-shotgunreview/arrow.png);
                        subcontrol-position: right center;
                        subcontrol-origin: padding;
                        width: 10px;
                        right: -2px;
                        top: -1px;
                    }
                """
            )      
            self._pipeline_steps_menu.triggered.connect(self.handle_pipeline_menu)
        menu = self._pipeline_steps_menu
        menu.clear()

        action = QtGui.QAction(self._tray_frame.pipeline_filter_button)
        action.setCheckable(False)
        action.setChecked(False)
        action.setText('Pipeline Steps Priority')
        # XXX what object do we want here?
        action.setData( None )
        menu.addAction(action)
        menu.addSeparator()

        # XXX latest in pipeline means an empty steps list?
        action = QtGui.QAction(self._tray_frame.pipeline_filter_button)
        action.setCheckable(True)
        action.setChecked(False)
        action.setText('Latest in Pipeline')
        # XXX what object do we want here?
        action.setData( { 'cached_display_name' : 'Latest in Pipeline' } )
        menu.addAction(action)
        self._steps_proxyModel.sort(0, QtCore.Qt.DescendingOrder)
        rows = self._steps_proxyModel.rowCount()

        for x in range(0, rows):
            item = self._steps_proxyModel.index(x, 0)
            sg = shotgun_model.get_sg_data(item)
            action = QtGui.QAction(self._tray_frame.pipeline_filter_button)
            action.setCheckable(True)
            action.setChecked(False)
            action.setText(sg['cached_display_name'])
            action.setData(sg)
            menu.addAction(action)

        self.check_pipeline_menu()


    def check_pipeline_menu(self):
        if not self._pipeline_steps_menu:
            return
        # once we get here we only want to run this once
        if not self._preset_pipeline:
            return
        else:
            if self._incoming_pipeline == "None":
                return
            if self._incoming_pipeline == None:
                return
            # chcek the incoming values
            actions = self._pipeline_steps_menu.actions()
            count = 0
            name = None
            tmp_incoming = []
            if self._incoming_pipeline == []:
                e = {}
                e['cached_display_name'] = "Latest in Pipeline"
                tmp_incoming.append(e)
            else:
                tmp_incoming = self._incoming_pipeline

            for a in actions:
                if a.data():
                    for x in tmp_incoming:
                        if a.data()['cached_display_name'] == x['cached_display_name']:
                            a.setChecked(True)
                            name = a.data()['cached_display_name']
                            count = count + 1
            if count == 0:
                self._tray_frame.pipeline_filter_button.setText("Filter by Pipeline")
            if count == 1:
                self._tray_frame.pipeline_filter_button.setText(name)
            if count > 1:
                self._tray_frame.pipeline_filter_button.setText("%d steps" % count)

        self._preset_pipeline = False
    

    def handle_pipeline_menu(self, event):
        """
        This is run after the user makes a selection in the Pipeline Steps menu
        """
        # you only get the latest one clicked here. there could be more.
        # you might also get a roll off event that you dont want.
        # so check the widget and then update the button text

        want_latest = False
        if event.data():
            e = event.data()
            if e['cached_display_name'] == 'Latest in Pipeline':
                want_latest = True
                if not event.isChecked():
                    want_latest = False
        
        actions = self._pipeline_steps_menu.actions()
        count = 0
        name = 'Error'
        # for later filtering, None tells us no step is selected vs [] which means latest in pipeline
        if self._incoming_pipeline != None:
            if self._incoming_pipeline == []:
                want_latest = True
            elif self._incoming_pipeline == "None":
                self._incoming_pipeline = None

            self._pipeline_steps = self._incoming_pipeline
            #self._incoming_pipeline = None
        else:    
            self._pipeline_steps = None
        
        last_name = None
        for a in actions:
            if a.isChecked():
                count = count + 1
                name = a.data()['cached_display_name']
                # XXX better way?
                if name == 'Latest in Pipeline' and not want_latest:
                    a.setChecked(False)
                    count = count - 1
                    name = last_name
                if a.data()['cached_display_name'] != 'Latest in Pipeline':
                    if self._pipeline_steps == None:
                        self._pipeline_steps = []
                    self._pipeline_steps.append(a.data())
                    if want_latest:
                        a.setChecked(False)
                last_name = name
        if want_latest:
            # an empty list is what the query wants for 'latest in pipeline'
            self._pipeline_steps = []
            name = 'Latest in Pipeline'
            count = 1

        if count == 0:
            self._tray_frame.pipeline_filter_button.setText("Filter by Pipeline")
        if count == 1:
            self._tray_frame.pipeline_filter_button.setText(name)
        if count > 1:
            self._tray_frame.pipeline_filter_button.setText("%d steps" % count)

        self.request_versions_for_statuses_and_steps()

    # methods for 'the crazy query', find versions that match criteria in steps and statuses

    def filters_exist(self):
        if self._status_list or self._pipeline_steps != None or self._incoming_status or self._incoming_pipeline != None or self._incoming_pipeline != "None":
            return True
        return False

    def clear_out_rv_roles(self):
        rows = self._tray_frame.tray_model.rowCount()

        for x in range(0,rows):
            index = self._tray_frame.tray_model.index(x, 0)
            self._tray_frame.tray_delegate.update_rv_role(index, None)

            thumb = index.data(self._CUT_THUMB_ROLE)
            item = self._tray_frame.tray_model.itemFromIndex(index)
            item.setIcon(thumb)
                
        self._tray_frame.tray_model.notify_filter_data_refreshed(True)


    def filter_tray(self):
        rows = self._filtered_versions_model.rowCount()
        if rows < 1:
            self.clear_out_rv_roles()
            return None

        shot_map = {}
        for x in range(0, rows):
            item = self._filtered_versions_model.index(x, 0)
            sg = shotgun_model.get_sg_data(item)
            shot_map[sg['entity']['id']] = sg 

        # roll thru the tray and replace
        rows = self._tray_frame.tray_proxyModel.rowCount()
        if rows < 1:
             self._engine.log_warning( "Tray is empty." )
             return None

        for x in range(0,rows):
            item = self._tray_frame.tray_proxyModel.index(x, 0)
            sg = shotgun_model.get_sg_data(item)
            # cut item may not be linked to shot
            if sg['shot'] and sg['shot']['id'] in shot_map:
                v = shot_map[sg['shot']['id']]
                self._tray_frame.tray_delegate.update_rv_role(item, v)
            else:
                self._tray_frame.tray_delegate.update_rv_role(item, None)

        self._tray_frame.tray_model.notify_filter_data_refreshed(True)

    def get_tray_filters(self):
        if self._incoming_pipeline != None:
            if self._incoming_pipeline == "None":
                self._incoming_pipeline = None
            self._pipeline_steps = self._incoming_pipeline
            self._incoming_pipeline = None
        if self._incoming_status:
            self._status_list = self._incoming_status
            self._incoming_status = None

        rows = self._tray_frame.tray_proxyModel.rowCount()
        if rows < 1:
            return []
        shot_list = []
        for x in range(0,rows):
            item = self._tray_frame.tray_proxyModel.index(x, 0)
            sg = shotgun_model.get_sg_data(item)
            if sg.get('shot'):
                # cut item may not be linked to shot
                shot_list.append(sg['shot'])
        entity_list = [ 'entity', 'in', shot_list ]
        if self._status_list and self._pipeline_steps != None:
            status_list = ['sg_status_list', 'in', self._status_list ]
            step_list = ['sg_task.Task.step', 'in', self._pipeline_steps]
            if self._pipeline_steps == []:
                return [ status_list, entity_list ] 
            filters = [ step_list, status_list, entity_list ]
            return filters
        if self._status_list:
            status_list = ['sg_status_list', 'in', self._status_list ]
            filters = [ status_list, entity_list ]
            return filters
        if self._pipeline_steps != None:
            if self._pipeline_steps == []:
                return [ entity_list ]
            step_list = ['sg_task.Task.step', 'in', self._pipeline_steps]
            filters = [ step_list, entity_list ]
            return filters
        return None

    def request_versions_for_statuses_and_steps(self, silent=False):
        if not silent:
            rve.displayFeedback("Reloading ...", 60.0)

        full_filters = self.get_tray_filters()

        if full_filters == None:
            self._filtered_versions_model.clear()
            self._filtered_versions_model.data_refreshed.emit(True)
            return
        version_fields = ["image"] + required_version_fields
        version_filter_presets = [
                {"preset_name": "LATEST", "latest_by": "BY_PIPELINE_STEP_NUMBER_AND_ENTITIES_CREATED_AT" }
            ]

        self._filtered_versions_model.load_data(entity_type='Version', filters=full_filters, 
            fields=version_fields, additional_filter_presets=version_filter_presets)
        
