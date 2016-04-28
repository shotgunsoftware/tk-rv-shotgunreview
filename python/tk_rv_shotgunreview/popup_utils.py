import json
import tank

from tank.platform.qt import QtCore, QtGui

task_manager = tank.platform.import_framework("tk-framework-shotgunutils", "task_manager")
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

from .filter_steps_model import FilterStepsModel
from .rel_cuts_model import RelCutsModel
from .rel_shots_model import RelShotsModel

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
        self._pipeline_steps = []

        self._steps_task_manager = task_manager.BackgroundTaskManager(parent=None,
                                                                    start_processing=True,
                                                                    max_threads=2)

        self._steps_model = FilterStepsModel(None, self._steps_task_manager)

        self._rel_cuts_task_manager = task_manager.BackgroundTaskManager(parent=None,
                                                                    start_processing=True,
                                                                    max_threads=2)

        self._rel_cuts_model = RelCutsModel(None, self._rel_cuts_task_manager)

        self._rel_shots_task_manager = task_manager.BackgroundTaskManager(parent=None,
                                                                    start_processing=True,
                                                                    max_threads=2)

        self._rel_shots_model = RelShotsModel(None, self._rel_cuts_task_manager)

        
        # connections
        self._rel_cuts_model.data_refreshed.connect(self.on_rel_cuts_refreshed)
        self._rel_shots_model.data_refreshed.connect(self.on_rel_shots_refreshed)
        
        self._steps_model.data_refreshed.connect(self.handle_pipeline_steps_refreshed)
        

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
        # print "find_rel_cuts_with_model %r %r %r" % (entity_in, shot_entity, self._project_entity['id'])
        self._rel_cuts_done = False
        self._rel_shots_done = False

        conditions = ['entity', 'is', entity_in]
        cut_filters = [ conditions, ['project', 'is', { 'id': self._project_entity['id'], 'type': 'Project' } ]]
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


    def on_rel_cuts_refreshed(self):
        self._rel_cuts_done = True
        if self._rel_cuts_done and self._rel_shots_done:
            self._rel_shots_done = False
            self._rel_cuts_done = False
            self.related_cuts_ready.emit()

    def on_rel_shots_refreshed(self):
        self._rel_shots_done = True
        if self._rel_cuts_done and self._rel_shots_done:
            self._rel_shots_done = False
            self._rel_cuts_done = False
            self.related_cuts_ready.emit()
        
    def set_project(self, entity):
        # XXX invalidate queries? auto-load status? 
        self._project_entity = entity

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

        sorted_cuts = sorted(seq_cuts, key=lambda x: x['cached_display_name'], reverse=False)
 
        dup_map = {}
        for x in sorted_cuts:
            if x['code'] not in dup_map:
                dup_map[x['code']] = 1
            else:
                dup_map[x['code']] = dup_map[x['code']] + 1
        for x in sorted_cuts:
            x['count'] = dup_map[x['code']]

        return sorted_cuts
 

    def get_status_list(self, project_entity=None):
        """
        This query needs to be run only when the project changes.
        We cache the last query in memory.
        """
        # XXX - cache all queries in a map for bouncing between projects?
        if not project_entity:
            project_entity = self._project_entity

        if not self._status_schema or project_entity['id'] != self._project_entity['id']:
            self._project_entity = project_entity
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
        # print "status_list: %r" % self._status_schema['sg_status_list']
        # print "properties: %r" % self._status_schema['sg_status_list']['properties']
        # print "values: %r" % self._status_schema['sg_status_list']['properties']['valid_values']['value']
        # for x in self._status_schema['sg_status_list']:
            #print "%r" % x
        # print "display values: %r" % self._status_schema['sg_status_list']['properties']['display_values']['value']
        
        s = self.get_status_list(project_entity)
        d = s['sg_status_list']['properties']['display_values']['value']
        status_list = []
        for x in d:
            e = {}
            e[x] = d[x]
            status_list.append(e)
        return status_list

    def build_status_menu(self):
        statii = self.get_status_menu(self._project_entity)
        if not self._status_menu:
            self._status_menu = QtGui.QMenu(self._tray_frame.status_filter_button)
            self._tray_frame.status_filter_button.setMenu(self._status_menu)        
            self._status_menu.triggered.connect(self.handle_status_menu)
        menu = self._status_menu
        menu.clear()
        action = QtGui.QAction(self._tray_frame.status_filter_button)
        action.setCheckable(True)
        action.setChecked(False)
        action.setText('Any Status')
        # XXX what object here?
        action.setData(None)
        menu.addAction(action)
        menu.addSeparator()

        for status in statii:
            action = QtGui.QAction(self._tray_frame.status_filter_button)
            action.setCheckable(True)
            action.setChecked(False)
            for x in status:
                action.setText(status[x])
            action.setData(status)
            menu.addAction(action)


    def handle_status_menu(self, event):
        print "handle_status_menu event: %r" % event.data()
        # if 'any status' is picked, then the other
        # choices are zeroed out. event.data will be None for any status

        self._status_list = []
        actions = self._status_menu.actions()
        if not event.data():
            print 'clearing out status list'
            for a in actions:
                a.setChecked(False)
            self._tray_frame.status_filter_button.setText("Filter by Status")
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
        
        self._rv_mode.filter_tray()

    def get_pipeline_steps_with_model(self):
        step_filters = [['entity_type', 'is', 'Shot' ]]
        step_fields = ['code', 'list_order', 'short_name', 'id', 'cached_display_name']
        step_orders = [ {'field_name': 'list_order', 'direction': 'desc'} ]
        self._steps_model.load_data(entity_type="Step", filters=step_filters, fields=step_fields, order=step_orders)        


    def handle_pipeline_steps_refreshed(self, refreshed):
        """
        This loads the menu with values returned when the _steps_model returns data_refreshed
        """
        self._engine.log_info('================handle_pipeline_steps_refreshed')

        if not self._pipeline_steps_menu:
            self._pipeline_steps_menu = QtGui.QMenu(self._tray_frame.pipeline_filter_button)
            self._tray_frame.pipeline_filter_button.setMenu(self._pipeline_steps_menu)        
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

        rows = self._steps_model.rowCount()

        for x in range(0, rows):
            item = self._steps_model.index(x, 0)
            sg = shotgun_model.get_sg_data(item)
            action = QtGui.QAction(self._tray_frame.pipeline_filter_button)
            action.setCheckable(True)
            action.setChecked(False)
            action.setText(sg['cached_display_name'])
            action.setData(sg)
            menu.addAction(action)

    def handle_pipeline_menu(self, event):
        """
        This is run after the user makes a selection in the Pipeline Steps menu
        """
        # you only get the latest one clicked here. there could be more.
        # you might also get a roll off event that you dont want.
        # so check the widget and then update the button text
        # if event.data():
        #     print "handle_pipeline_menu: %r" % event.data()
        actions = self._pipeline_steps_menu.actions()
        count = 0
        name = 'Error'
        # for later filtering
        self._pipeline_steps = []
        for a in actions:
            if a.isChecked():
                count = count + 1
                name = a.data()['cached_display_name']
                self._pipeline_steps.append(a.data())
        if count == 0:
            self._tray_frame.pipeline_filter_button.setText("Filter by Pipeline")
        if count == 1:
            self._tray_frame.pipeline_filter_button.setText(name)
        if count > 1:
            self._tray_frame.pipeline_filter_button.setText("%d steps" % count)
        self._rv_mode.filter_tray()


   # def merge_cuts_for_menu(self, seq_cuts, shot_cuts):

    #     shot_map = {}
    #     shot_ids = []

    #     if shot_cuts:
    #         for x in shot_cuts:
    #             shot_ids.append(x['id'])
    #             shot_map[x['id']] = x
        
    #     seq_ids = []
    #     for x in seq_cuts:
    #         seq_ids.append(x['id'])

    #     for n in shot_ids:
    #         if n not in seq_ids:
    #             seq_cuts.append(shot_map[n])

    #     # resort seq_cuts by 'code'
    #     sorted_cuts = sorted(seq_cuts, key=lambda x: x['cached_display_name'], reverse=False)
 
    #     # count the dups
    #     dup_map = {}
    #     for x in sorted_cuts:
    #         if x['code'] not in dup_map:
    #             dup_map[x['code']] = 1
    #         else:
    #             dup_map[x['code']] = dup_map[x['code']] + 1
    #     for x in sorted_cuts:
    #         x['count'] = dup_map[x['code']]

    #     return sorted_cuts

    # Pipeline filtering

