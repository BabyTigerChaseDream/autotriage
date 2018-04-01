import optparse
import subprocess
import json
import re
import sys
import os
import urllib2
import cookielib
import datetime

def get_source(uuid, testsuite):
    eris_url = "https://eris-portal.nvidia.com/OneSubmissionTestSuitesServlet?uuid=%s&tableselector=dataTableOneSubmissionBuilds&url"%uuid
    print eris_url
    try:
        url_open = urllib2.urlopen(eris_url)
    except urllib2.HTTPError,e:
        print e.code
        print e.reason
        print e.geturl()
        print e.read()

    eris_results = url_open.read()

    f2 = open("bb.txt", 'w')
    f2.write(eris_results)
    f2.close()


    f1 = open("bb.txt", 'r')
    eris_results = f1.read()
    f1.close()


    AllRunConfigs= re.findall(r"<td> <TABLE.*?testSuiteNameText=.*?<\\/TABLE><\\/td>",eris_results)

    print "len of AllRunConfigs is %d" % len(AllRunConfigs)

    Configs = []
    Configs_1 = []

    for rc in AllRunConfigs:
        s1 = re.search("testSuiteNameText=(%s)&.*?ConfigID=(.*?)\'>" % testsuite, rc)
        if (s1):
            flag = True
            #print "testsuite = %s, configID = %s" % (s1.group(1), s1.group(2))
            status = "Unknown"
            testsuite = s1.group(1)
            configID = s1.group(2)
            s11 = re.search("badge-failed\'>(.*?)<\\\\/span>", rc)
            if s11:
                failcount = s11.group(1)
                if failcount == "Failed Other":
                    status = "Failed Other"
                    flag = False

            if flag:
                s12 = re.search("badge-aborted", rc)
                if s12:
                    status = "Aborted"
                    flag = False

            if flag:
                s13 = re.search("badge-notrun\'>(.*?)<\\\\/span>", rc)
                if s13:
                    notruncount = s13.group(1)
                    if notruncount == "Not Run":
                        status = "Not_Run"
                        flag = False
                    else:
                        if notruncount == "Submission Timeout":
                            status = "Submission_Timeout"
                            flag = False
            if flag == False:
                Configs_1.append(tuple((testsuite, "no_log", status, configID)))
                continue
            s2 = re.search("\'Show test suite logfile\'.*?component_name=%s&.*?&hostName=(.*?)&phase=(.*?)\\\\\">" % testsuite, rc)
            if (s2):
                #print "hostname = %s, phase = %s" % (s2.group(1), s2.group(2))
                status = "RunWithLog"
                hostname = s2.group(1)
                phase = s2.group(2)
                logname=hostname+'_'+phase+".zip"
            else:
                status = "RunWithoutLog"
                logname="no_log"

            Configs_1.append(tuple((testsuite, logname, status, configID)))
    #print Configs_1
    #print len(Configs_1)

    configID_list = list()
    for i in Configs_1:
        if i[3] not in configID_list:
            configID_list.append(i[3])

    configID_dict = dict()
    for i in configID_list:
        configID_dict[i]=ConfigID(i)

    for i in Configs_1:
        flag1 = True
        if flag1 == True:
            config = list()
            lists = list(i)
            lists.extend(configID_dict[i[3]])
            if lists[11] == "[Default]":
                lists[11] = ''
            config = [lists[0],lists[2], lists[1], '', lists[6],lists[7],lists[8], '', lists[10],lists[11]]
            Configs.append(config)

##name = [ 'components', 'status', 'logname', 'gpu_model', 'gpu', 'arch', 'os', 'abi','build', 'compiler']
    print "len of Configs is %d" % len(Configs)

    return Configs

def ConfigID(cid):
    url = "https://eris-portal.nvidia.com/GetTestHeaderServlet?testSuiteNameText=&testNameText=&erisConfigID=%s"%cid
    url_open = urllib2.urlopen(url)
    url_source = url_open.read()
    res_td = r"<td>(.*?)<\\/td>"
    config = re.findall(res_td,url_source)
    return config

def generate_filename(cfg_list):
    logname_list = list()
    filename_list = list()
    i = -1
    for cc in cfg_list:
        i = i + 1
        cfg = ""
        log = cc[2]
        if cc[1] != "RunWithLog":
            continue
        if log[len(log)-4:] != ".zip":
            print "not end with .zip"
            continue
        if log == "pending_placeholder__db_init.zip":
            continue

        for j in range(3, len(cfg_list[i])):
            cfg += "__%s" % cfg_list[i][j]
        name = log[0:len(log)-4] + cfg + ".log"##assume ends with .zip
        name2 = "%s\\%s" % (output_dir, name)
        if not os.path.isfile(name2):
            logname_list.append(log)
            filename_list.append(name)
        else:
            print "%s exists" % name2
            stats_dict["Download"] += 1

    return logname_list, filename_list


