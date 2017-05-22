#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask_restful.utils import cors
from flask.ext.httpauth import HTTPBasicAuth
from phenoparser import PhenoWLInterpreter, PhenoWLParser, PythonGrammar
import os
import sys


app = Flask(__name__, static_url_path="")
api = Api(app)
#api.decorators=[cors.crossdomain(origin='*')]
auth = HTTPBasicAuth()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

interpreter = PhenoWLInterpreter()
interpreter.context.load_libraries("funcdefs.json")
    
tasks = []
for l in interpreter.context.libraries:
    for p in l["packages"]:
        for f in p["functions"]:
            name = f["name"] if f.get("name") else f["internal"]
            internal = f["internal"] if f.get("internal") else f["name"]
            tasks.append({"module": p["module"] if p.get('module') else "", "name": name, "internal": internal}) 

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
    'module': fields.String,
    'name': fields.String,
    'internal': fields.String
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
        print(args['script'], sys.stderr)
        script = args['script']
        try:
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
        self.reqparse.add_argument('internal', type=bool, location='json')
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


api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<string:id>', endpoint='task')

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    app.run(debug=True)
