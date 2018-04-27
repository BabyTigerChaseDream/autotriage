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
        for i in sorted(oldfail):
            print(i.strip())

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:    
        # legacy fail
        newfail = set(newfd)-set(oldfd)    
        print('\n####################\n[##### New #####]')
        for i in sorted(newfail):
            print(i.strip())

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:
        # failure in old but pass in new 
        fixedfail = set(oldfd)-set(newfd)    
        print('\n####################\n[##### FIXED #####]')
        for i in sorted(fixedfail):
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
        print('===== [TID Groups] =====   \n\t',key)
        
        ResuGroup = []
        count  = 0
        for t in testItem:
            ResuGroup.append(t) 
            count = count + 1
        print("Contain: %d member"%count) 
        
        if count == 1:
            # nothing to compare 
            tsuite = ResuGroup[0]
            print("[Single suite]\n\t",tsuite.values())
            print('====================',key)
        elif count == 2:
            # both suites "failed" AND both have log, makes sense to DIFF 
            t1,t2 = ResuGroup
            if (t1['resu'] == 'failed' and t2['resu'] == 'failed')\
                and t1['log'] \
                and t2['log']:
                    print("[Diff suite]\n")
                    print("\t",t1.values())
                    print("\t",t2.values())
                    print('====================',key)  

                    log1 = LocateFd(locTrgdir,t1['log']+'.log')
                    log2 = LocateFd(locTrgdir,t2['log']+'.log')

                    if log1 is None or log2 is None:
                    # it is for "failed" on "BADDRIVER" which display 'log' but no log generated 
                        print("[Failed to locate log in suite] Double check \n")
                        print("\t",t1.values())
                        print("\t",t2.values()) 
                    else:
                        flog1 = TestFilter(log1,keyword="FAILED",logfail=True, diffuuid=True)
                        flog2 = TestFilter(log2,keyword="FAILED",logfail=True, diffuuid=True)
                        print('CMP...ing :',flog1,flog2)
                        DiffTests(flog1,flog2)

            elif t1['resu'] == 'passed' or t2['resu'] == 'passed':
                    print("[PASS in suite] Compare by testparser \n")
                    print("\t",t1.values())
                    print("\t",t2.values())                
            elif not t1['log'] or not t2['log']:
                # one log is empty
                    print("[EMPTY log in suite] Re-Run \n")
                    print("\t",t1.values())
                    print("\t",t2.values()) 
        else:
            print('***** [WARNING] count is %d' % count)
            for r in ResuGroup:
                print(r)

                
if __name__=="__main__":
    import sys
    if(len(sys.argv) < 2):
        print("PROG /ws/abspath/src.log /ws/abspath/src.fail")
        print("compare different uuid's test suite")
    else:
        newfd = sys.argv[1]
        oldfd = sys.argv[2] 
        DiffTests(newfd, oldfd)        
