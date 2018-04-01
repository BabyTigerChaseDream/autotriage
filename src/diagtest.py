#!/usr/bin/python3

# private module 
from fdfetcher import *
from testparser import *

# OS module 
import subprocess as sub 
import os

"""
receive info from uuid parser, deal with different kinds of failure 
- notrun : rerun (check historyof test and build/hw see if hw issue)
- aborted :  same as above 
"""

global testCmd 
# TODO: [advance] force-test-system/force-build-system/
testCmd = "vulcan -v --eris -user jiag --product={vlcp} --target-gpu {gpu} --target-os {os} --target-arch {arch} --testsuite {tsuite} --target-revision=cl-{commit} --tags {tags}"

# can interact with user 
# to change vulcan cmd param
"""
 func : rerun deal with notrun(subtimeout)/failed(BADINSTALL)/aborted test 
"""
""" TestList: 
    ==> {'resu': 'notrun', 'tsuite': 'cudnn_layer_tests', 'log': None, 'cid': ('gp100sxm2', 'ppc64le', 'RHEL7_3'), 'info': 'Dependency Failed', 'hw': None}
"""
def reRun(TestEntry, vlcp, interact=False, cl='tot'):
    # can groupby same [suite]/os/gpu together and submit all in one 
    ### expand "cid" 
    gpu,os,arch,tsuite,resu,info = *TestEntry['cid'],TestEntry['tsuite'],TestEntry['resu'],TestEntry['info'], 
    # TODO: name a good tag - like unique ID 
    tags ='#'.join((gpu,os,arch,tsuite,resu,info)) 
    #cmdlind = testCmd.format_map(vars())
    cmdlind = "vulcan -v --eris -user jiag --product={vlcp} --target-gpu {gpu} --target-os {os} --target-arch {arch} --testsuite {tsuite} --target-revision=cl-{commit} --tags {tags}".format_map(vars())
    print(cmdline)
    # TODO: os.system ?
    return cmdline

### download log and parse it ###
def DownloadFd(TestEntry, uuid):
    {'fdlink':''.join(("http://eris-fs000/logs/",uuid)),'log':'*'.join((TestEntry['hw'],TestEntry['log'],'zip')),'path':''.join(("/home/jia/workspace/download/triage/logs/",uuid))}
    serverDir = ''.join(("http://eris-fs000/logs/",uuid))
    pattern = '*'.join((TestEntry['hw'],TestEntry['log'],'zip'))
    localDir = ''.join(("/home/jia/workspace/download/triage/logs/",uuid))
    log = TestEntry['log']
    # called module fdfetcher's "func:: wget"
    # wget(serverDir,pattern,localDir)
    os.system("wget -r -l1 --no-parent --cut-dirs=10 -nH -np -A \"{pattern}\" {serverDir} -P {localDir}".format_map(vars()))
    # TODO : get real fd name, no "*" in it 
    cmd = "ls {localDir} | grep {log}".format_map(vars())
    proc=sub.Popen(cmd, bufsize=1, shell=True, stdout=sub.PIPE)
    # get stdout/stderr
    stdout,stderr = proc.communicate()
    return stdout.decode('utf-8') 

""" get full local log path : def DownloadFd(TestEntry, uuid) 
    Then pass it to "testparser.py" -> [func] TestFilter
"""

    
"""
 Handler to filter Test Table as expected 
"""
