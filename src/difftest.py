#!/usr/bin/python3

import sys, os 
import subprocess as sub 

from itertools import groupby 
from operator import itemgetter

from testparser import *
from fdfetcher import *

# nfd contains NEW result
# ofd contains OLD result
# sum is for create a file to store summery
def DiffTests(nfd,ofd,sum=None):
    #check file exist or not 
    print('=== > Diff ...ING')
    if os.path.isfile(nfd) and os.path.isfile(ofd):
        pass
    else:
        raise ValueError("Make sure %s,%s exist !",nfd,ofd)

    # TODO: [ISSUE] newfd/oldfd can only be handled once, 
    #with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:
    #        # legacy fail
    #        oldfail = set(newfd).intersection(oldfd)    
    #        ### here , iterator oldfd/newfd consumed up .... so below data set all empty 
    #        # legacy fail
    #        newfail = set(newfd)-set(oldfd)    
    #        # failure in old but pass in new 
    #        fixedfail = set(oldfd)-set(newfd)   

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:
        oldfail = set(newfd).intersection(oldfd)
        print('\n####################\n[##### OLD #####]')
        for i in oldfail:
            print(i.strip())

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:    
        # legacy fail
        newfail = set(newfd)-set(oldfd)    
        print('\n####################\n[##### New #####]')
        for i in newfail:
            print(i.strip())

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:
        # failure in old but pass in new 
        fixedfail = set(oldfd)-set(newfd)    
        print('\n####################\n[##### FIXED #####]')
        for i in fixedfail:
            print(i.strip())

def LocateFd(path,filepat):
    print('Looking for : %s'% filepat)
    for (ThisLeveldirs, sub_dirs, files) in os.walk(path):
        for fd in files:
            if filepat in fd:
                # ThisLeveldirs is where fd located
                return os.path.join(ThisLeveldirs,fd)
            #print("no files at this level")
    return None

# UUID lists group by keys
# arbitrary lists TODO 
# arbitrary keys to compare 
def GroupUUID(ResuListx2,key1='suite',key2='cid'):
    grouper = itemgetter(key1, key2)
    ResuListx2.sort(key=grouper)
    for key, testItem in groupby(ResuListx2,key=grouper):
        print('===== [TID Groups] =====   ',key)
        #if(len(list(testItem)) == 2):
        # TODO: testItem can only be iterate once , ??? 
        #print('[DBG]===> len of testItem: %d',len(list(testItem)))
        fds= []
        for t in testItem:
            #if "failed" not in t['resu']:
            #    continue
            print(t.values())
            fd_log = LocateFd(locTrgdir,t['log']+'.log') if t['log'] else None
            #print('fd_log :',fd_log)
            if fd_log is not None:
                fds.append(TestFilter(fd_log,keyword="FAILED",logfail=True))
    
        #print('==> Fds:',*fds)
        if (len(fds)== 2) :
            print('==> Compare Fds:',*fds)
        ##DiffTests(*fds)
            DiffTests(fds[0],fds[1])
        else:
            pass
                
if __name__=="__main__":
    import sys
    if(len(sys.argv) < 2):
        print("PROG /ws/abspath/src.log /ws/abspath/src.fail")
        print("compare different uuid's test suite")
    else:
        newfd = sys.argv[1]
        oldfd = sys.argv[2] 
        DiffTests(newfd, oldfd)        
