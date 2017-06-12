from importlib import import_module
from fileop import IOHelper
#from imgproc.imagefuncs import ImageProcessor
from os import path

from subprocess import Popen, PIPE, STDOUT, run

#from phenoparser import Context

def func_exec(app, *args):

    cmd = app
    if args:
        cmd += ' ' + ' '.join(args)
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=False)
    return p.stdout.read()

def func_exec_run(*args):
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
    
def call_func(context, module_name, func_name, arguments):
    '''
    Call a function from a module.
    :param context: The context for output and error
    :param module_name: The name of the module. If it's empty, local function is called    
    :param func_name: Name of the function
    :param arguments: The arguments for the function
    '''
    
    localdir = path.join(path.abspath(path.dirname(__file__)), 'storage')
    
    if not module_name or module_name == "None":
        if func_name.lower() == "print":
            return context.write(*arguments)
        elif func_name.lower() == "range":
            return range(*arguments)
        elif func_name.lower() == "read":
            if not arguments:
                raise "Read must have one argument."
            return IOHelper.read(arguments[0])
        elif func_name.lower() == "write":
            if len(arguments) < 2:
                raise "Write must have two arguments."
            return IOHelper.write(arguments[0], arguments[1])
        elif func_name.lower() == "get_files":
            return IOHelper.get_files(arguments[0])
        elif func_name.lower() == "get_folders":
            return IOHelper.get_folders(arguments[0])
        elif func_name.lower() == "remove":
            return IOHelper.remove(arguments[0])
        elif func_name.lower() == "makedirs":
            return IOHelper.makedirs(arguments[0])
        elif func_name.lower() == "reduce_noise":
            return ImageProcessor.reduce_noise(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]))
        elif func_name.lower() == "convert_color":
            return ImageProcessor.convert_color(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), arguments[2])
        elif func_name.lower() == "register_image":
            return ImageProcessor.register_image(path.join(localdir, arguments[0]), path.join(localdir, arguments[1]), path.join(localdir, arguments[2]))
        elif func_name.lower() == "exec":
            return func_exec_run(arguments[0], *arguments[1:])
        #    return func_exec(arguments[0], *arguments[1:])
        else:
            raise "{0} function not implemented".format(func_name)
#             possibles = globals().copy()
#             possibles.update(locals())
#             function = possibles.get(func_name)
#             return function(*arguments)
    else:           
        module_obj = load_module(module_name)
        function = getattr(module_obj, func_name)
        return function(*arguments)