#!/usr/bin/python3

"""
autotriage provide cmdline for triage nightly failures

- "show command" (show test results option arg: -d for detail):
    -test all/failed/passed/.../(aborted|notrun)  --> regex supported
     (-test failed -name L3 ... -> specify a suite)
    -build all/failed/depend failed ...
    -command
    -config
- "diff command" (diff test set )
    -uuid "uuid1" "uuid2" (diff 2 uuid's results: dict &|)
    -testcid "testsuite_cid1" "testsuite_cid2" (diff 2 testsuite's result)
- "exec command" (exec command to run)
     [] required  <> optional 
    -testcid [tags] <cl-num> <hw> <apply-change>  (default => cl-num:tot / hw:chosen by Eris )
"""


"""
standard Python module
"""
import argparse 

"""
Private module for triage 
"""
from fdfetcher import *
from testparser import *
from uuidparser import *

####################
#####   main   #####
####################
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Auto Parse Eris uuid: test/build results')
    # show command group 
    parser.add_argument('-u', action='store', dest='uuid', default=None, required=True, help='Eris uuid')
    # TODO: regex format "-k"
    parser.add_argument('-k', action='store', dest='keyword', default=None, help='keyword filter contents')
    # mutual exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sh', action='store', dest='show', default=None, choices=['build','test'], help='show specify dataset')
    group.add_argument('-diff', action='store', dest='diff', default=None, choices=['build','test'], help='diff between 2 tests/build')
    group.add_argument('-exec', action='store', dest='exec', default=None, help='submit test/build cmdline to Eris')
    
    arglist=parser.parse_args()
    print(parser.parse_args())

    """
    ARG Parsing starts
    """
    uuid = arglist.uuid
    # TODO : better exclusive subparam among(sh/diff/exec)
    if arglist.show:
        if arglist.show == 'test':
            if arglist.keyword:
                for t in filter(lambda l:arglist.keyword in l['resu'],GetCompleteTestList(uuid)):
                    print(t['resu'],t['info'],t['tsuite'],t['cid'],t['hw'],t['log'], sep=' | ')
            else:
                for t in GetCompleteTestList(uuid):
                    print(t['resu'],t['info'],t['tsuite'],t['cid'],t['hw'],t['log'], sep=' | ')
        elif arglist.show == 'build':
            if arglist.keyword:
                for t in filter(lambda l:arglist.keyword in l['resu'],GetCompleteBuildList(uuid)):
                    print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')
            else:
                for t in GetCompleteBuildList(uuid):
                    print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')
