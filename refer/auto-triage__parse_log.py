import optparse
import subprocess
import sys
import string
import re
import os

from os import listdir
from os.path import isfile, join

from datetime import datetime


def print_to_csv(l_a, t_a, l_b, flag, fn):
    ###output to fail.csv
    t = ""
    if (len(l_a) == 0):
        return
    len1 = len(l_a[0])
    len2 = len(t_a)
    len3 = 0

    if (len(l_a) != len(l_b)):
        flag2 = False
    else:
        flag2 = True
        len3 = len(l_b[0])


    for i in range(0, len(l_a)):
        if (flag == True):###merge the last two columns
            i1 = len1 - 2
        else:
            i1 = len1
        for j in range(0, i1):
            t += "%s," % l_a[i][j]
        if (flag == False):
            continue
        if (l_a[i][len1 - 1] > 1):
            t += "%s[%d]," % (l_a[i][len1 - 2], l_a[i][len1 - 1])
        else:
            t += "%s," % (l_a[i][len1 - 2])
        for k in range(0, len2):
            t += "%s," % t_a[k]
        if (flag2):
            for j in range(0, len3):
                t += "%s," % l_b[i][j]
        fn.write("%s\n" % t)
        t = ""


def parse_one_file(fn):
    f = open(fn, 'r')

    print fn

    g0 = 0 ### 1 indicates occurrence of testsuite begin words
    g1 = 0 ### 1 indicates after &&&& RUNNING
    g2 = 1 ### 1 indicates no occurrence of exclude words
    g11 = 0 ### 1 indicates occurrence of timeout words
    g11a = 0 ### 1 indicates time in a timeout test is found
    g12 = 0 ### 1 indicates search for time words
    g1a = 0 ### 1 indicates exc result happens, e.g., BUILDING
    g1x = 0 ### 1 indicates beginning banner is found

    r1 = "^&&&& RUNNING\s*(.*)"
    #r2 = "SELECT 1 FROM eris_config WHERE target_arch='(.*)' AND target_os='(.*)' AND target_abi='' AND .* AND target_compiler='(.*)' AND gpu_device='(.*)' AND gpu_core.*"
    r_time = "(\d{4}[-]\d{2}[-]\d{2} \d{2}:\d{2}:\d{2}).*"
    FMT = '%Y-%m-%d %H:%M:%S'
    start_time = "N/A"
    end_time = "N/A"
    key_word_finish = "finished testsuite"

    stats_dict = dict()
    for ss in result_list:
        stats_dict[ss] = 0

    s1 = re.search(".*\\\\(.*)\.log", fn)
    if (s1):
        file_name = s1.group(1).strip()

    config_list = file_name.split("__")

    if len(config_list) < 10:
        print "error. config list len < 10"
        return

    mac_name = config_list[0]
    gpu_config = config_list[4]
    os_config = config_list[6]
    compiler_config = config_list[9]
    arch_config = config_list[5]

    l_a=[] ###test items that fail, list of tuple like (result, test name, count)
    l_b=[] ###all test items
    l_c=[] ###all test items with results, list of tuple like (result, test name, count)
    l_time=[]
    l_empty=[]

    while True:
        line = f.readline()
        if not line:
            break

        if (g0 == 0):
            s1 = re.search("testsuite \"(.*)\"", line)
            if (s1):
                g0 = 1
        else:
            s1 = re.search("%s" % r_time, line)
            if (s1):
                start_time = s1.group(1)
                l_time.append(s1.group(1))
            else:
                l_time.append("N/A")
                print "error: after testsuite, no start time"
            break

    pos1 = f.tell()
    prevline = line
    while True:
        line = f.readline() #continue from last while
        if not line:
            break
        s1 = re.search("%s" % key_word_finish, line)
        if (s1):
            s2 = re.search("%s" % r_time, prevline)
            if (s2):
                end_time = s2.group(1)
            break
        prevline = line

    f.seek(pos1)
    while True:
        line = f.readline() #continue from last while
        if not line:
            break
        if (g12 == 1):###search for time words after a test is finished
             g12 = 0
             s1 = re.search("%s" % r_time, line)
             if (s1):
                time1 = l_time[len(l_time)-1]
                time2 = s1.group(1)
                time_delta = "N/A"
                l_time.append(time2)
                #print "time1 = %s" % time1
                #print "time2 = %s" % time2
                if (time1 != "N/A"):
                    time_delta = datetime.strptime(time2, FMT) - datetime.strptime(time1, FMT)
                l_c.append((test_result, time_delta, test_name, cc ))
                continue
             else:
                 l_time.append("N/A")
                 l_c.append((test_result, "N/A", test_name, cc))

        if ((g1 == 1) and (g11 != 1)):
            for b in key_words:###key_words is for timeout/abort, 12-04
                s3 = re.search("%s" % b, line)
                if (s3):
                    g11 = 1
                    break
            if (g11 == 1):
                cc = l_b.count(test_name)
                l_c.append(("Timeout", "N/A", test_name, cc))
                #l_a.append(("Timeout", "N/A", test_name, cc))
                l_a.append(("Timeout", test_name, cc))
                stats_dict["Timeout"] += 1
                stats_dict["Total"] += 1
                g1x = 0
                continue
            s2 = re.search("%s" % r2, line)
            if (s2):
                if (g2 == 1):
                    b2 = s2.group(1).strip()
                    for b in exc_banner_list:###skip/ignore exc_banner, e.g. &&&& Building (samples_tests)
                        if (b2 == b):
                            g1a = 1
                            break
                    if (g1a == 1):
                        g1a = 0
                        continue
                    test_result = b2
                    cc = l_b.count(s2.group(2))
                    ###distinguish among tests with same name, e.g. 3 omp_basic are denoted as omp_basic, omp_basic[2], omp_basic[3](openMP, testsuite)
                    stats_dict["Total"] += 1
                    g12 = 1
                    g1x = 0
                    for b in result_list2:
                        if (b2 == b):
                            stats_dict[b2] += 1
                            break
                    for b in banners:
                        #print s2.group(1) == b
                        if (b2 == b):
                            l_a.append((b2, s2.group(2), cc))
                            break


                g1 = 0
                g2 = 1
                continue

            if (g2 == 1):
                for b in exc_words:
                ###if test log contains special words, skip/ignore the test. e.g., "Cannot read input file"(nvgraph_tests_L0)
                    s3 = re.search("%s" % b, line)
                    if (s3):
                        g2 = 0
                    break

        s1 = re.search("%s" % r1, line) ###search for beginning banner
        if (s1):
            g1 = 1
            g11 = 0
            g11a = 0
            s1_g1 = s1.group(1)
            s1_g1d = re.escape(s1_g1)
            if g1x == 1:###if finish banner is missing and timeout kw is found, assume fail
                cc = l_b.count(test_name)
                l_c.append(("FAILED", "N/A", test_name, cc))
                l_a.append(("FAILED", test_name, cc))
                stats_dict["FAILED"] += 1
                stats_dict["Total"] += 1
            g1x = 1
            r2 = "^&&&& (.*) (%s)" %  s1_g1d###one or two spaces
            test_name = s1.group(1)
            l_b.append(s1.group(1)) ###s1.group(1) is test name/exe, may contain space, so cannot strip()

        else:
            if (g11 == 1):###timeout keyword is found
                s11 = re.search("^&&&& NOT RUN\s*(.*)", line)
                if (s11):
                    test_name = s11.group(1)
                    cc = l_b.count(test_name)
                    l_c.append(("NotRun", "N/A", test_name, cc))
                    stats_dict["NotRun"] += 1
                    stats_dict["Total"] += 1
                else:
                    s12 = re.search("^&&&&", line)
                    if (s12):
                        g11 = 1
                    else:
                        s13 = re.search("%s" % r_time, line)
                        #print line
                        if (s13):
                            l_time.append(s13.group(1))
                            g11 = 0 ##end of read
                            g11a = 1
                        else:
                            print "error: after timeout, no time"

    if g1 == 1 and g11 != 1 and g11a != 1:
    ###after beginning banner, no end banner in the end of file; and is not timeout
    ###to-do, create a new status as timeout in the final, which indicates testsuite timeout
        test_name = s1_g1
        print "final test that is not timeout: %s" % test_name
        cc = l_b.count(test_name)
        l_c.append(("FAILED", "N/A", test_name, cc))
        l_a.append(("FAILED", test_name, cc))
        stats_dict["FAILED"] += 1
        stats_dict["Total"] += 1


    len_time = len(l_time)
    if (start_time != "N/A") and (end_time != "N/A"):
        tdelta = datetime.strptime(end_time, FMT) - datetime.strptime(start_time, FMT)
        t2 = "%s" % tdelta
        stats_dict["Duration"] = t2
    print stats_dict
    t = "%s,%s,%s,%s,%s," % (os_config, gpu_config, arch_config, compiler_config, mac_name)
    for ss in result_list:
        t += "%s," % stats_dict[ss]
    f6.write("%s\n" % t)


    f.close()

