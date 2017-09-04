import os
from os import path
from exechelper import func_exec_run

localdir = path.join(path.dirname(path.dirname(path.dirname(__file__))), 'storage')
flash = path.join(path.abspath(path.dirname(__file__)), path.join('bin', 'pear'))

def run_flash(*args):
    input1 = path.join(localdir, args[0])
    input2 = path.join(localdir, args[1])
    cmdargs = []
    if len(args) > 2:
        cmdargs.append("-d {0}".format(path.join(localpath, args[2])))
    
    if len(args) > 3:
         cmdargs.append(" -M " + str(args[3]))
    
    for arg in args[4:]:
        cmdargs.append(arg)
            
    cmdargs.append(input1)
    cmdargs.append(input2)

    return func_exec_run(flash, *cmdargs)

def run_flash_recursive(*args):
    #assign arguments 
    input_path = path.join(localdir, args[0])
    if len(args) > 1:
        output_path = path.jon(localdir, args[1])
        log_path = path.join(output_path, "log")
    if len(args) > 2:
        max_overlap = args[2]
    
    if not os.path.exists(output_path): 
        os.makedirs(output_path) 
    
    if not os.path.exists(log_path): 
        os.makedirs(log_path) 

    #create list of filenames 
    filenames = next(os.walk(input_path))[2] 
    filenames.sort() 
    
    #divide forward and reverse read files into sepeate lists 
    R1 = list() 
    R2 = list() 

    for files1 in filenames[::2]: 
        R1.append(files1)  
    
    for files2 in filenames[1:][::2]: 
        R2.append(files2) 
    
    #iterate through filenames and call Flash joining  
    
    if len(R1) != len(R2):
        raise "R1 and R2 different lengths"
    
    for i in range(len(R1)):
        if R1[i][:-12] == R2[i][:-12]:
            args = []
            args.append(" -M " + str(max_overlap))
            args.append(" -d " + output_path)
            args.append(" -o " + R1[i][:-12])
            args.append(input_path + R1[i])
            args.append(input_path + R2[i])
            output = func_exec_run(flash, *args)
            
            output_file = path.join(log_path, R1[i][:-12] + ".flash.log")
            
            with open(output_file, 'a+') as f:
                f.write(output)
    
    return log_path