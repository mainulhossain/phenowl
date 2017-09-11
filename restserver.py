#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask_restful.utils import cors
from flask.ext.httpauth import HTTPBasicAuth
from flask import send_from_directory
from werkzeug.datastructures import MultiDict, FileStorage
import os
import sys
import json
from timer import Timer
import mimetypes

from phenoparser import PhenoWLInterpreter, PhenoWLParser, PythonGrammar, PhenoWLCodeGenerator
from func_resolver import Library, Function
from fileop import IOHelper, PosixFileSystem, HadoopFileSystem
from os import path

app = Flask(__name__, static_url_path="")
api = Api(app)
api.decorators=[cors.crossdomain(origin='*')]
auth = HTTPBasicAuth()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

tasks = []
interpreter = PhenoWLInterpreter()
codeGenerator = PhenoWLCodeGenerator()

def load_interpreter():
    tasks.clear()

    interpreter.context.load_library("libraries")
    funcs = []
    for f in interpreter.context.library.funcs.values():
        funcs.extend(f)
    funcs = sorted(funcs, key=lambda k : k.package)
    for f in funcs:
        tasks.append({"package_name": f.package if f.package else "", "name": f.name, "internal": f.internal, "example": f.example if f.example else "", "desc": f.desc if f.desc else "", "runmode": f.runmode if f.runmode else ""}) 

    codeGenerator.context.load_library("libraries")

load_interpreter()

@auth.get_password
def get_password(username):
    if username == 'mainulhossain@gmail.com':
        return 'mainul'
    return None


@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

task_fields = {
    'package_name': fields.String,
    'name': fields.String,
    'internal': fields.String,
    'example': fields.String,
    'desc': fields.String,
    'runmode': fields.String
}


class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('script', type=str, required=False, help='No script provided', location='json')
        self.reqparse.add_argument('code', type=str, required=False, location='json')
        self.reqparse.add_argument('library', location='files', required=False, type=FileStorage)
        self.reqparse.add_argument('mapper', location='form', required=False)
        self.reqparse.add_argument('package', location='form', required=False)
        self.reqparse.add_argument('org', location='form', required=False)
        super(TaskListAPI, self).__init__()

    #@cors.crossdomain(origin='*')
    def get(self):
        load_interpreter()
        return {'tasks': [marshal(task, task_fields) for task in tasks]}

    #@cors.crossdomain(origin='*')
    def post(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__))) #set dir of this file to current directory
        args = self.reqparse.parse_args()
        if args['script'] or args['code']:
            machine = interpreter if args['script'] else codeGenerator
            script =  args['script'] if args['script'] else args['code']
            duration = 0
            try:
                machine.context.reload()
                parser = PhenoWLParser(PythonGrammar())   
                with Timer() as t:
                    prog = parser.parse(script)
                    machine.run(prog)
                duration = t.secs
            except:
                machine.context.err.append("Error in parse and interpretation")
            return { 'out': machine.context.out, 'err': machine.context.err, 'duration': "{:.4f}s".format(duration)}, 201
        elif args['library']:
            try:
                file = args['library']#.files['file']
                filename = file.filename#secure_filename(file.filename)
                this_path = os.path.dirname(os.path.abspath(__file__))
                rel_path = 'libraries/users/mainulhossain'
                this_path = os.path.join(this_path, os.path.normpath(rel_path))
                if not os.path.isdir(this_path):
                    os.makedirs(this_path)
                path = os.path.join(this_path, filename)
                if os.path.exists(path):
                    os.remove(path)
                file.save(path)
                
                if args['mapper']:
                    base, _ = os.path.splitext(path)
                    base += '.json'
                    with open(base, 'w') as mapper:
                        mapper.write(args['mapper'])
                    package = args['package'] if args['package'] else None
                    org = args['org'] if args['org'] else None
                    rel_path = os.path.join(rel_path, filename)
                    rel_path, _ = os.path.splitext(rel_path)
                    rel_path = rel_path.replace(os.sep, '.')
                    
                    with open(base, 'r') as json_data:
                        data = json.load(json_data)
                        libraries = data["functions"]
                        for f in libraries:
                            f['module'] = rel_path
                            if package:
                                f['package'] = package
                            if org:
                                f['org'] = org
                                
                    os.remove(base)
                    with open(base, 'w') as f:
                        json.dump(data, f, indent=4)
                    load_interpreter();
            except:
                interpreter.context.err.append("Error in parse and interpretation")
            return { 'out': interpreter.context.out, 'err': interpreter.context.err}, 201


class TaskAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('module', type=str, location='json')
        self.reqparse.add_argument('name', type=str, location='json')
        self.reqparse.add_argument('internal', type=str, location='json')
        self.reqparse.add_argument('example', type=str, location='json')
        self.reqparse.add_argument('desc', type=str, location='json')
        super(TaskAPI, self).__init__()

    #@cors.crossdomain(origin='*')
    def get(self, id):
        task = [task for task in tasks if task['name'] == id]
        if len(task) == 0:
            abort(404)
        return {'task': marshal(task[0], task_fields)}

    #@cors.crossdomain(origin='*')
    def put(self, id):
        task = [task for task in tasks if task['name'] == id]
        if len(task) == 0:
            abort(404)
        task = task[0]
        args = self.reqparse.parse_args()
        for k, v in args.items():
            if v is not None:
                task[k] = v
        return {'task': marshal(task, task_fields)}

    def delete(self, id):
        task = [task for task in tasks if task['name'] == id]
        if len(task) == 0:
            abort(404)
        tasks.remove(task[0])
        return {'result': True}

class Samples():
    @staticmethod
    def load_samples_recursive(library_def_file):
        if os.path.isfile(library_def_file):
            return Samples.load_samples(library_def_file)
        
        all_samples = []
        for f in os.listdir(library_def_file):
            samples = Samples.load_samples_recursive(os.path.join(library_def_file, f))
            all_samples.extend(samples if isinstance(samples, list) else [samples])
            #all_samples = {**all_samples, **samples}
        return all_samples
       
    @staticmethod
    def load_samples(sample_def_file):
        samples = []
        if not os.path.isfile(sample_def_file) or not sample_def_file.endswith(".json"):
            return samples
        try:
            with open(sample_def_file, 'r') as json_data:
                d = json.load(json_data)
                samples = d["samples"] if d.get("samples") else d 
        finally:
            return samples
        
    @staticmethod
    def get_samples_as_list():
        samples = []
        for s in Samples.load_samples_recursive('samples'):
            samples.append({"name": s["name"], "desc": s["desc"], "sample": '\n'.join(s["sample"])})
        return samples
        
sample_fields = {
    'name': fields.String,
    'desc': fields.String,
    'sample': fields.String
}

class SamplesAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('sample', required=False, location='form')
        self.reqparse.add_argument('name', location='form', required=False)
        self.reqparse.add_argument('desc', location='form', required=False)
        super(SamplesAPI, self).__init__()

    #@cors.crossdomain(origin='*')
    def get(self):
        return {'samples': [marshal(sample, sample_fields) for sample in Samples.get_samples_as_list()]}

    def unique_filename(self, path, prefix, ext):
        make_fn = lambda i: os.path.join(path, '{0}({1}).{2}'.format(prefix, i, ext))

        for i in range(1, sys.maxsize):
            uni_fn = make_fn(i)
            if not os.path.exists(uni_fn):
                return uni_fn
            
    #@cors.crossdomain(origin='*')
    def post(self):
        this_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(this_path) #set dir of this file to current directory
        args = self.reqparse.parse_args()
        if args['sample']:
            try:
#                 sample = {}
#                 sample['sample'] = args['sample']
#                 sample['name'] = args['name']
#                 sample['desc'] = args['desc']
#                 
#                 samples = {}
#                 samples["samples"] = [sample]
                
                rel_path = 'samples/users/mainulhossain'
                this_path = os.path.join(this_path, os.path.normpath(rel_path))
                if not os.path.isdir(this_path):
                    os.makedirs(this_path)
                path = self.unique_filename(this_path, 'sample', 'json')
                
                sample = args['sample']
                with open(path, 'w') as fp:
                    fp.write("{\n")
                    fp.write('{0}"name":"{1}",\n'.format(" " * 4, args['name']));
                    fp.write('{0}"desc":"{1}",\n'.format(" " * 4, args['desc']));
                    fp.write('{0}"sample":[\n'.format(" " * 4))
                    sample = sample.replace("\\n", "\n").replace("\r\n", "\n").replace("\"", "\'")
                    lines = sample.split("\n")
                    for line in lines[0:-1]:
                        fp.write('{0}"{1}",\n'.format(" " * 8, line))
                    fp.write('{0}"{1}"\n'.format(" " * 8, lines[-1]))
                    fp.write("{0}]\n}}".format(" " * 4))