###output to fail.csv
    l_a_kw = filter_kw_one_file(fn, l_a)
    print_to_csv(l_a, (os_config, gpu_config, arch_config, compiler_config, mac_name),l_a_kw, True, f3)
###output to full.csv
    print_to_csv(l_c, (os_config, gpu_config, arch_config, compiler_config, mac_name), l_empty, True, f5)


def filter_kw_one_file(fn, l_a):
    f = open(fn, 'r')

    g0 = 0 ### 1 indicates occurence of testsuite begin words
    g1 = 0 ### 1 indicates after &&&& RUNNING
    g2 = 1 ### 1 indicates no occurence of key words
    i = 0 ### index for l_a
    kw = ""
    l_a_kw=[] ###test items that fail, list of tuple like (result, test name, count)

    if (len(l_a) == 0):
        return l_a_kw

    while True:
        line = f.readline()
        if not line:
            break

        if (g0 == 0):
            s1 = re.search("testsuite \"(.*)\"", line)
            if (s1):
                g0 = 1
                break

    while True:
        line = f.readline() #continue from last while
        if not line:
            break

        if (g1 == 1):
            s2 = re.search("%s" % r2, line)
            if (s2):
                l_a_kw.append((kw,))###war
                g1 = 0
                g2 = 1
                i = i + 1
                kw = ""
                if (i == len(l_a)):
                    break
                continue

            if (g2 == 1):
                ii = 0
                for b in key_words2:
                    s3 = re.search("%s" % b, line, re.IGNORECASE) ###2016-11-22
                    if (s3):
                        kw = key_words2a[ii]
                        g2 = 0 ###to-do, support multiple key words for one test, e.g., l_a[i].keyword[b]=1
                        break
                    ii = ii + 1


        testname = re.escape(l_a[i][1])
        r1 = "^&&&& RUNNING\s*%s" % testname
        s1 = re.search("%s" % r1, line)

        if(s1):
            g1 = 1
            r2 = "^&&&& FAILED\s*%s" % testname ###one or two spaces

    if g1 == 1: ###handle final test that doesn't finish with banner
        l_a_kw.append((kw,)) ###2016-11-22

    f.close()

    return l_a_kw

