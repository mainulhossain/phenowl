#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask_restful.utils import cors
from flask.ext.httpauth import HTTPBasicAuth
from phenoparser import PhenoWLInterpreter, PhenoWLParser, PythonGrammar
from func_resolver import Library, Function
import os
import sys
import json
from timer import Timer

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

interpreter = PhenoWLInterpreter()
interpreter.context.load_library("libraries")
    
tasks = []
funcs = []
for k,f in interpreter.context.library.funcs.items():
    funcs.extend(f)
funcs = sorted(funcs, key=lambda k : k.package)
for f in funcs:
    tasks.append({"package_name": f.package if f.package else "", "name": f.name, "internal": f.internal, "example": f.example if f.example else "", "desc": f.desc if f.desc else "", "runmode": f.runmode if f.runmode else ""}) 

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
        self.reqparse.add_argument('script', type=str, required=True, help='No script provided', location='json')
        super(TaskListAPI, self).__init__()

    #@cors.crossdomain(origin='*')
    def get(self):
        return {'tasks': [marshal(task, task_fields) for task in tasks]}

    #@cors.crossdomain(origin='*')
    def post(self):
        args = self.reqparse.parse_args()
        script = args['script']
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__))) #set dir of this file to current directory
            with Timer() as t:
                interpreter.context.reload()
                parser = PhenoWLParser(PythonGrammar())   
                prog = parser.parse(script)
                interpreter.run(prog)
                
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

def load_samples(sample_def_file):
    with open(sample_def_file, 'r') as json_data:
        d = json.load(json_data)
        return d["samples"]
    
samples = []
for s in load_samples('samples.json'):
    samples.append({"name": s["name"], "desc": s["desc"], "sample": '\n'.join(s["sample"])}) 

sample_fields = {
    'name': fields.String,
    'desc': fields.String,
    'sample': fields.String,
}

class SamplesAPI(Resource):
    #decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(SamplesAPI, self).__init__()

    #@cors.crossdomain(origin='*')
    def get(self):
        return {'samples': [marshal(sample, sample_fields) for sample in samples]}

    #@cors.crossdomain(origin='*')
    def post(self):
        args = self.reqparse.parse_args()
        return { 'out': '', 'err': ''}, 201

api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<string:id>', endpoint='task')
api.add_resource(SamplesAPI, '/todo/api/v1.0/samples', endpoint='samples')

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    app.run(debug=True)