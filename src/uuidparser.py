#!/usr/bin/python3

"""
parse info from uuid 

1) Test results 
- overall test results (gpu/os/suite)
- test configID
- TODO :history 

2) build results

"""

# system mod 
import sys
# web mod 
import ssl
from urllib.request import urlopen
# orderring mod
from operator import itemgetter 
from itertools import groupby
# other mod 
import re

global resuList = list()

global cudnn_vlcp_dict 

cudnn_vlcp_dict = {
                  "CUDNN DEV GPGPU CUDA_A"       : "//sw/gpgpu/MachineLearning/cudnn/eris/cudnn_gpgpu_cuda_a.vlcp",
                  "CUDNN DEV CUDA 9.2 r396"      : "//sw/gpgpu/MachineLearning/cudnn/eris/cudnn_r92_r396.vlcp"
        }

########### func ############

def GetUrlString(url):
    if sys.version_info >= (2,7,9):
        ssl._create_default_https_context = ssl._create_unverified_context
    # urlopen().read() returns 'b' needs decode('utf-8') --> string
    urlstring= urlopen(url).read().decode('utf-8')
    return urlstring

"""
    ####################################################
        Generate complete Tests result of each uuid  
        /***     contains all info we need     ***/
    ####################################################
"""

### return CUDA_A/CUDA9.2 
def GetProd(uuid):
    url = 'https://eris-portal.nvidia.com/GetProductServlet?uuid=%s'%uuid
    headersource = GetUrlString(url)
    config=json.loads(headersource)
    product = config["product"]

    return cudnn_vlcp_dict[product]

def GetBuildTable(uuid):
    # sample link:
    # https://eris-portal.nvidia.com/OneSubmissionBuildsServlet?uuid=8b19bd82-4683-4d0b-995a-41748c206bb8&tableselector=dataTableOneSubmissionTestSuites
    url = "https://eris-portal.nvidia.com/OneSubmissionBuildsServlet?uuid=%s&tableselector=dataTableOneSubmissionTestSuites"%uuid
    urlstring = GetUrlString(url)

    for ent in re.finditer(r'&componentNameText=cudnn(?P<component>\w+)&erisConfigID=(?P<cid>\d+)(?:.+?)(?:(?:&hostName=(?P<hw>eris-\w+-\w+)&phase=(?P<log>\w+))|(?:Log file was not created))',urlstring):
        resuList.append(ent.groupdict())
    
    return resuList


def GetTestTable(uuid):
    url = "https://eris-portal.nvidia.com/OneSubmissionTestSuitesServlet?uuid=%s&tableselector=dataTableOneSubmissionBuilds&url"%uuid
    urlstring = GetUrlString(url)

    # find test bed/log 
    # match patterns : greedy (.*) , matches only one group -- last one :
    # >>> re.findall(r'badge-(\w+)\'>([\w\d\s]+)<(?:.*)testSuiteNameText=(\w+)&erisConfigID=(\w+)(?:.*)&hostName=(eris-(?:[\w\d]+)-(?:[\w\d]+))&phase=([\w\d_]+)',urlstring)
    # [('passed', '2208', 'cudnn_layer_tests', '11990698', 'eris-ub16-vt000', '_test__dbf53848ec')] 
    # re.findall(r"badge-(\w+)\'>(.+?)<\\/span>.+?historyChannelLabel.+?testSuiteNameText=(.+?)&.+?ConfigID=(\w+)(?:.+?)&hostName=(eris-(?:[\w\d]+)-(?:[\w\d]+))&phase=([\w\d_]+)(?:.+?)\'>",urlstring)

    # re.findall returns Lists fill with tuple element :
    # match ALL patterns : no greedy (.+?):all shortest match groups
    # (result, fail/pass num or fail detail, testsuite, configID, testbed, logID)
    # ('passed', '2045', 'cudnn_layer_tests', '51662', 'eris-ub14-vt004', '_test__51ee6e354f') .... ()() 
    #resuList = re.findall(r"badge-(\w+)\'>(.+?)<\\/span>.+?historyChannelLabel.+?testSuiteNameText=(.+?)&.+?ConfigID=(\w+)(?:.+?)&hostName=(eris-(?:[\w\d]+)-(?:[\w\d]+))&phase=([\w\d_]+)(?:.+?)\'>",urlstring) 
    
    # match both test w/wo log generated :
    # match A OR B 
    # ('notrun', 'Subm Timeout', 'cudnn_samples_mnist_tests', '9681', '', '')
    # ('passed', '6', 'cudnn_samples_mnist_tests', '51662', 'eris-ub14-vt005', '_test__96c266482b')
    for ent in re.finditer(r'badge-(?P<resu>\w+)\'>(?P<info>[\w\d\s]+)<(?:.+?)&testSuiteNameText=(?P<tsuite>\w+)&erisConfigID=(?P<cid>\d+)(?:.+?)(?:(?:&hostName=(?P<hw>eris-\w+-\w+)&phase=(?P<log>\w+))|(?:Log file was not created))',urlstring):
        resuList.append(ent.groupdict())
    
    return resuList

"""
    ####################################################
        Get: os/arch/gpu info from configID(number) 
    ####################################################
"""

def MapConfigID2Str(ConfigSet):
    global configMap
    configMap = {c:GetConfig(c) for c in ConfigSet}
    return configMap

def GetConfig(cfgID):
    url = "https://eris-portal.nvidia.com/GetTestHeaderServlet?testSuiteNameText=&testNameText=&erisConfigID=%s"%cfgID
    urlstring= GetUrlString(url)
    config = re.findall(r"<td>(.*?)<\\/td>",urlstring)
    # config info below :
    # ['', 'gp102', 'p40', 'x86_64', 'Ubuntu14_04', '[Default]', 'release', '[Default]']
    # needs GPU,arch.os only --> item [2:5] in list
    # tuple is mutable -> for config
    return tuple(config[2:5])

def ConfigIDSet(ResuList):
    ConfigSet = set()
    for r in ResuList:
        # collect configID without repeat
        ConfigSet.add(r['cid'])
    return ConfigSet

def ConfigStrUpdate(ResuList, configMap):
    for r in ResuList:
        r['cid']= configMap[r['cid']]
    return ResuList
"""
    #########################################################
     Get failed/notrun/abort items from overall Results List
    #########################################################
"""
def FilterResuList(ResuListAll, keyword=None):    
    """
    keyword can be : failed/nortun/abort/passed(normally ignored)
    yield IS return , just returns an "iterator"
    """
    ### <2> use filter enough
    if not keyword:
        return ResuListAll
    else:
        print(" ... Searching [\"%s\"] "%keyword)
        return list(filter(lambda r:keyword in r['resu'], ResuListAll))

    ### <1> use groupby (overkill)
    #ResuListAll.sort(key=itemgetter('resu'))
    #for resu, ent in groupby(ResuListAll,key=itemgetter('resu')):
    #    if resu == keyword:
    #        yield ent
    #    elif keyword == None:
    #        yield ent

def display(ResuList):
    ResuList.sort(key=itemgetter('resu'))
    for resu, ent in groupby(ResuList,key=itemgetter('resu')):
        print('\n =============== Result [%s] ===============',resu)
        for e in ent:
            # TODO:remove item from dict elegant
            print(e)
            #print(e.values())


"""
Delta between nightly
"""
# dictA &| dictB (dict is ResuListAll ...)

