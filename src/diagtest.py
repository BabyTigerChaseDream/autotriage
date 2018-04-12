#!/usr/bin/python3

# private module 
from fdfetcher import *
from testparser import *


"""
receive info from uuid parser, deal with different kinds of failure 
- notrun : rerun (check historyof test and build/hw see if hw issue)
- aborted :  same as above 
"""

global testCmd 
# TODO: [advance] force-test-system/force-build-system/
testCmd = "vulcan -v --eris -user jiag --product={vlcp} --target-gpu {gpu} --target-os {os} --target-arch {arch} --testsuite {suite} --target-revision=cl-{commit} --tags {tags}"

# can interact with user 
# to change vulcan cmd param
"""
 func : rerun deal with notrun(subtimeout)/failed(BADINSTALL)/aborted test 
"""
""" TestList: 
    ==> {'resu': 'notrun', 'suite': 'cudnn_layer_tests', 'log': None, 'cid': ('gp100sxm2', 'ppc64le', 'RHEL7_3'), 'info': 'Dependency Failed', 'hw': None}
"""
def reRun(TestEntry, vlcp, interact=False, cl='tot'):
    # can groupby same [suite]/os/gpu together and submit all in one 
    ### expand "cid" 
    gpu,os,arch,suite,resu,info = *TestEntry['cid'],TestEntry['suite'],TestEntry['resu'],TestEntry['info'], 
    # TODO: name a good tag - like unique ID 
    tags ='#'.join((gpu,os,arch,suite,resu,info)) 
    #cmdlind = testCmd.format_map(vars())
    cmdlind = "vulcan -v --eris -user jiag --product={vlcp} --target-gpu {gpu} --target-os {os} --target-arch {arch} --testsuite {suite} --target-revision=cl-{commit} --tags {tags}".format_map(vars())
    print(cmdline)
    # TODO: os.system ?
    return cmdline

"""
 Handler to filter Test Table as expected 
"""
