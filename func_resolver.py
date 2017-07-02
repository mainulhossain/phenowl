from importlib import import_module
from fileop import IOHelper
#from imgproc.imagefuncs import ImageProcessor
from os import path
from subprocess import Popen, PIPE, STDOUT, run
import json

#from phenoparser import Context

def func_exec(app, *args):

    cmd = app
    if args:
        cmd += ' ' + ' '.join(args)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False)
    return p.stdout.read()

def func_exec_run(app, *args):
    cmd = app
    if args:
        cmd += ' ' + ' '.join(args)
    p = run(cmd, stdout=PIPE, stderr=STDOUT, shell=True)
    return p.stdout.decode('utf-8')

def load_module(modulename):
    '''
    Load a module dynamically from a string module name.
    It was first implemented with __import__, but later
    replaced by importlib.import_module.
    :param modulename:
    '''
    #if modulename not in sys.modules:
    #name = "package." + modulename
    #return __import__(modulename, fromlist=[''])
    return import_module(modulename)

class Function():
    def __init__(self, name, internal, package = None, module = None, runmode = 'local', params = []):
        self.name = name
        self.internal = internal
        self.package = package
        self.module = module
        self.runmode = runmode
        self.params = params
        
class Library():
    def __init__(self, funcs = {}):
        self.funcs = funcs
        self.tasks = {}
        self.localdir = path.join(path.abspath(path.dirname(__file__)), 'storage')
    
    def add_task(self, name, expr):
        self.tasks[name] = expr
    
    def run_task(self, name, args, dotaskstmt):
        if name in self.tasks:
            dotaskstmt(self.tasks[name], args)
    
    @staticmethod
    def load(library_def_file):
        library = Library()
        with open(library_def_file, 'r') as json_data:
            d = json.load(json_data)
            libraries = d["functions"]
            libraries = sorted(libraries, key = lambda k : k['package'].lower())
            for f in libraries:
                name = f["name"].lower() if f.get("name") else f["internal"]
                internal = f["internal"] if f.get("internal") else f["name"].lower()
                module = f["module"] if f.get("module") else None
                package = f["package"] if f.get("package") else None
                runmode = f["runmode"] if f.get("runmode") else None
                params = []
                if (f.get("params")):
                    for param in f["params"]:
                        params.append(param)
                f = Function(name, internal, package, module, runmode, params)
                if name in library.funcs:
                    library.funcs[name].append(f)
                else:
                    library.funcs[name] = [f]
                    
        return library
    
    def func_to_internal_name(self, funcname):
        for f in self.funcs:
            if f.get("name") and self.iequal(f["name"], funcname):
                return f["internal"]
            
    def get_function(self, name, package = None):
        functions = self.funcs[name]
        if package is not None:
            fs = []
            for f in functions:
                if f.package == package:
                    fs.append(f)
            return fs 
        return functions
    
    def check_function(self, name, package = None):
        functions = self.get_function(name, package)
        return functions is not None and len(functions) > 0
    
    def select_function(self, context, name, package = None):
        functions = self.funcs[name]
        if package is not None:
            fs = []
            for f in functions:
                if f.package == package:
                    fs.append(f)
            return fs 
        return functions
    
    def call_func(self, context, package, function, arguments):
        '''
        Call a function from a module.
        :param context: The context for output and error
        :param package: The name of the package. If it's empty, local function is called    
        :param function: Name of the function
        :param arguments: The arguments for the function
        '''
        if not package or package == "None":
            if function.lower() == "print":
                return context.write(*arguments)
            elif function.lower() == "range":
                return range(*arguments)
            elif function.lower() == "read":
                if not arguments:
                    raise "Read must have one argument."
                return IOHelper.read(arguments[0])
            elif function.lower() == "write":
                if len(arguments) < 2:
                    raise "Write must have two arguments."
                return IOHelper.write(arguments[0], arguments[1])
            elif function.lower() == "get_files":
                return IOHelper.get_files(arguments[0])
            elif function.lower() == "get_folders":
                return IOHelper.get_folders(arguments[0])
            elif function.lower() == "remove":
                return IOHelper.remove(arguments[0])
            elif function.lower() == "makedirs":
                return IOHelper.makedirs(arguments[0])
            elif function.lower() == "reduce_noise":
                return ImageProcessor.reduce_noise(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]))
            elif function.lower() == "convert_color":
                return ImageProcessor.convert_color(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), arguments[2])
            elif function.lower() == "register_image":
                return ImageProcessor.register_image(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), path.join(localdir, arguments[2]))
            elif function.lower() == "exec":
                return func_exec_run(arguments[0], *arguments[1:])
            #    return func_exec(arguments[0], *arguments[1:])
            else:
                raise "{0} function not implemented".format(function)
    #             possibles = globals().copy()
    #             possibles.update(locals())
    #             function = possibles.get(function)
    #             return function(*arguments)
        else:           
            module_obj = load_module(module_name)
            function = getattr(module_obj, function)
            return function(*arguments)

    def code_func(self, context, package, function, arguments):
        '''
        Call a function from a module.
        :param context: The context for output and error
        :param package: The name of the package. If it's empty, local function is called    
        :param function: Name of the function
        :param arguments: The arguments for the function
        '''
        if not package or package == "None":
            if function.lower() == "print":
                return context.write(*arguments)
            elif function.lower() == "range":
                return range(*arguments)
            elif function.lower() == "read":
                if not arguments:
                    raise "Read must have one argument."
                return IOHelper.read(arguments[0])
            elif function.lower() == "write":
                if len(arguments) < 2:
                    raise "Write must have two arguments."
                return IOHelper.write(arguments[0], arguments[1])
            elif function.lower() == "get_files":
                return IOHelper.get_files(arguments[0])
            elif function.lower() == "get_folders":
                return IOHelper.get_folders(arguments[0])
            elif function.lower() == "remove":
                return IOHelper.remove(arguments[0])
            elif function.lower() == "makedirs":
                return IOHelper.makedirs(arguments[0])
            elif function.lower() == "reduce_noise":
                return ImageProcessor.reduce_noise(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]))
            elif function.lower() == "convert_color":
                return ImageProcessor.convert_color(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), arguments[2])
            elif function.lower() == "register_image":
                return ImageProcessor.register_image(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), path.join(localdir, arguments[2]))
            elif function.lower() == "exec":
                return func_exec_run(arguments[0], *arguments[1:])
            #    return func_exec(arguments[0], *arguments[1:])
            else:
                raise "{0} function not implemented".format(function)
    #             possibles = globals().copy()
    #             possibles.update(locals())
    #             function = possibles.get(function)
    #             return function(*arguments)
        else:           
            module_obj = load_module(module_name)
            function = getattr(module_obj, function)
            return function(*arguments)
            
    def __repr__(self):
        return "Library: " + repr(self.funcs)
    def __getitem__(self, key):
        return self.funcs[key]
    def __setitem__(self, key, val):
        self.funcs[key] = val
    def __delitem__(self, key):
        del self.funcs[key]
    def __contains__(self, key):
        return key in self.funcs
    def __iter__(self):
        return iter(self.funcs.keys())
    
    def __str__(self):
        funcs = []
        for k, v in self.funcs.items():
            funcs.extend(v)
            
        if len(funcs) > 0:
            mod_name = "Module name"
            mod_len = max(max(len(i.module) if i.module is not None else 0 for i in funcs), len(mod_name))
         
            internal_name = "Internal Name"
            internal_len = max(max(len(i.internal) for i in funcs), len(internal_name))
            
            func_name = "Function Name"
            func_len = max(max(len(i.name) for i in funcs), len(func_name))
           
            param_names = "Parameters"
            param_len = len(param_names)
            l = 0
            for a in funcs:
                for v in a.params:
                    l += len(v)
                param_len = max(param_len, l)
            
            # print table header for vars
            display = "\n\n{0:3s} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}s}".format(" No", mod_name, mod_len, internal_name, internal_len, func_name, func_len, param_names, param_len)
            display += ("\n-------------------" + "-" * (mod_len + internal_len + func_len + param_len))
            # print symbol table
            
            i = 1
            for v in funcs:
                module = v.module if v.module is not None else "None"
                parameters = ""
                for p in v.params:
                    if parameters == "":
                        parameters = "{0}".format(p)
                    else:
                        parameters += ", {0}".format(p)
                display += "\n{0:3d} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}s}".format(i, module, mod_len, v.internal, internal_len, v.name, func_len, parameters, param_len)
                
                i += 1
                
        return display
