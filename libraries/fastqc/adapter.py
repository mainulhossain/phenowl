import os
from os import path
from exechelper import func_exec_run

localdir = path.join(path.dirname(path.dirname(path.dirname(__file__))), 'storage')
fastqc = path.join(path.abspath(path.dirname(__file__)), path.join('lib', 'fastqc'))

def run_fastqc(*args):
    input = path.join(localdir, args[0])
    cmdargs = [input]
    outdir = path.dirname(input)
    if len(args) > 1:
        outdir = path.join(localpath, args[1]) 
        cmdargs.append("--outdir={0}".format(outdir))
    func_exec_run(fastqc, *cmdargs)
    outname = path.basename(input)
    outname = outname.split(os.extsep)[0] + "_fastqc.html"
    return path.join(outdir, outname)
    