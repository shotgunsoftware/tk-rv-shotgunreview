

class PopupUtils:
    def __init__(self, engine, shotgun, project_entity):
        self._engine = engine
        self._shotgun = shotgun
        self._project_entity = project_entity
        self._sequence_cuts = []
        self._sequence_entity = None
     
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

        cuts = self._shotgun.find('Cut',
                filters=[ conditions, ['project', 'is', { 'id': self._project_entity['id'], 'type': 'Project' } ]],
                fields=['id', 'entity', 'code', 'cached_display_name'],
                order=[
                    # {'field_name': 'entity', 'direction': 'asc'}, 
                    {'field_name': 'code', 'direction': 'asc'}, 
                    {'field_name': 'cached_display_name', 'direction': 'asc'}
                    ])


        print "find_cuts: %r" % conditions
        for x in cuts:
            for keys in x:
                print "\t%r: %r" % (keys, x[keys])
            print "-----------------------------------"
        
        return cuts

    def set_project(self, entity):
        self._project_entity = entity

    def merge_cuts_for_menu(self, seq_cuts, shot_cuts):

        print "MERGE NEW ==============="
        print "shot_cuts: %r" % shot_cuts
        print "=====================\n"
        print "seq_cuts: %r" % seq_cuts
        print "=====================\n"

        shot_map = {}

        shot_ids = []
        if shot_cuts:
            for x in shot_cuts:
                shot_ids.append(x['id'])
                shot_map[x['id']] = x
        
        seq_ids = []
        for x in seq_cuts:
            print "seq x: %r" % x
            seq_ids.append(x['id'])

        for n in shot_ids:
            if n not in seq_ids:
                print "appending %r" % shot_map[n]
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

        print "merge_cuts_for_menu:"
        for x in sorted_cuts:
            for keys in x:
                print "\t%r: %r" % (keys, x[keys])
            print "-----------------------------------"
        print "%d ENTRIES IN SORTED" % len(sorted_cuts)
        return sorted_cuts


