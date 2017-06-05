from importlib import import_module
from fileop import IOHelper

#from phenoparser import Context

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
    if not module_name or module_name == "None":
        if func_name.lower() == "print":
            return context.write(*arguments)
        elif func_name.lower() == "range":
            return range(*arguments)
        elif func_name.lower() == "read":
            if not arguments:
                raise "Read must have one argument."
            return IOHelper.read(arguments[0])
        elif func_name.lower() == "get_files":
            return IOHelper.get_files(arguments[0])
        elif func_name.lower() == "get_folders":
            return IOHelper.get_folders(arguments[0])
        elif func_name.lower() == "remove":
            return IOHelper.remove(arguments[0])
        elif func_name.lower() == "makedirs":
            return IOHelper.makedirs(arguments[0])
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