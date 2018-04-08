#!/usr/bin/python3

import os 

# nfd contains NEW result
# ofd contains OLD result
# sum is for create a file to store summery
def DiffTests(nfd,ofd,sum=None):
    #check file exist or not 
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
            print(i)

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:    
        # legacy fail
        newfail = set(newfd)-set(oldfd)    
        print('\n####################\n[##### New #####]')
        for i in newfail:
            print(i)

    with open(nfd, 'r') as newfd, open(ofd, 'r') as oldfd:
        # failure in old but pass in new 
        fixedfail = set(oldfd)-set(newfd)    
        print('\n####################\n[##### FIXED #####]')
        for i in fixedfail:
            print(i)

if __name__=="__main__":
    import sys
    if(len(sys.argv) < 2):
        print("PROG /ws/abspath/src.log /ws/abspath/src.fail")
        print("compare different uuid's test suite")
    else:
        newfd = sys.argv[1]
        oldfd = sys.argv[2] 
        DiffTests(newfd, oldfd)        