def download_unzip_log(logname_list, filename_list, uuid):
    url1 = "http://eris-fs000/logs/%s" % uuid

    for log2 in logname_list:
        url2 = "%s/%s" % (url1, log2)
        wget_cmd = "wget %s -O %s\\%s" % (url2, output_dir, log2)
        ret1 = run_cmd(wget_cmd)

        if (ret1 == 0):
            unzip_cmd = "7z e -y -o%s %s\\%s" % (output_dir, output_dir, log2)
            ret2 = run_cmd(unzip_cmd)
            #print "!!!ret2 = %s" % ret2
            if (ret2 == 0):
                stats_dict["New"] += 1 ###to-do, if os.exists()
            else:
                stats_dict["Other"] += 1
        else:
            stats_dict["Other"] += 1
    rm_cmd = "del %s\\*.zip" % output_dir
    run_cmd(rm_cmd)

    i = 0
    for log2 in logname_list:
        log = log2.replace(".zip", ".log")
        cmd = "rename %s\\%s %s" % (output_dir, log, filename_list[i])
        run_cmd(cmd)
        i = i + 1


def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        print line
    retval = p.wait()
    return retval

def main():
    parser = optparse.OptionParser()
    parser.add_option('-u','--uuid',dest='uuid',action='store',type='string',default=False,help='specify the uuid of submission')
    parser.add_option('-b','--branch',dest='branch',action='store',type='string',default=False,help='specify branch of submission, e.g., cuda_8_0_r378, cuda_a')
    parser.add_option('-l','--label',dest='label',action='store',type='string',default=False,help='specify label of submission, e.g., nightly')
    parser.add_option('-d','--date',dest='date',action='store',type='string',default=False,help='specify date of submission, e.g., 20170117')
    parser.add_option('-t','--testsuite',dest='testsuite',action='store',type='string',default=False,help='specify the name of testsuite, e.g., samples_tests')
    options,args = parser.parse_args()
    if options.uuid:
        uuid = options.uuid
    else:
        print 'ERROR: This script need option "--uuid" or "-u".'
        sys.exit(1)
    if options.branch:
        branch = options.branch
    else:
        print 'ERROR: This script need option "--branch" or "-b".'
        sys.exit(1)
    if options.label:
        label = options.label
    else:
        print 'ERROR: This script need option "--label" or "-l".'
        sys.exit(1)
    if options.date:
        date = options.date
    else:
        print 'ERROR: This script need option "--date" or "-d".'
        sys.exit(1)
    if options.testsuite:
        testsuite = options.testsuite
    else:
        print 'ERROR: This script need option "--testsuite" or "-t".'
        sys.exit(1)
    #===================customize begin=======================================================
    #uuid = "6f399333-66e2-4035-80d0-e05debbc1da4"
    #submission = "cuda_8_0_r378__nightly__20170117"
    #submission = "cuda_a__nightly__20170115"
    #testsuite = "samples_tests"
    submission = "%s__%s__%s" % (branch, label, date)
    output_dir0 = "C:\\Work\\auto-triage\\raw_data\\"

    #===================customize end=======================================================
    global output_dir
    global stats_dict

    output_dir = "%s%s__%s" % (output_dir0, testsuite, submission)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_list = list()
    cfg_list = list()
    log_name_list = list()
    file_name_list = list()

    result_list = ["Download", "New", "Other"]
    stats_dict = dict()
    for ss in result_list:
        stats_dict[ss] = 0

    cfg_list = get_source(uuid, testsuite)
    log_name_list, file_name_list = generate_filename(cfg_list)

    download_unzip_log(log_name_list, file_name_list, uuid)

    #print "len of log_list in protal is %d" % len(log_list)
    #print "len of log_name_list in local PC is %d" % len(log_name_list)
    print stats_dict

    stat_file_name = "%s\\00_download_history.csv" % output_dir0
    if not os.path.isfile(stat_file_name):
        f1 = open(stat_file_name, 'w')
        t = "uuid,testsuite,submission,"
        for ss in result_list:
            t += "%s," % ss
        t += "date"
        f1.write("%s\n" % t)
        f1.close()

    stats_dict["Download"] += stats_dict["New"]
    f1 = open(stat_file_name, 'a')
    t = "%s,%s,%s," % (uuid, testsuite, submission)
    for ss in result_list:
        t += "%s," % stats_dict[ss]
    str2 = "%s %s" % (datetime.date.today(), datetime.datetime.now().time())
    t += str2
    f1.write("%s\n" % t)
    f1.close()

if __name__ == '__main__':
    main()