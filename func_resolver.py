from importlib import import_module
from phenoparser import Context

def load_module(modulename):
    #if modulename not in sys.modules:
    #name = "package." + modulename
    #return __import__(modulename, fromlist=[''])
    return import_module(modulename)
    
def call_func(context, module_name, func_name, arguments):
    if not module_name or module_name == "None":
        if func_name == "print".lower():
            return context.write(*arguments)
        if func_name == "range".lower():
            return range(*arguments)
        possibles = globals().copy()
        possibles.update(locals())
        function = possibles.get(func_name)
        return function(*arguments)
    else:
        module_obj = load_module(module_name)
        function = getattr(module_obj, func_name)
        return function(*arguments)