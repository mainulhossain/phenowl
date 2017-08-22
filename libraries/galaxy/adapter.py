from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.histories import HistoryClient
from bioblend.galaxy.libraries import LibraryClient
from bioblend.galaxy.tools import ToolClient
from urllib.parse import urlparse, urlunparse
import json
import uuid
import tempfile
from ftplib import FTP
from fileop import IOHelper

#gi = GalaxyInstance(url='http://sr-p2irc-big8.usask.ca:8080', key='7483fa940d53add053903042c39f853a')
#  r = toolClient.run_tool('a799d38679e985db', 'toolshed.g2.bx.psu.edu/repos/devteam/fastq_groomer/fastq_groomer/1.0.4', params)

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
        if j['id'] == args[2]:
            return j

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
        if j['id'] == args[2]:
            return j

def get_tools_by_name(*args):
    wf = get_tools_json(*args)
    named = []
    for j in wf:
        if j['name'] == args[2]:
            named.append(j)
    return named

def tool_id_to_name(*args):
    wf = get_tools_json(*args)
    for j in wf:
        if j['id'] == args[2]:
            return j['name']

def tool_name_to_ids(*args):
    wf = get_tools_json(*args)
    ids = []
    ids.append(j['id'] for j in wf if j['name'] == args[2])
    return ids 

def get_tool_params(*args):
    tools = get_tools_json(*args)               
    for t in tools:
        if t['name'] == args[2]:
            ts = toolClient.show_tool(tool_id = t['id'], io_details=True)
            if len(args) > 3:
                return ts[args[3]]
            else:
                return ts
                            
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

def create_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    hc = HistoryClient(gi)
    historyName = args[2] if len(args) > 2 else str(uuid.uuid4())
    h = hc.create_history(historyName)
    return h["id"]

def upload_to_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    historyid = args[2]
    path = IOHelper.normaize_path(args[3])
    d = gi.tools.upload_file(path, historyid)
    return d["id"]
    
def ftp_to_history(*args):
    gi = GalaxyInstance(args[0], args[1])
    historyid = args[2]
       
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
    
    d = gi.tools.upload_file(destfile, historyid) #hid: a799d38679e985db 03501d7626bd192f
    return d["id"]

def run_tool(*args):
    gi = GalaxyInstance(args[0], args[1])
    toolClient = ToolClient(gi)
    return toolClient.run_tool(history_id=args[2], tool_id=args[3], tool_inputs=args[4])