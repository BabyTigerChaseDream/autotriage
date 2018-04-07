#!/usr/bin/python3
from operator import itemgetter 
from itertools import groupby
import re

def TestFilter(logfile, keyword):
    print(' Start parsing log ...\n\t %s \n'% logfile)
    # TODO : wordaround bug in autotriage download_list
    if not logfile.endswith('log'):
        print("[Err] Wrong format log !!!")
        return 
    resuList = []
    with open(logfile,'r') as f:
    # 2018/04/07 : working version
        #for result in re.finditer(r"(?P<errname>@@@@ (?:First error msg).*$)(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
        # Step-2 capture "NOT RUN already but cannot capture group name when sorting"
        #for result in re.finditer(r"(?P<errname>@@@@ First error msg.*$)|Error Detected:(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
        for result in re.finditer(r"(?P<errname>@@@@ First error msg.*$|Error Detected:)(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
            #print(result.groupdict())
            resuList.append(result.groupdict())
    # before groupby(the key "errname") , need to sort list first
    resuList.sort(key=itemgetter('errname'))

    for err, testItem in groupby(resuList,key=itemgetter('errname')):
        if keyword:
            # check if any keyword match testid (PASS/FAILED/WAIVED) 
            if any(filter(lambda t: keyword in t['testid'], testItem)):
                print('===== [matched] =====   ',err)
                for t in testItem:
                    print(t['testid'])
        else:
            print('=============    ',err)
            for t in testItem:
                print(t['testid'])
           
if __name__=="__main__":
    import sys
    if(len(sys.argv) < 2):
        print("PROG /ws/abspath/src.log <keyword>")
        print("<keyword> is optional , can be chosen from \"PASS/FAIL/WAIVED\" ")
    else:
        filename = sys.argv[1]
        keyword = sys.argv[2] if len(sys.argv)>2 else None
        TestFilter(filename, keyword)
"""
"^(\d\d\d)(\d\d\d)(?:\.(\d\d)){0,1}$"

(r"(?P<errname>@@@@ (?:First error msg).*$){0,1}(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE)
"""
