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
from cmdparser import *
#from diagtest import *

cudnn_path_dict = {
            # TODO : weekly
            'CUDNN V7.1 CUDA 9.2 r396':'v71_r92_r396',
            'CUDNN V7.1 CUDA 9.1 r390':'v71_r91_r390',
            'CUDNN V7.1 CUDA 9.0 r384':'v71_r90_r384',
            'CUDNN V7.1 CUDA 8.0 r375':'v71_r80_r375',
            # TODO : v7.1 weekly
            'CUDNN DEV GPGPU CUDA_A':'cudnn_gpgpu_cuda_a',

            'CUDNN 7.2 CUDA 9.2 r396':'v72_r92_r396',
            'CUDNN V7.2 CUDA 9.0 r384':'v72_r90_r384',
            'CUDNN V7.2 CUDA 8.0 r375':'v72_r80_r375',
            'CUDNN 7.2 CUDA 10.0 r400':'v72_r100_r400'
            }
            
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

    # sub for "-get cl", usage : "-ele ]=cudnn"
    # support lists of elements: cudnn,cudn_tests,]=cudnn ... 
    parser.add_argument('-ele', action='store', dest='element', nargs='+',default=None, help='element to delta CL')
    parser.add_argument('-clrange', action='store', dest='clrange', default=None, help='CL ranges to delta: in form of 123,456 ')

    # TODO: to restrict -s to follow "show suite only "
    # suite name -- show one suite 
    # TODO: supports list param 
    parser.add_argument('-n', action='store', dest='name', default=None, help='select test suite to parse')
    # mutual exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-sh', action='store', dest='show', default=None, choices=['build','test','suite'], help='show specify result:test/build/suite')
    group.add_argument('-diff', action='store', dest='diff', default=None, choices=['build','test'], help='diff between 2 tests/build')
    
    # cmd / cl in vul
    group.add_argument('-get', action='store', dest='get', default=None, choices=['cmd','cl','cfg'], help='get needs re-run eris cmdline/cl number/config ')
    
    ############# temp solution for vulMT triage cmd  #############
    group.add_argument('-trg', action='store_true', dest='trg', default=False, help='submit vul to test ')
    # show command group for "-trg" 
    parser.add_argument('-cl', action='store', dest='cllist', default=None, help='CL numbers to run, inform of 1,2,3 ')    
    # note: -cmd must quote by " 
    parser.add_argument('-cmd', action='store', dest='cmdline', default=None, help='full vul cmdline')    
    parser.add_argument('-t', action='store', dest='tags', default=None, help='tags in cmdline')     

    arglist=parser.parse_args()
    print(parser.parse_args())

    """
    ARG Parsing starts
    """
    uuid = arglist.uuid

    print('============ UUID Info =============')
    (uuid, prod, testdate, user, uuidCL, tags) = UUIDInfo(uuid) 
    print((uuid, prod, testdate, user, uuidCL, tags))
    LocDir = os.path.join(locTrgdir,cudnn_path_dict[prod],arglist.uuid)

    # TODO : better exclusive subparam among(sh/diff/exec)
    """ 
        'show cmd' support 
        ->  -sh test
        ->  -sh suite -n "suitename"
    """
    if arglist.show:
    #TODO : keep uuid overall result table:: load once and ONLY once !!!
        if arglist.show == 'test':

            print("[DBG] Making LocDir:",LocDir)
            MakeDir(LocDir)
            print('============ Overall =============')
            for t in GetCompleteTestList(uuid, LocDir,keyword=arglist.keyword, force=arglist.force):
                print(t['suite'],t['resu'],t['info'],t['cid'],t['hw'],t['log'], sep=' | ')

            print('=====================================')
            # sub-arg for "show test"
        elif arglist.show == 'suite':
            DnldTuple = namedtuple('DnldTuple', ['suite','cid','pathlog'])
            download_list = []
            if arglist.name:
                for t in GetCompleteTestList(uuid, LocDir,"failed", force=arglist.force):
                # TODO : change arglist.suite to support list 
                    # failed with Eris Infra , no log 
                    # [Note] When transferred by csv , element will be '' (empty string)
                    if arglist.name in t['suite'] and \
                        t['hw'] and \
                        t['log']: 
                        download_list.append(DnldTuple(t['suite'],t['cid'],DownloadFd(t, uuid, force=arglist.force)))
            # else download all failed suite name's log 
            else:
                for t in GetCompleteTestList(uuid, LocDir,"failed", force=arglist.force):
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
        print('============ new UUID Info =============')
        print(UUIDInfo(arglist.uuidnew))
        print('============ old UUID Info =============')
        print(UUIDInfo(arglist.uuidold))
        newResuList = GetCompleteTestList(arglist.uuidnew, LocDir,force=arglist.force)
        oldResuList = GetCompleteTestList(arglist.uuidold, LocDir,force=arglist.force)

        DiffUUIDSep(newResuList,oldResuList)
        # start compare 
        #DiffTests(fd_uuidnew,fd_uuidold)
    elif arglist.get:
        vlcpFd=GetProd(uuid)
        #GetCompleteTestList(uuid, LocDir,"failed", force=arglist.force)
        if arglist.get == 'cmd':
        # force to get "dict" from url, rather than read from csv(it will turn all data into "str")
           GenerateCmd(uuid, GetCompleteTestList(uuid, LocDir,force=True), vlcpFd)
        elif arglist.get == 'cl':
           element = arglist.element
           clrange = arglist.clrange
        # get cl delta: input old-cl/new-cl AND a uuid for the prod (uuid just to maap vlcp)
           GenerateCL(vlcpFd, element, clrange)
           pass 
    # run vul cmd: cmdtemp / cllists / tags ... 
    elif arglist.trg:
    # usage : 
    # autotriage -u 9c3a6a0c-2fd5-4c89-981b-a354f9485722 -trg -cl 24068678,2406867 -cmd "vulcan --keep-going -v --eris --user jiag --product=//sw/gpgpu/MachineLearning/cudnn_v7.1/eris/cudnn_r92_r396.vlcp --build cudnn_doc --target-os=Linux --target-arch=aarch64 --tag={tags} --target-revision=cl-{cl}" -t 0524Test
        cmdline = arglist.cmdline
        cllist = arglist.cllist
        tags = arglist.tags
        #vlcpFd=GetProd(uuid)
        #cmdline = cmdtemp.format_map(vars())
        # TODO: embed vlcp (from uuid) to cmdline?
        # force to get "dict" from url, rather than read from csv(it will turn all data into "str")
        GenTriageUUID(LocDir, cmdline, cllist, tags)
            