def readkw_from_file(fn):
    f = open(fn, 'r')
    kw = []

    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip()
        if line != "":
            kw.append(line)

    f.close()
    return kw


def main():
    parser = optparse.OptionParser()
    parser.add_option('-b','--branch',dest='branch',action='store',type='string',default=False,help='specify branch of submission, e.g., cuda_8_0_r378, cuda_a')
    parser.add_option('-l','--label',dest='label',action='store',type='string',default=False,help='specify label of submission, e.g., nightly')
    parser.add_option('-d','--date',dest='date',action='store',type='string',default=False,help='specify date of submission, e.g., 20170117')
    parser.add_option('-t','--testsuite',dest='testsuite',action='store',type='string',default=False,help='specify the name of testsuite, e.g., samples_tests')
    parser.add_option('-f','--configfile',dest='configfile',action='store',type='string',default=False,help='specify config file name for key words, e.g., C:\\a.txt, a.txt; each key word is separated by each line; white space is stripped for each key word')
    options,args = parser.parse_args()

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
    if options.configfile:
        kwconfigfile = options.configfile
    else:
        print 'ERROR: This script need option "--configfile" or "-f".'
        sys.exit(1)

#===================customize begin=======================================================
    global result_list, result_list2, banners, exc_banner_list, key_words, exc_words, key_words2, key_words2a
    in_dir = "C:\\Work\\auto-triage\\raw_data"
    out_dir = "C:\\Work\\auto-triage\\output"

    #dir_name = "samples_tests__cuda_a__nightly__20170117"
    dir_name = "%s__%s__%s__%s" % (testsuite, branch, label, date)

    mypath = "%s\\%s" % (in_dir, dir_name)
    out_dir2 = "%s\\%s" % (out_dir, dir_name)

    result_list = ["Duration", "Total", "PASSED", "FAILED", "Timeout", "NotRun", "WAIVED"]
    result_list2 = ["PASSED", "FAILED", "NotRun", "WAIVED"]###to-do, needs to be refined, e.g. notrun
    banners = ["FAILED"]###to-do: can be extended to RE, e.g. include timeout
    exc_banner_list = ["BUILDING"]
    key_words = ["timeout expired, test aborted"]###search after &&&&RUNNING

    key_words2a = readkw_from_file(kwconfigfile)
    print "key words:"
    print key_words2a

    key_words2 = []

    #key_words2a = ["error MSB4175", "MSB0001: ", "unable to find required executable file(s)", "code=38", "MSBUILD : error MSB1011: ", "Driver API error = 0003", "no CUDA-capable device", "could not get device count", "not supported by display ':0'", "failed to open display ':0'", "code=46(cudaErrorDevicesUnavailable)", "code=30(cudaErrorUnknown)"]
    #key_words2a = ["cuSolver Error (C:/p4sw/sw/gpgpu/nvgraph/src/lobpcg.cu:663): CUSOLVER_STATUS_EXECUTION_FAILED", "cuSolver Error (/home/erisuser/p4sw/sw/gpgpu/nvgraph/src/lobpcg.cu:663)"]
    #key_words2a = []

    ###to-do: can be extended to RE
    #exc_words = ["!!!!total fails"]
    exc_words = []
    #===================customize end=======================================================
    global f3, f5, f6

    onlyfiles = [join(mypath, f) for f in listdir(mypath) if isfile(join(mypath, f))]

    if not os.path.exists(out_dir2):
        os.makedirs(out_dir2)

    for b in key_words2a:
        b2 = re.escape(b)
        key_words2.append(b2)

    f3 = open('%s\\%s_fail.csv' % (out_dir2, dir_name), 'w')
    f5 = open('%s\\%s_full.csv' % (out_dir2, dir_name), 'w')
    f6 = open('%s\\%s_stats.csv' % (out_dir2, dir_name), 'w')

    f3.write("result,name,os,gpu,arch,compiler,mac,keywords\n")
    f6.write("os,gpu,arch,compiler,mac,duration,total,passed,failed,timeout,notrun,waived\n")

    for f in onlyfiles:
        parse_one_file(f)


    f3.close()
    f5.close()
    f6.close()

if __name__ == '__main__':
    main()