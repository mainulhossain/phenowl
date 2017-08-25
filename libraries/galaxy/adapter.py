from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.histories import HistoryClient
from bioblend.galaxy.libraries import LibraryClient
from bioblend.galaxy.tools import ToolClient
from bioblend.galaxy.datasets import DatasetClient
from urllib.parse import urlparse, urlunparse
import urllib.request
import shutil
import json
import uuid
import tempfile
from ftplib import FTP
from collections import namedtuple

from fileop import IOHelper

#gi = GalaxyInstance(url='http://sr-p2irc-big8.usask.ca:8080', key='7483fa940d53add053903042c39f853a')
#  r = toolClient.run_tool('a799d38679e985db', 'toolshed.g2.bx.psu.edu/repos/devteam/fastq_groomer/fastq_groomer/1.0.4', params)

def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())

def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)

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

def get_most_recent_history_id(gi):
    hc = HistoryClient(gi)
    hi = hc.get_most_recently_used_history()
    return hi['id']
    
def get_most_recent_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    return get_most_recent_history_id(gi)
        
def create_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    hc = HistoryClient(gi)
    historyName = args[3] if len(args) > 3 else str(uuid.uuid4())
    h = hc.create_history(historyName)
    return h["id"]

def history_id_to_name(*args):
    wf = get_histories_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j['name']

def history_name_to_ids(*args):
    wf = get_histories_json(*args)
    ids = []
    for j in wf:
        if j['name'] == args[3]:
            ids.append(j['id'])
    return ids
        
def get_tools_json(*args):
    gi = GalaxyInstance(args[0], args[1])
    tc = ToolClient(gi)
    return tc.get_tools()

def get_tools_ids(*args):
    wf = get_tools_json(*args)
    wf_ids = []
    for j in wf:
        #yield j.name
        wf_ids.append(j['id'])
    return wf_ids

def get_tools_names(*args):
    wf = get_tools_json(*args)
    wf_ids = []
    for j in wf:
        #yield j.name
        wf_ids.append(j['name'])
    return wf_ids
    
def get_tool(*args):
    wf = get_tools_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j

def get_tools_by_name(*args):
    wf = get_tools_json(*args)
    named = []
    for j in wf:
        if j['name'] == args[3]:
            named.append(j)
    return named

def tool_id_to_name(*args):
    wf = get_tools_json(*args)
    for j in wf:
        if j['id'] == args[3]:
            return j['name']

def tool_name_to_id(*args):
    wf = get_tools_json(*args)
    for j in wf:
        if j['name'] == args[3]:
            return j['id']

def get_tool_params_by_tool_name(*args):
    tools = get_tools_json(*args)
    tc = ToolClient(gi)               
    for t in tools:
        if t['name'] == args[3]:
            ts = tc.show_tool(tool_id = t['id'], io_details=True)
            if len(args) > 4:
                return ts[args[4]]
            else:
                return ts
                            
def get_tool_params(*args):
    gi = GalaxyInstance(args[0], args[1])
    tc = ToolClient(gi)
    ts = tc.show_tool(tool_id = args[3], io_details=True)
    if len(args) > 4:
        return ts[args[4]]
    else:
        return ts
                                        
def get_history_datasets(*args):
    gi = GalaxyInstance(args[0], args[1])
    historyid = args[3] if len(args) > 3 else get_most_recent_history_id(gi)
    name = args[4] if len(args) > 4 else None

    datasets = gi.histories.show_matching_datasets(historyid, name)
    ids = []
    for dataset in datasets:
        ids.append(dataset['id'])
    return ids

def dataset_id_to_name(*args):
    gi = GalaxyInstance(args[0], args[1])
    dc = DatasetClient(gi)
    details = dc.show_dataset(args[3])
    return details['name']
                            
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

def create_library(*args):
    gi = GalaxyInstance(args[0], args[1])
    hc = LibraryClient(gi)
    historyName = args[2] if len(args) > 2 else str(uuid.uuid4())
    h = hc.create_library(historyName)
    return h["id"]

def upload_to_library_from_url(*args):
    gi = GalaxyInstance(args[0], args[1])
    hc = LibraryClient(gi)
    libraryid = args[2]
    d = hc.upload_file_from_url(libraryid, args[3])
    return d["id"]

def upload_to_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    path = IOHelper.normaize_path(args[3])
    historyid = args[4] if len(args) > 4 else get_most_recent_history_id(gi)
    d = gi.tools.upload_file(path, historyid)
    return d["id"]
    
def ftp_to_history(*args):
    gi = GalaxyInstance(args[0], args[1])
       
    u = urlparse(args[3])
    if u.scheme:
        p = urlunparse((u.scheme, u.netloc, '', '', '', ''))
    
    if u.scheme.lower() is not 'ftp':
        raise 'No ftp address given.'
        
    ftp = FTP(u.netloc)
    ftp.login()
    
    ftp.cwd(os.path.dirname(u.path))
    filename = os.path.basename(u.path)
    
    destfile = os.path.join(tempfile.gettempdir(), filename)
    if os.exists(destfile):
        os.delete(destfile)
        
    ftp.retrbinary("RETR " + filename, open(destfile, 'wb').write)
    
    historyid = args[4] if len(args) > 4 else get_most_recent_history_id(gi)
    d = gi.tools.upload_file(destfile, historyid) #hid: a799d38679e985db 03501d7626bd192f
    return d["id"]

def download_file(*args):
    remote_name = args[3]
    u = urlparse(remote_name)
    
    filename = os.path.basename(u.path)   
    destfile = os.path.join(tempfile.gettempdir(), filename)
    if os.exists(destfile):
        os.delete(destfile)
    
    if u.scheme:
        if u.scheme.lower() == 'http' or u.scheme.lower() == 'https':
            # Download the file from `url` and save it locally under `file_name`:
            with urllib.request.urlopen(remote_name) as response, open(destfile, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        elif u.scheme.lower() == 'ftp':
            ftp = FTP(u.netloc)
            ftp.login()
            ftp.cwd(os.path.dirname(u.path))
        else:
            raise 'No http(s) address given.'

    gi = GalaxyInstance(args[0], args[1])
    historyid = args[4] if len(args) > 4 else get_most_recent_history_id(gi)
    d = gi.tools.upload_file(destfile, historyid) #hid: a799d38679e985db 03501d7626bd192f
    return d["id"]
    
def http_to_history(*args):
    return download_file(*args)  

def run_tool(*args):
    gi = GalaxyInstance(args[0], args[1])
    toolClient = ToolClient(gi)
    #params = json2obj(args[5])
    params = args[5]
    inputs = {}
    if params:
        params = params.split(",")
        for param in params:
            param = param.split(":")
            inputs[str(param[0])] = param[1]
            
    return toolClient.run_tool(history_id=args[3], tool_id=args[4], tool_inputs=inputs)
