#!/usr/bin/python3

from itertools import groupby 
from operator import itemgetter

global cmdTemp 
# TODO: different template for different product 

cmdTemp = "vulcan -v --user jiag --eris --trace 3 --product={vlcp} --target-arch {arch} --target-os {os} --testsuite {suite} --target-gpu {gpu} --target-revision=cl-{tot} --tag {tag}"

# TODO : add optional param like : apply-change 
def GenerateCmd(ResuList, vlcp, cmdTemp=cmdTemp, keyword=None, optional=None):
    CmdList = []
    tot='tot'
    grouper = itemgetter('resu','info')
    ResuList.sort(key=grouper)
    # for loop below shows all cmd unit
    #for t in ResuList:
    for keys, testItem in groupby(ResuList,key=grouper):
        print('===== Catalog ===== \n\t',keys)
        for t in testItem:
            tag = '#'.join((t['suite'], *t['cid'])) #, t['hw']))
            suite = t['suite']
            gpu,arch,os = t['cid']
            #print(type(t['cid']))
            #CmdList.append(cmdTemp.format_map(vars()))
            print(cmdTemp.format_map(vars()))
    
    # Advance: suite/gpu ,select any tests param combo  
    # Group Same config / multi suite 
    # cmd is very flexible - THINK... 
    # re-run due to error types 


