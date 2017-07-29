from bioblend.galaxy import GalaxyInstance
import json

def get_workflows(*args):
    gi = GalaxyInstance(args[0], args[1])
    wf = gi.workflows.get_workflows()
    js = json.load(wf)
    wf_names = []
    for j in js:
        wf_names.append(js.name)
    return wf_names

def get_workflow(*args):
    gi = GalaxyInstance(args[0], args[1])
    wf = gi.workflows.get_workflows()
    js = json.load(wf)
    for j in js:
        if js.name is args[2]:
            return js
