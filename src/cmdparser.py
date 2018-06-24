#!/usr/bin/python3

from itertools import groupby 
from operator import itemgetter

## Find rev - multiproc
from multiprocessing import *
import subprocess as sub
import os 

import re

# TODO: different template for different product 


# TODO : add optional param like : apply-change 
def GenerateCmd(uuid,ResuList, vlcp, cmdtemp=None, keyword=None, optional=None):
    cmdtemp = "vulcan -v --user jiag --eris --trace 3 --product={vlcp} --target-arch {arch} --target-os {os} --testsuite {suite} --target-gpu {gpu} --target-revision=cl-{tot} --tag {tag}"
    CmdList = []
    tot='tot'
    grouper = itemgetter('resu','info')
    ResuList.sort(key=grouper)
    # for loop below shows all cmd unit
    #for t in ResuList:
    for keys, testItem in groupby(ResuList,key=grouper):
        print('===== Catalog ===== \n\t',keys)
        for t in testItem:
            tag = '#'.join((uuid, t['suite'], *t['cid'],keys[-1].strip())) #, t['hw']))
            suite = t['suite']
            gpu,arch,os = t['cid']
            #print(type(t['cid']))
            #CmdList.append(cmdtemp.format_map(vars()))
            print(cmdtemp.format_map(vars()))
    
    # Advance: suite/gpu ,select any tests param combo  
    # Group Same config / multi suite 
    # cmd is very flexible - THINK... 
    # re-run due to error types 

###################################
###         Find-revision       ###
###################################

def FindCLMTFunc(arglists):
    vlcpFd, eleunit, CLRange = arglists
    cmdtemp = "vulcan --find-revisions --product={vlcpFd} --revision-range {CLRange} {eleunit}"

    DResu = {'ele':eleunit,'CLRange':[]}
    
    print('=====> Find {eleunit},CL:{CLRange},product {vlcpFd}'.format_map(vars()))
    #print('cmdline: ',cmdtemp.format_map(vars()))
    proc=sub.Popen(cmdtemp.format_map(vars()), bufsize=1, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    stdout,stderr = proc.communicate()
    
    # parse stdout/stderr
    strout=stdout.decode("utf-8").split('\n')
    strerr=stderr.decode("utf-8")

    # check if command error 
    if strerr:
    # TODO customize exception ? 
        raise ValueError("Error",strerr)

    for s in strout:
        if s.isdigit():
            DResu['CLRange'].append(s)

    # check if list empty 
    if not DResu['CLRange']:
        DResu['CLRange'] = "Empty"

    # TODO : learn:
    # if returns values only error msg :
    # multiprocessing.pool.MaybeEncodingError: Error sending result: '[dict_values(['cudnn', ['24056110', '24061509']])]'. Reason: 'TypeError("can't pickle dict_values objects",)'
    # return(DResu.values()) # error on "pickle" ???
    return(DResu)

# eleList : type(List) / CLRange : type(string) - split by ,
def GenerateCL(vlcpFd, eleList, CLRange):
    # check CLRange:
    minCL,maxCL = CLRange.split(',')
    if int(minCL) > int(maxCL):
        raise ValueError(" Doesn't match: minCL{minCL} < maxCL{maxCL} !!!".format_map(vars()))
    
    arglists = [(vlcpFd, e, CLRange) for e in eleList]

    p = Pool(cpu_count())
    results = p.map_async(FindCLMTFunc, arglists)
    
    outputs = results.get()
    for r in outputs:
    # TODO handle different types of return value 
        print(r)
        
#############################
#   vulcmd sub-process      #
#############################

def vulmtFunc(vulargs):
    # cl: change-list / tags: notes of submit 
    cl, cmdtemp, tags = vulargs
    DResu = {'tags':tags,'resu':'pass','uuidLink':None}

    print('=====> Start running cl-{cl}'.format_map(vars()))
    print('cmdline: ',cmdtemp.format_map(vars()))
    proc=sub.Popen(cmdtemp.format_map(vars()), bufsize=1, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    stdout,stderr = proc.communicate()

# parse stdout/stderr
    strout=stdout.decode("utf-8")
    strerr=stderr.decode("utf-8")
    #queue , 
    #Qbar.put(tags)

    # Filter error 
    # b'[ERROR cuda.py:_get_eris_arch_targets:1851] unknown target architecture "ppc"\n    
    if 'ERROR' in strerr:
        DResu['resu'] = 'failed :' + strerr
        # if failed , no uuidLink at all... use "None" in default DResu
    else:
    #  TODO: can be an attri of vulcmd class 
        start='ACCEPTED... Go to '
        end=' to check its status.'
    
        DResu['uuidLink']=re.search('%s(.*)%s' % (start, end), strout).group(1)

    # if returns values only error msg :
    # multiprocessing.pool.MaybeEncodingError: Error sending result: '[dict_values(['cudnn', ['24056110', '24061509']])]'. Reason: 'TypeError("can't pickle dict_values objects",)'
    # return(DResu.values()) # error on "pickle" ???
    return (DResu)

# LocDir is absolute path for one uuid 
def GenTriageUUID(LocDir, cmdline, CLList, tags):
    ### vulmtFunc paramter
    #CLList = ['24068678','24068670','24068575','24068452','24068331','24068142','24068074','24068074','tot']
    #CLList = ['hello','multi']
    #cmdline="vulcan --keep-going -v --eris --user *** --product=//sw/gpgpu/MachineLearning/cudnn_v7.1/eris/cudnn_r92_r396.vlcp --build cudnn_doc --target-os=Linux --target-arch=aarch64 --tag={tags} --target-revision=cl-{cl}"
    #tags = 'MT'
   
    CLList = CLList.split(',')
    # use " as a special char , incase of mix other cmdline param with it
    cmdline = re.sub('\"','',cmdline)
    tags = tags

    ##### multi-process param #####
    p = Pool(cpu_count()) 

    arglists = [ (cl,cmdline,tags) for cl in CLList ]

    ### block mode 
    #result = p.map(vulmtFunc,lists)
    
    # none block mode 
    # TODO: one cmdline for all CLs ran in triage.log(key.group dict ?) 
    result = p.map_async(vulmtFunc,arglists)
    	
    ### collect ALL process result in a Queue ? and summarize  
    # monitor loop
    #while True:
    #    if result.ready():
    #        break
    #    else:
    #        size = q.qsize()
    #        print(size)
    #        time.sleep(3)
    
    outputs = result.get()
    
    for o in outputs:
        try:
            with open(os.path.join(LocDir,'triage.log'),'a+') as fd:
                print("Opening : LocDir ", LocDir)
                print(o,file=fd)
            os.system('cat '+os.path.join(LocDir,'triage.log')) 
        except AttributeError:
            print("Error at : ",os.path.join(LocDir,'triage.log'))
            
            
