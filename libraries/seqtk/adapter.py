import os
from os import path
from exechelper import func_exec_run

localdir = path.join(path.dirname(path.dirname(path.dirname(__file__))), 'storage')
seqtk = path.join(path.abspath(path.dirname(__file__)), path.join('bin', 'seqtk'))

def run_seqtk(*args):
    input = path.join(localdir, args[0])
    command = args[1]
    output = path.join(localdir, args[2])
    
    cmdargs = [command]
    for arg in args[3:]:
        cmdargs.append(arg)
            
    cmdargs.append(input)

    outdata = func_exec_stdout(seqtk, *cmdargs)
    with open(output, 'w') as f:
        f.write(outdata)
    return output