#                json.dump(samples, fp, indent=4, separators=(',', ': '))
            finally:
                return { 'out': '', 'err': ''}, 201

datasources = [{'path': 'http://sr-p2irc-big1.usask.ca:50070/user/phenodoop', 'text': 'HDFS', 'nodes': [], 'folder': True}, { 'text': 'Local FS', 'path': path.join(path.abspath(path.dirname(__file__)), 'storage'), 'nodes': [], 'folder': True}]
class DataSource():
    
    @staticmethod
    def load_data_sources():
        datasource_tree = []
        try:
            hdfs = HadoopFileSystem(datasources[0]['path'], 'hdfs')
            datasources[0]['nodes'] = hdfs.make_json('/')['nodes']
            datasource_tree.append(datasources[0])
        except:
            pass
        
        fs = PosixFileSystem()
        datasources[1]['nodes'] = fs.make_json('/')['nodes']
        datasource_tree.append(datasources[1])
            
        return datasource_tree
    
    @staticmethod
    def get_filesystem(path):
        for ds in datasources:
            if path.startswith(ds['path']):
                return IOHelper.getFileSystem(ds['path'])
    
    @staticmethod
    def load_data_sources_json():
        return json.dumps(DataSource.load_data_sources())
    
    @staticmethod
    def upload(file, fullpath):
        fs = DataSource.get_filesystem(fullpath)
        return fs.saveUpload(file, fullpath)
    
    @staticmethod
    def download(fullpath):
        fs = DataSource.get_filesystem(fullpath)
        return fs.download(fullpath)
        
class DataSourcesAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('path', location='form', required=False)
        self.reqparse.add_argument('upload', location='files', required=False, type=FileStorage)
        self.reqparse.add_argument('download', required=False)
        self.reqparse.add_argument('addfolder', required=False, location='json')
        self.reqparse.add_argument('delete', required=False)
        self.reqparse.add_argument('rename', required=False)
        self.reqparse.add_argument('oldpath', required=False)
        super(DataSourcesAPI, self).__init__()

    def get(self):
        return {'datasources': DataSource.load_data_sources_json() }
    
    @staticmethod
    def guess_mimetype(resource_path):
        """
        Guesses the mimetype of a given resource.
        Args:
            resource_path: the path to a given resource.
        Returns:
            The mimetype string.
        """
    
        mime = mimetypes.guess_type(resource_path)[0]
    
        if mime is None:
            return "application/octet-stream"
    
        return mime

    #@cors.crossdomain(origin='*')
    def post(self):
        this_path = os.path.dirname(os.path.abspath(__file__))
        args = self.reqparse.parse_args()
        if args['upload']:
            try:
                file = args['upload']
                DataSource.upload(file, args['path'])
            finally:
                return { 'out': '', 'err': ''}, 201
        elif args['download']:
            try:
                fullpath = DataSource.download(args['download'])
                mime = mimetypes.guess_type(fullpath)[0]
                return send_from_directory(os.path.dirname(fullpath), os.path.basename(fullpath), mimetype=mime, as_attachment = mime is None )
            except Exception as inst:
                return { 'out': '', 'err': str(inst)}, 201
        elif args['addfolder']:
            fileSystem = DataSource.get_filesystem(args['addfolder'])
            parent = args['addfolder'] if fileSystem.isdir(args['addfolder']) else os.path.dirname(args['addfolder'])
            unique_filename = IOHelper.unique_fs_name(fileSystem, parent, 'newfolder', '')
            return {'path' : fileSystem.create_folder(unique_filename) }
        elif args['delete']:
            fileSystem = DataSource.get_filesystem(args['delete'])
            return {'path' : fileSystem.remove(fileSystem.strip_root(args['delete'])) }
        elif args['rename']:
            fileSystem = DataSource.get_filesystem(args['oldpath'])
            oldpath = fileSystem.strip_root(args['oldpath'])
            newpath = os.path.join(os.path.dirname(oldpath), args['rename'])
            return {'path' : fileSystem.rename(oldpath, newpath) }
    
api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<string:id>', endpoint='task')
api.add_resource(SamplesAPI, '/todo/api/v1.0/samples', endpoint='samples')
api.add_resource(DataSourcesAPI, '/todo/api/v1.0/datasources', endpoint='datasources')

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    app.run(debug=True)