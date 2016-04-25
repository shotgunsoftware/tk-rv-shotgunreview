import json

class PopupUtils:
    def __init__(self, engine, shotgun, project_entity):
        self._engine = engine
        self._shotgun = shotgun
        self._project_entity = project_entity
        self._sequence_cuts = []
        self._sequence_entity = None
        self._shot_steps = None
        self._status_schema = None
     
    def cached_find_cuts(self, conditions):
        # conditions is an array, with 3 vals
        # [ <field>, 'is', dict ]
        if conditions[2]['type'] == 'Sequence' or conditions[2]['type'] == 'Scene':
            if self._sequence_entity:
                if self._sequence_entity['id'] != conditions[2]['id']:
                    self._sequence_entity =  conditions[2]
                    self._sequence_cuts = self.find_cuts(conditions)
                else:
                    return self._sequence_cuts
            else:
                self._sequence_entity = conditions[2]
                self._sequence_cuts = self.find_cuts(conditions)

            return self._sequence_cuts
        else:
            # not something we cache anyway
            return self.find_cuts(conditions)

    def find_cuts(self, conditions):
        # conditions is an array, with 3 vals
        # [ <field>, 'is', dict ]
        # ['entity', 'is', {'type': 'Sequence', 'id': 31, 'name': '08_a-team'}]
        # ['cut_items.CutItem.shot', 'is', {'type': 'Shot', 'id': 1237}]
        print "DB CALL: find_cuts with conditions: %r" % conditions
        cuts = self._shotgun.find('Cut',
                filters=[ conditions, ['project', 'is', { 'id': self._project_entity['id'], 'type': 'Project' } ]],
                fields=['id', 'entity', 'code', 'cached_display_name'],
                order=[
                    # {'field_name': 'entity', 'direction': 'asc'}, 
                    {'field_name': 'code', 'direction': 'asc'}, 
                    {'field_name': 'cached_display_name', 'direction': 'asc'}
                    ])
       
        return cuts

    def set_project(self, entity):
        self._project_entity = entity

    def merge_cuts_for_menu(self, seq_cuts, shot_cuts):

        shot_map = {}
        shot_ids = []

        if shot_cuts:
            for x in shot_cuts:
                shot_ids.append(x['id'])
                shot_map[x['id']] = x
        
        seq_ids = []
        for x in seq_cuts:
            seq_ids.append(x['id'])

        for n in shot_ids:
            if n not in seq_ids:
                seq_cuts.append(shot_map[n])

        # resort seq_cuts by 'code'
        sorted_cuts = sorted(seq_cuts, key=lambda x: x['cached_display_name'], reverse=False)
 
        # count the dups
        dup_map = {}
        for x in sorted_cuts:
            if x['code'] not in dup_map:
                dup_map[x['code']] = 1
            else:
                dup_map[x['code']] = dup_map[x['code']] + 1
        for x in sorted_cuts:
            x['count'] = dup_map[x['code']]

        # print "merge_cuts_for_menu:"
        # for x in sorted_cuts:
        #     for keys in x:
        #         print "\t%r: %r" % (keys, x[keys])
        #     print "-----------------------------------"
        # print "%d ENTRIES IN SORTED" % len(sorted_cuts)
        return sorted_cuts

    # Pipeline filtering

    def get_pipeline_steps(self):
        if not self._shot_steps:
            print "DB CALL: get_pipeline_steps"
            self._shot_steps = self._shotgun.find('Step', filters=[['entity_type', 'is', 'Shot' ]], fields=['code', 'list_order', 'short_name', 'id', 'cached_display_name'], order=[{'field_name': 'list_order', 'direction': 'desc'}])
        
        # for x in self._shot_steps:
        #     print '=============='
        #     for z in x:
        #         print "%r -> %r" %( z, x[z])
        # print "STEPS: %r" % len(self._shot_steps)

        return self._shot_steps


    def get_status_list(self, project_entity=None):
        print "get_status_list %r" % project_entity
        if project_entity:
            if project_entity['id'] != self._project_entity['id']:
                self._project_entity = project_entity
                project_id = self._project_entity['id']
                print "DB CALL: get_status_list - new project id"
                self._status_schema = self._shotgun.schema_field_read('Version', field_name='sg_status_list', project_entity={ 'id': project_id, 'type': 'Project' } )
        
        if not self._status_schema:
            project_id = self._project_entity['id']
            print "DB CALL: get_status_list - load schema"
            self._status_schema = self._shotgun.schema_field_read('Version', field_name='sg_status_list', project_entity={ 'id': project_id, 'type': 'Project' } )

        # print "status_list: %r" % self._status_schema['sg_status_list']
        # print "properties: %r" % self._status_schema['sg_status_list']['properties']
        # print "values: %r" % self._status_schema['sg_status_list']['properties']['valid_values']['value']
        #for x in self._status_schema['sg_status_list']:
            #print "%r" % x
        # print "display values: %r" % self._status_schema['sg_status_list']['properties']['display_values']['value']

        return self._status_schema
        #shot_filters = None
        #self.request_data(shot_filters)

    def get_status_menu(self, project_entity=None):
        s = self.get_status_list(project_entity)
        d = s['sg_status_list']['properties']['display_values']['value']
        status_list = []
        for x in d:
            e = {}
            e[x] = d[x]
            status_list.append(e)
        return status_list


    ##################################################################################################################

    ##################################################################################################################
    # popup right side menu stuff from eric BELOW  ... tested but not integrated yet.

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


        sg = self._shotgun
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
