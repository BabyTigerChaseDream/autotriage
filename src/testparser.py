#!/usr/bin/python3

from operator import itemgetter 
from itertools import groupby
import re

# file/path lib
from pathlib import Path

def TestFilter(logfile, keyword, logfail=False, detail=True):
    print(' Start parsing log ...\n\t %s \n'% logfile)
    # TODO : wordaround bug in autotriage download_list
    if not logfile.endswith('log'):
        print("[Err] Wrong format log !!!")
        return 
    # TODO : make logfail passed from user input 
    # TIPs: change file suffix with python lib : "from pathlib import Path"
    if logfail:
    # TODO: elegant create new file 
        p = Path(logfile)
        log4fail =p.with_suffix('.fail').name
        with open(log4fail,'wt'):
            pass
        print('===== Log failure at:',log4fail)

    resuList = []
    # "with..open" file with little known mode "wt"(py3 only)
    with open(logfile,'r') as f:
    # 2018/04/07 : working version
        #for result in re.finditer(r"(?P<errname>@@@@ (?:First error msg).*$)(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
        # Step-2 capture "NOT RUN already but cannot capture group name when sorting"
        #for result in re.finditer(r"(?P<errname>@@@@ First error msg.*$)|Error Detected:(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
        for result in re.finditer(r"(?P<errname>@@@@ First error msg.*$|Error Detected:)(?:(?:\n|.)*?)(?P<testid>(?:&&&&) (?:PASSED|FAILED|WAIVED) cudnnTest.*$)",f.read(),re.MULTILINE):
            resuList.append(result.groupdict())
    # before groupby(the key "errname") , need to sort list first
    resuList.sort(key=itemgetter('errname'))

    for err, testItem in groupby(resuList,key=itemgetter('errname')):
        if keyword:
            # check if any keyword match testid (PASS/FAILED/WAIVED) 
            if any(filter(lambda t: keyword in t['testid'], testItem)):
                print('===== [matched] =====   ',err)
                [print(t['testid']) for t in testItem if detail]
                if logfail:
                    with open(log4fail,'a') as fdfail:
                        [print(t['errname'],t['testid'],file=fdfail) for t in testItem]
        else:
            print('=============    ',err)
            [print(t['testid']) for t in testItem if detail]
            if logfail:
                with open(log4fail,'a') as fdfail:
                    [print(t['errname'],t['testid'],file=fdfail) for t in testItem]
           
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
