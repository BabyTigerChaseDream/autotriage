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
import os 

# data parse module
from collections import namedtuple

"""
Private module for triage 
"""
from fdfetcher import *
from testparser import *
from uuidparser import *
from difftest import *
#from diagtest import *

####################
#####   main   #####`
####################
if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Auto Parse Eris uuid: test/build results')
    # show command group 
    parser.add_argument('-u', action='store', dest='uuid', default=None, help='Eris uuid')
    # show diff param 
    # -c will be passed as "list" easy to handle by "set()"
    parser.add_argument('-com', action='store', dest='combo', default=None, help='suitename,configID : combination')
    parser.add_argument('-unew', action='store', dest='uuidnew', default=None, help='Newer uuid')
    parser.add_argument('-uold', action='store', dest='uuidold', default=None, help='old uuid')
    #parser.add_argument('-t', action='store', dest='tag', default=None, required=True, help='test tag:new/old/fixed failure')

    parser.add_argument('-f', action='store_true', dest='force', default=False, help='force pull data from url')
    # TODO: regex format "-k"
    parser.add_argument('-k', action='store', dest='keyword', default=None, choices=['passed','failed','notrun','aborted'], help='\'resu\' keyword filter:notrun/failed/passed/aborted/ ')
    parser.add_argument('-d', action='store_true', dest='detail', default=False, help='list testid/err in suites')
    # TODO: to restrict -s to follow "show suite only "
    # suite name -- show one suite 
    # TODO: supports list param 
    parser.add_argument('-n', action='store', dest='name', default=None, help='select test suite to parse')
    # mutual exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sh', action='store', dest='show', default=None, choices=['build','test','suite'], help='show specify result:test/build/suite')
    group.add_argument('-diff', action='store', dest='diff', default=None, choices=['build','test'], help='diff between 2 tests/build')
    group.add_argument('-exec', action='store', dest='exec', default=None, help='submit test/build cmdline to Eris')
    
    arglist=parser.parse_args()
    print(parser.parse_args())

    """
    ARG Parsing starts
    """
    uuid = arglist.uuid
    # TODO : better exclusive subparam among(sh/diff/exec)
    """ 
        'show cmd' support 
        ->  -sh test
        ->  -sh suite -n "suitename"
    """
    if arglist.show:
    #TODO : keep uuid overall result table:: load once and ONLY once !!!
        if arglist.show == 'test':
            print('============ Overall =============')
            for t in GetCompleteTestList(uuid, keyword=arglist.keyword, force=arglist.force):
                print(t['suite'],t['resu'],t['info'],t['cid'],t['hw'],t['log'], sep=' | ')

            print('=====================================')
            # sub-arg for "show test"
        elif arglist.show == 'suite':
            DnldTuple = namedtuple('DnldTuple', ['suite','cid','pathlog'])
            download_list = []
            if arglist.name:
                for t in GetCompleteTestList(uuid, "failed"):
                # TODO : change arglist.suite to support list 
                    # failed with Eris Infra , no log 
                    # [Note] When transferred by csv , element will be '' (empty string)
                    if arglist.name in t['suite'] and \
                        t['hw'] and \
                        t['log']: 
                        download_list.append(DnldTuple(t['suite'],t['cid'],DownloadFd(t, uuid, force=arglist.force)))
            # else download all failed suite name's log 
            else:
                for t in GetCompleteTestList(uuid, "failed"):
                    # failed with Eris Infra , no log , 'hw':None/'log':None
                    # [Note] When transferred by csv , element will be '' (empty string)
                    if t['hw'] and t['log']:
                        download_list.append(DnldTuple(t['suite'],t['cid'],DownloadFd(t, uuid, force=arglist.force)))
            
            print('====== Download Done !!! ====== \n')

            for d in download_list:
                print('####################\n[##### SUM TABLE #####]',d.suite,d.cid)
                # TODO: optimize data structure 
                # os.path.join() argument must be str or bytes, not 'tuple'
                TestFilter(os.path.join(*d.pathlog),'FAILED',detail=arglist.detail)
            
        elif arglist.show == 'build':
            for t in GetCompleteBuildList(uuid, arglist.keyword):
                print(t['resu'],t['info'],t['comp'],t['cid'],t['hw'],t['log'], sep=' | ')
        else:
            pass
    ############################################################################################
    #### Diff 'cmd' support 
    ####    ->  -diff -unew [new uuid] -uold [old uuid] -com [suite,config] -t [new/old/fixed]
    ############################################################################################
    # TODO: optimize search algo 
    elif arglist.diff:
        pass
    #    fd_uuidnew = ''
    #    fd_uuidold = ''
    #    print('[DBG] combo is:',arglist.combo)
    #    # Get new uuid log
    #    for t in GetCompleteTestList(arglist.uuidnew):
    #        newCombo = (arglist.combo).split(',')
    #        if set(newCombo) in set((t['suite'],t['cid'])):
    #            fd_uuidnew = os.path.join(DownloadFd(t, uuidnew))
    #            print('[DBG] fd_uuidnew is:',fd_uuidnew)
    #    # Get old uuid log
    #    for t in GetCompleteTestList(arglist.uuidold):
    #        oldCombo = (arglist.combo).split(',')
    #        if set(oldCombo) in set((t['suite'],t['cid'])):
    #            fd_uuidold = os.path.join(DownloadFd(t, uuidold))
    #            print('[DBG] fd_uuidold is:',fd_uuidold)                

    #    # start compare 
    #    DiffTests(fd_uuidnew,fd_uuidold)
