import os
from os import path
from exechelper import func_exec_run

localdir = path.join(path.dirname(path.dirname(path.dirname(__file__))), 'storage')
pear = path.join(path.abspath(path.dirname(__file__)), path.join('bin', 'pear'))

def run_pear(*args):
    forward_fastq = "-f {0}".format(path.join(localdir, args[0]))
    reverse_fastq = "-r {0}".format(path.join(localdir, args[1]))
    cmdargs = [forward_fastq, reverse_fastq]
    if len(args) > 2:
        cmdargs.append("-o {0}".format(path.join(localpath, args[2])) )
    func_exec_run(pear, *cmdargs)
    return path.join(localdir, args[2])
    