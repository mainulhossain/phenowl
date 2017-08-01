from bioblend.galaxy import GalaxyInstance
import json

def get_workflows_json(*args):
    gi = GalaxyInstance(args[0], args[1])
    return gi.workflows.get_workflows()
    
def get_workflow_ids(*args):
    wf = get_workflows_json(*args)
    wf_ids = []
    for j in wf:
        #yield j.name
        wf_ids.append(j['id'])
    return wf_ids

def get_workflow(*args):
    wf = get_workflows_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j
        
def get_libraries_json(*args):
    gi = GalaxyInstance(args[0], args[1])
    return gi.libraries.get_libraries()
    
def get_library_ids(*args):
    wf = get_libraries_json(*args)
    wf_ids = []
    for j in wf:
        #yield j.name
        wf_ids.append(j['id'])
    return wf_ids

def get_library(*args):
    wf = get_libraries_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j
        
def get_histories_json(*args):
    gi = GalaxyInstance(args[0], args[1])
    return gi.histories.get_histories()
    
def get_history_ids(*args):
    wf = get_histories_json(*args)
    wf_ids = []
    for j in wf:
        #yield j.name
        wf_ids.append(j['id'])
    return wf_ids

def get_history(*args):
    wf = get_histories_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j

def get_history_datasets(*args):
    gi = GalaxyInstance(args[0], args[1])
    #history = get_history(*args)
    #if history is not None:
    #return gi.histories.show_matching_datasets(args[3])
    return gi.histories.show_history(args[3], contents=True)
                        
def upload(*args):
    gi = GalaxyInstance(args[0], args[1])
    library = get_library(*args)
    if library is not None:
        return gi.libraries.upload_file_from_local_path(library['id'], args[4])
    else:
        r = gi.tools.upload_file(args[4], args[3])
    
def run_workflow(*args):
    gi = GalaxyInstance(args[0], args[1])
    workflow_id = args[3]
    datamap = dict()
    datamap['252'] = { 'src':'hda', 'id':str(args[4]) }
    return gi.workflows.run_workflow(args[3], datamap, history_name='New Workflow Execution History')