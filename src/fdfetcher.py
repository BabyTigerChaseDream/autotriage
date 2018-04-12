#!/usr/bin/python3

'''
1.This file auto download file from http path
2.make local path 
3.unzip log , remove zip
'''
################################################
# -trg <http path> -uuid <num> -pat <file pattern/name> (default path: /ws/fd/triage/uuid)
# -rel <http path> -i <rel ver> -pat <file pattern/name> (default path: /ws/fd/rel/uuid)
################################################

# OS module 
import sys, os, errno
import subprocess as sub 

dbg =True 

# download servevr 
global trgServer
trgServer = "http://eris-fs000/logs/"
global RelServer
RelServer = {
    'cuda' : "http://dlswqa.nvidia.com/sw/cuda/",
    #'cuda' : "http://cuda-repo/release-candidates/9.0/candidates/Prod/07/local_installers/",
    'cudnn' : "http://cuda-repo/release-candidates/Libraries/cuDNN/v7.1/",
    # TODO needs user/pw:  --user=swqa --password=test
    'drv' : "http://10.19.193.206/teslaswqash_manual/UDA/"
}

# local path  
global locTrgdir 
locTrgdir = "/home/jia/workspace/download/triage/logs/"
global locReldir 
locReldir = "/home/jia/workspace/download/rel/img/"
global locPrivDir 
locPrivDir = "/home/jia/workspace/download/priv/"

# local dir settting for file download
def MakeDir(localDir):
    if dbg:
        print('localDir:',localDir)
    try:
        os.makedirs(localDir)
        if dbg:
            print('success make dir:',localDir)
    # if dir exist, quit makedir
    # else fail due to other errors , raise error 
    except OSError as e:
        if e.errno != errno.EEXIST:
            localDir = None
            raise
        else:
            # clear ALL (log) files in localDir
            # TODO : check file needs overwrite 
            #os.chdir(localDir)
            #os.system('rm *.log -rf')
            print("Path \" {localDir} \" already exist:".format_map(vars()))

    return localDir
    
# wget file (parent/child param)
def wget(serverDir,pattern,localDir):
    if dbg:
        print('serverDir:',serverDir)
        print('pattern:',pattern)
        print('localDir:',localDir)
        # get file by pattern only
        # wget -r --no-parent --cut-dirs=4 -A libcudnn7*7.1.2.21* http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64/
    if pattern:
        # if pattern specified
        # --cut-dirs set "super large" Num
        cmd = "wget -r -l1 --no-parent --cut-dirs=10 -nH -np -A \"{pattern}\" {serverDir} -P {localDir}".format_map(vars())
    else:
        # download all files in http , if no pattern specified  
        cmd = "wget -r -nH -np --cut-dirs=10 -R \"index.html*\" {serverDir} -P {localDir}".format_map(vars())

    if dbg:
        print('cmd ==>\n',cmd)
    os.system(cmd)    

    # display all file when done 
    cmdshow = "ls -al {localDir}".format_map(vars())
    os.system(cmdshow)

    # exec cmd at localDir , for unzip 
    os.chdir(localDir)
    # unzip all zip files in localDir(must be absolute path)
    for item in os.listdir(localDir):
        if item.endswith('.zip'):
            cmd="unzip %s && rm %s" % (item,item)
            #print('unzip ==> ',cmd)
            os.system(cmd)            
    # display all file when done 
    print("\n")
    print("/ ***** File at {localDir} ***** /".format_map(vars()))
    print("\n")
    cmdshow = "ls -al {localDir}".format_map(vars())
    os.system(cmdshow)

