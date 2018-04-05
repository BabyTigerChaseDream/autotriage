#!/usr/bin/python3

"""
autotriage provide cmdline for triage nightly failures

- "show command" (show test results option arg: -d for detail):
    -test all/failed/passed/.../(aborted|notrun)  --> regex supported
     (-test failed -name L3 ... -> specify a suite)
    -build all/failed/depend failed ...
    -suite all/[suitename] 
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
#####   main   #####`
####################
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Auto Parse Eris uuid: test/build results')
    # show command group 
    parser.add_argument('-u', action='store', dest='uuid', default=None, required=True, help='Eris uuid')
    # TODO: regex format "-k"
    parser.add_argument('-k', action='store', dest='keyword', default=None, help='keyword filter contents')
    # TODO: to restrict -s to follow "show suite only "
    # suite name -- show one suite 
    parser.add_argument('-s', action='store', dest='suite', nargs='+', help='select test suite to show detail')
    # mutual exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sh', action='store', dest='show', default=None, choices=['build','test','suite'], help='show specify dataset')
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
    #TODO : keep uuid overall result table:: load once and ONLY once !!!
        if arglist.show == 'test':
            for t in GetCompleteTestList(uuid, arglist.keyword):
                print(t['tsuite'],t['resu'],t['info'],t['cid'],t['hw'],t['log'], sep=' | ')
                #print(t.values())
        elif arglist.show == 'build':
            for t in GetCompleteBuildList(uuid, arglist.keyword):
                print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')
        # show suite supports fail log download/parse only 
        # no need to parse PASS log 
        elif arglist.show == 'suite':
            if arglist.suite:
                for t in filter(lambda l:arglist.suite in l['tsuite'],GetCompleteTestList(uuid)):
                    print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')
            # else download all failed suite's log file 
            else:
                for t in filter(lambda l:arglist.keyword in l['tsuite'],GetCompleteTestList(uuid)):
                    print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')

