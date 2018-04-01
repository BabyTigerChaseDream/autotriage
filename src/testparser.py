#!/usr/bin/python3
from operator import itemgetter 
from itertools import groupby
import re

def TestFilter(logfile, keyword):
    resuList = []
    with open(logfile,'r') as f:
        for result in re.finditer(r"(?P<errname>@@@@ (?:First error msg).*$)(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
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
