#!/usr/bin/python3

"""
autotriage provide cmdline for triage nightly failures

- "show command" (show test results option arg: -d for detail):
    -t all/failed/passed/.../(aborted|notrun)  --> regex supported
    -b all/failed/depend failed ...
- "diff command" (diff test set )
    -uuid "uuid1" "uuid2" (diff 2 uuid's results: dict &|)
    -testcid "testsuite_cid1" "testsuite_cid2" (diff 2 testsuite's result)
- "get command " (generate and display command)   
- "subm command" (exec command to run)
     [] required  <> optional 
    -testcid [tags] <cl-num> <hw> <apply-change>  (default => cl-num:tot / hw:chosen by Eris )
"""


"""
standard Python module
"""
import argparser 

"""
Private module for triage 
"""
from fdfetcher import *
from testparser import *
from uuidparser import *