""" get full local log path : def DownloadFd(TestEntry, uuid) 
    Then pass it to "testparser.py" -> [func] TestFilter
"""
### download log and parse it ###
def DownloadFd(TestEntry, uuid):
    serverDir = os.path.join("http://eris-fs000/logs/",uuid)
    # some file is HUGE , ends with log NOT zip , so in "pattern" , used * instead 
    pattern = '*'.join((TestEntry['hw'],TestEntry['log'],'*'))

    localDir = os.path.join("/home/jia/workspace/download/triage/logs/",uuid)
    log = TestEntry['log']
    # called module fdfetcher's "func:: wget"
    # wget(serverDir,pattern,localDir)
    os.system("wget -r -l1 -R \"index.*\" --no-parent --cut-dirs=10 -R \"index.html*\" -nH -np -A \"{pattern}\" {serverDir} -P {localDir}".format_map(vars()))

    # exec cmd at localDir , for unzip 
    os.chdir(localDir)
    # unzip all zip files in localDir(must be absolute path)
    for item in os.listdir(localDir):
        if item.endswith('.zip'):
            cmd="unzip %s && rm %s" % (item,item)
            #print('unzip ==> ',cmd)
            os.system(cmd)  

    # TODO : get real fd name, no "*" in it , use glob/fmatch ?
    #cmd = "ls {localDir} | grep {log}".format_map(vars())
    # needs 2 wildcat "*"
    cmd = "find {localDir} -name *{log}*.log".format_map(vars())
    print("[cmd] ", cmd)
    proc=sub.Popen(cmd, bufsize=1, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    # get stdout/stderr
    stdout,stderr = proc.communicate()
    if stdout is None:
        print("[!!!] {log} download FAILED [!!!]".format_map(vars()))
    
    return localDir,stdout.decode('utf-8').strip()

####################
#####   main   #####
####################
if __name__=="__main__":
    import argparse
    parent_parser = argparse.ArgumentParser(description='fetch files from server')
    #parent_parser.add_argument('-show', action='store_true', dest='show', default=None, help='show default link')
    # download file pattern: name/pattern; default is None (download all file in folder)
    parent_parser.add_argument('-fd', action='store', dest='fdpat', default=None, help='file regex pattern')
    parent_parser.add_argument('-dir', action='store', dest='dir', default=None, help='specify dir to put file')
    parent_parser.add_argument('-http', action='store', dest='http', default=None, help='specify download link')

    subparsers = parent_parser.add_subparsers(dest='type')
    #group = subparsers.add_mutually_exclusive_group(required=True)
    # http link 
    parser_release = subparsers.add_parser('rel')
    parser_triage = subparsers.add_parser('tr')
    #parser_priv = subparsers.add_parser('priv')

    # default link: Eris - uuid
    parser_triage.add_argument('-u', action='store', dest='uuid', default=None,help='uuid')
    parser_triage.add_argument('-l', action='store', dest='link', default=None, help='specify download link')
    
    # depends on -r : cuda/drv/cudnn set default link 
    parser_release.add_argument('-c', action='store', dest='comp', default=None, choices=['cuda', 'cudnn', 'drv'], help='component (cuda/cudnn/drv) to download')
    parser_release.add_argument('-l', action='store', dest='link', default=None, help='specify download link')

    # must has default link
    #parser_priv.add_argument('-l', action='store', dest='link', default=None, help='customized download link')
    #parser.add_argument('-d', action='store', dest='dir',help='local dir')
    
    arglist=parent_parser.parse_args()
    print(parent_parser.parse_args())

    # handle different type of download  
    global WgetLink, pattern, LocDir

    fileType = arglist.type
    if fileType == 'tr':
        WgetLink=(trgServer+arglist.uuid if arglist.link == None else arglist.link)
        LocDir = (locTrgdir+arglist.uuid if arglist.dir== None else arglist.dir)
    elif fileType == 'rel':
    # TODO : need parse "RelServer" further 
        WgetLink=(RelServer[arglist.comp] if arglist.link == None else arglist.link)
        LocDir = (locReldir if arglist.dir== None else arglist.dir)
    else:
    # default needs http link from user 
        if arglist.http == None:
            raise ValueError("-http must be specified in priv download !!! ")
            
        WgetLink = arglist.http
        LocDir = (locPrivDir if arglist.dir== None else arglist.dir)
        
    pattern = arglist.fdpat
    
    # calling func 
    MakeDir(LocDir)
    wget(WgetLink, pattern, LocDir)
