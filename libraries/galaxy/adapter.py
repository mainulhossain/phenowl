from bioblend.galaxy import GalaxyInstance
import json

def get_workflows_json(*args):
    gi = GalaxyInstance(args[0], args[1])
    return gi.workflows.get_workflows()
    
def get_workflows(*args):
    wf = get_workflows_json(*args)
    wf_names = []
    for j in wf:
        #yield j.name
        wf_names.append(j['name'])
    return wf_names

def get_workflow(*args):
    wf = get_workflows_json(args)
    for j in wf:
        if j['name'] is args[2]:
            return j