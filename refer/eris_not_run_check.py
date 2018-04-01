#!/usr/bin/env python
# This script is used to find out testsuites did not run in eris nightly testing compared with batch file. There is only one option "--uuid " which is must.
import optparse
import subprocess
import json
import re
import sys
import os
import urllib2
import ssl
import cookielib
import datetime

def main():
    parser = optparse.OptionParser()
    parser.add_option('-u','--uuid',dest='uuid',action='store',type='string',default=False,help='specify the uuid of eris nightly')
    parser.add_option('-n','--uuid_not',dest='uuid_not',action='store',type='string',default=False,help='specify the uuid of not run')
    parser.add_option('-e','--email',dest='email',action='store',type='string',default=False,help='specify the mail username if needed')
    parser.add_option('-b','--batch',dest='batch',action='store_true',default=False,help='create batch file')
    parser.add_option('-c','--cl',dest='cl',action='store',type='string',default=False,help='specify the cl')
    options,args = parser.parse_args()
    if options.uuid and not options.batch and not options.uuid_not:
        run = not_run(options.uuid,options.email)
        run.run()
    elif options.uuid and options.batch:
        run = not_run(options.uuid)
        diff_list = run.run(out=False)
        info =run.return_info()
        cl = options.cl if options.cl else info[1]
        batch = create_batch()
        batch.run(info[0],diff_list,cl,info[2],options.uuid)
    elif options.uuid and options.uuid_not:
        run = not_run(options.uuid,options.email,options.uuid_not)
        run.run2()
    else:
        print 'ERROR: This script need option "--uuid" or "-u".'
        sys.exit(1)

def GetURLSource(url):
    if sys.version_info >= (2,7,9):
        ssl._create_default_https_context = ssl._create_unverified_context

    url_open = urllib2.urlopen(url)
    url_source = url_open.read()
    return url_source

def GetRunConfigs(uuid):
    eris_url = "https://eris-portal.nvidia.com/OneSubmissionTestSuitesServlet?uuid=%s&tableselector=dataTableOneSubmissionBuilds&url"%uuid
    #eris_results = urllib2.urlopen(eris_url).read()
    eris_results = GetURLSource(eris_url)
    AllRunConfigs= re.findall(r"badge-(passed|failed)\'>(.*?)<\\/span>.*?[^']&testSuiteNameText=(.*?)&.*?ConfigID=(.*?)\'>",eris_results)

    configID_list = list()
    for i in AllRunConfigs:
        #flag1 = True
        #if i[0] == "failed":
        #    if i[1] == "Failed Other" or i[1] == "Vrl Install Driver Timeout":
        #        flag1 = False
        flag1 = False
        if i[1].isdigit() or i[1] == "Vrl Vulcan Failure":
            flag1 = True
        if flag1 == True:
            configID_list.append(i[3])
    configID_list = list(set(configID_list))
    configID_dict = dict()
    for i in configID_list:
        configID_dict[i]=ConfigID(i)
    Configs= []
    for i in AllRunConfigs:
        #flag1 = True
        #if i[0] == "failed":
        #    if i[1] == "Failed Other" or i[1] == "Vrl Install Driver Timeout":
        #        flag1 = False
        flag1 = False
        if i[1].isdigit() or i[1] == "Vrl Vulcan Failure":
            flag1 = True
        if flag1 == True:
            config = list()
            lists = list(i)
            lists.extend(configID_dict[i[3]])
            if lists[11] == "[Default]":
                lists[11]=''
            config = [lists[2],lists[6],lists[8],lists[7],lists[11],lists[10]] ##name = [ 'components', 'gpu', 'os', 'arch', 'compiler', 'build']
            Configs.append(config)

    return Configs

def ConfigID(cid):
    url = "https://eris-portal.nvidia.com/GetTestHeaderServlet?testSuiteNameText=&testNameText=&erisConfigID=%s"%cid
    #url_open = urllib2.urlopen(url)
    #url_source = url_open.read()
    url_source = GetURLSource(url)
    res_td = r"<td>(.*?)<\\/td>"
    config = re.findall(res_td,url_source)
    return config


class create_batch:
    def run(self,product,diff_list,cl,p4root,uuid):
        vlcp = self.vlcp_path(product)
        command = self.commands(vlcp,diff_list,uuid)
        plan = self.plan()
        self.create(command,plan,uuid)
        self.cmd(p4root,cl)

    def commands(self,product,diff_list,uuid):
        components=list()
        for config in diff_list:
            components.append(config['components'])
        components = list(set(components))
        components.sort()
        self.components=components
        commands=list()
        for com in components:
            command = dict()
            command["components"] = com.split()
            command["name"] = com
            commands.append(command)
        for i in commands:
            target=list()
            for l in diff_list:
                tmp = l.copy()
                if i["name"] == tmp["components"]:
                    tmp["os"]   = l["os"].split()
                    tmp["gpu"]  = l["gpu"].split()
                    tmp["arch"] = l["arch"].split()
                    if tmp.has_key("compiler"):
                        tmp["compiler"] = l["compiler"].split()
                    del tmp["components"]
                    target.append(tmp)
            i["targets"] = target
        tags = "AUTO_NOT_RUN_%s"%uuid
        for i in commands:
            i["product"] = product
            if i["name"].find("32on64") == -1:
                command = [ "vulcan", "--eris", "--keep-going", "--tags=%s"%tags, "--user=sw-cuda-qa-sh", "--build", "--clean", "--testsuite" ]
            else:
                command = [ "vulcan", "--eris", "--keep-going", "--tags=%s"%tags, "--user=sw-cuda-qa-sh", "--build", "--clean", "--testsuite", "--test-system-arch=x86_64" ]

            i["command"] = command
        finalize = { "name"       : "finalize",
                     "is_final"   : "true",
                     "product"    : product,
                     "targets"    : [ { "arch" : [ "x86_64" ],  "os" : [ "Linux" ] } ],
                     "components" : [ "" ],
                     "command"    : [ "vulcan", "--eris", "--keep-going", "--tags=%s"%tags, "--user=sw-cuda-qa-sh", "--build", "compiler_internal_base" ] }
        commands.append(finalize)
        return commands

    def plan(self):
        plan = list()
        plan.append(self.components)
        plan.append(["finalize"])
        return plan

    def create(self,commands,plan,uuid):
        self.log = "%s/batch_%s.out"%(sys.path[0],uuid)
        print "&&&& The batch file is: %s"%self.log
        batch = dict()
        batch["commands"]=commands
        batch["plan"] = plan
        with open(self.log,'w') as files:
            files.write(json.dumps(batch,sort_keys=False,indent=4))

    def vlcp_path(self,product):
        vlcp_file = {
                      "CUDA Development"               : "//sw/gpgpu/eris/cuda.vlcp",
                      "CUDA 8.0 r361"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda.vlcp",
                      "CUDA 8.0"                       : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda.vlcp",
                      "CUDA 8.0 r367"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda_r367.vlcp",
                      "CUDA 8.0 r375"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda_r375.vlcp",
                      "CUDA 8.0 r378"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda_r378.vlcp",
                      "CUDA 9.0 r384"                  : "//sw/rel/gpgpu/toolkit/r9.0/eris/cuda_r384.vlcp",
                      "CUDA 8.0 chips_a"               : "//sw/rel/gpgpu/toolkit/r8.0/eris/cuda_chips_a.vlcp",
                      "CUDA gpgpu cuda_a"              : "//sw/gpgpu/eris/cuda.vlcp",
                      "CUDNN V5.1 CUDA 7.0 r346"       : "//sw/gpgpu/MachineLearning/cudnn_v5.1/eris/cudnn_70.vlcp",
                      "CUDNN V5.1 CUDA 7.5 r352"       : "//sw/gpgpu/MachineLearning/cudnn_v5.1/eris/cudnn_75.vlcp",
                      "CUDNN V5.1 CUDA 8.0 r361"       : "//sw/gpgpu/MachineLearning/cudnn_v5.1/eris/cudnn_80.vlcp",
                      "CUDNN V5.1 CUDA 8.0 r367"       : "//sw/gpgpu/MachineLearning/cudnn_v5.1/eris/cudnn_r80_r367.vlcp",
                      "GIE V1.0 CUDA 7.5 r352"         : "//sw/gpgpu/MachineLearning/DIT/release/1.0/eris/gie_75.vlcp",
                      "GIE V1.0 CUDA 8.0 r361"         : "//sw/gpgpu/MachineLearning/DIT/release/1.0/eris/gie_80.vlcp",
                      "GIE V1.0 CUDA 8.0 r367"         : "//sw/gpgpu/MachineLearning/DIT/release/1.0/eris/gie_80_r367.vlcp",
                      "Heterogeneous OpenMP Runtime gpgpu cuda_a"   : "//sw/gpgpu/runtimes/omp/omp.vlcp",
                      "ICE 1.1 CUDA 7.5 r352"          : "//sw/gpgpu/eris/ice11.vlcp",
                      "NCCL Public V1.2 CUDA 7.5 r352" : "//sw/gpgpu/nccl/eris/nccl_75_public.vlcp",
                      "NCCL Public V1.2 CUDA 8.0 r361" : "//sw/gpgpu/nccl/eris/nccl_80_public.vlcp",
                      "NCCL Public V1.2 CUDA 8.0 r367" : "//sw/gpgpu/nccl/eris/nccl_80_public_r367.vlcp",
                      "NCCL Private V1.5 CUDA7.5 r352" : "//sw/gpgpu/nccl/eris/nccl_75_private.vlcp",
                      "NCCL Private V1.5 CUDA8.0 r361" : "//sw/gpgpu/nccl/eris/nccl_80_private.vlcp",
                      "NCCL Private V1.5 CUDA8.0 r367" : "//sw/gpgpu/nccl/eris/nccl_80_private_r367.vlcp",
                      "OpenCL gpgpu r361"              : "//sw/gpgpu/opencl/eris/r361_00/opencl.vlcp",
                      "OpenCL gpgpu r367"              : "//sw/gpgpu/opencl/eris/r367_00/opencl.vlcp",
                      "OpenCL gpgpu r375"              : "//sw/gpgpu/opencl/eris/r375_00/opencl.vlcp",
                      "OpenCL gpgpu r378"              : "//sw/gpgpu/opencl/eris/r378_00/opencl.vlcp",
                      "OpenCL gpgpu r384"              : "//sw/gpgpu/opencl/eris/r384_00/opencl.vlcp",
                      "OpenCL gpgpu cuda_a"            : "//sw/gpgpu/opencl/eris/cuda_a/opencl.vlcp",
                      "OpenMPI gpgpu cuda_a"           : "//sw/gpgpu/eris/openmpi.vlcp",
                      "OpenMPI CUDA 8.0 r361"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/openmpi.vlcp",
                      "OpenMPI CUDA 8.0 r375"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/openmpi_r375.vlcp",
                      "OpenMPI CUDA 8.0 r378"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/openmpi_r378.vlcp",
                      "OpenMPI CUDA 9.0 r384"          : "//sw/rel/gpgpu/toolkit/r9.0/eris/openmpi_r384.vlcp",
                      "OpenMPI CUDA 8.0 r367"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/openmpi_r367_gp.vlcp"
                    }
        if vlcp_file.has_key(product):
            return vlcp_file[product]
        else:
            print 'Error: No such files product %s'%product
            sys.exit(1)
    def cmd(self,p4root,CL):
        vulcan = p4root + "/sw/eris/bin/vulcan"
        os.system("python %s --eris -v --target-revision=cl-%s --batch-file=%s"%(vulcan,CL,self.log))

class not_run:
    def __init__(self,uuid,mail=False,uuid_not=False):
        self.uuid = uuid
        self.mail = mail
        self.uuid_not = uuid_not

    def run(self,out=True):
        self.infor(self.uuid)
        batch_path = self.batch_path(self.product,self.tags,self.uname, self.re_rerun)
        source = self.get_source(self.uuid)
        target = self.get_batch(batch_path)
        diff_lists = self.diff(target,source)
        keep, exclude = self.diff_exclude(diff_lists)
        if out:
            self.output(keep,exclude)
            if self.mail:
                self.email(self.mail,self.product)
        else:
            return keep

    def run2(self):
        keep = self.run(out=False)
        source_not = self.get_source(self.uuid_not)
        for t in source_not:
            if t.has_key('compiler') and (t['compiler'] == '' or t['compiler'] == 'vc10'):
                del t['compiler']
            if t.has_key('build') and t['build'] == 'release':
                del t['build']

        diff_lists_not = self.diff(keep,source_not)
        self.output_not(diff_lists_not)

    def output_not(self,lists):
        components = list()
        log = "%s/run_not_run_%s.out"%(sys.path[0],self.uuid_not) 
        for config in lists:
            components.append(config['components'])
        components = list(set(components))
        components.sort()

        if os.path.isfile(log):
            os.remove(log)
        with open(log,'a') as files:
            files.write(self.info + '\n\nThe run not run link: https://eris-portal.nvidia.com/secure/DoOneSubmissionViewCommand?osuuid=%s'%self.uuid_not + '\n\nThe testsuites still did not run: \n' )
            for comp in components:
                files.write('\n'+comp+'\n')
                count = 0
                for config in lists:
                    if config.has_key('components') and config['components'] == comp:
                        del config['components']
                        files.write(json.dumps(config) + '\n')
                        count += 1
                    else: continue
        print 'The run not run link:://eris-portal.nvidia.com/secure/DoOneSubmissionViewCommand?osuuid=%s'%self.uuid_not
        print '&&&& The output file is "%s"'%log
        if self.mail:
            cmd='mail -s "[Need triage]Report of testsuites still not run on %s started at %s in eris %s testing." %s@exchange.nvidia.com < %s'%(self.product,self.time,self.tags,self.mail,log)
            out = self.proc(cmd)
            print '&&&& Sending email to %s... Done!'%self.mail


    def batch_path(self,branch,tags,uname,re_rerun):
        out = self.proc('p4 client -o')
        root = re.search('^Root:(.+)$',out,re.M)
        p4root = root.group(1).strip()
        self.p4root=p4root
        if re_rerun:
            batch_path = "batch_%s.out" % self.org_uuid
        else:
            if (uname == "sw-cuda-qa-sh" or uname =="erisuser") and tags == "nightly":
                batch = { "CUDA Development"     : "//sw/gpgpu/eris/batch/cuda.nightly",
                          "OpenCL Development"   : "//sw/gpgpu/eris/batch/opencl/cuda_a/opencl.nightly",
                          "OpenMPI Development"  : "//sw/gpgpu/eris/batch/openmpi.nightly",
                          "GDK Development"      : "//sw/dev/gpu_drv/chips_a/apps/gdk/eris/batch/gdk.nightly",
                          "OpenCL r361_00"       : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.nightly",
                          "CUDA 8.0"             : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda.nightly",
                          "OpenMPI 8.0"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/openmpi.nightly",
                          "GDK r361_00"          : "//sw/rel/gpu_drv/r361/r361_00/apps/gdk/eris/batch/gdk.nightly",
                          "CUDNN V5.1_7.0"       : "//sw/gpgpu/eris/batch/cudnn/cudnnV5.1_70.nightly",
                          "CUDNN V5.1_7.5"       : "//sw/gpgpu/eris/batch/cudnn/cudnnV5.1_75.nightly",
                          "CUDNN V5.1_8.0"       : "//sw/gpgpu/eris/batch/cudnn/cudnnV5.1_80.nightly",
                          "CUDNN V5.1_8.0_r367"  : "//sw/gpgpu/eris/batch/cudnn/cudnnV5.1_80_r367.nightly",
                          "ICE 1.1"              : "//sw/gpgpu/eris/batch/ice.nightly",
                          "Heterogeneous OpenMP Runtime" : "//sw/gpgpu/eris/batch/omp.nightly",
                          "GIE V1.0_CUDA7.5"     : "//sw/gpgpu/eris/batch/cudnn/gie_75.nightly",
                          "GIE V1.0_CUDA8.0"     : "//sw/gpgpu/eris/batch/cudnn/gie_80.nightly",
                          "GIE V1.0_CUDA8.0_r367": "//sw/gpgpu/eris/batch/cudnn/gie_80_r367.nightly",
                          "NCCL V1.2_CUDA7.5"    : "//sw/gpgpu/eris/batch/cudnn/nccl_75.nightly",
                          "NCCL V1.2_CUDA8.0"    : "//sw/gpgpu/eris/batch/cudnn/nccl_80.nightly",
                          "NCCL V1.2_CUDA8.0_r367": "//sw/gpgpu/eris/batch/cudnn/nccl_80_r367.nightly",
                          "CUDA 8.0 r367"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r367.nightly",
                          "CUDA 8.0 r367 GP"     : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r367_gp.nightly",
                          "CUDA 8.0 chips_a"     : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_chips_a.nightly",
                          "OpenCL r367_00 GP"    : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.nightly",
                             # new product
                          "CUDA gpgpu cuda_a"              : "//sw/gpgpu/eris/batch/cuda.nightly",
                          "CUDA 8.0 r375"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r375.nightly",
                          "CUDA 8.0 r378"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r378.nightly",
                          "CUDA 9.0 r384"                  : "//sw/rel/gpgpu/toolkit/r9.0/eris/batch/cuda_r384.nightly",
                          "GIE V1.0 CUDA 7.5 r352"         : "//sw/gpgpu/eris/batch/DeepLearning/gie_75.nightly",
                          "GIE V1.0 CUDA 8.0 r361"         : "//sw/gpgpu/eris/batch/DeepLearning/gie_80.nightly",
                          "GIE V1.0 CUDA 8.0 r367"         : "//sw/gpgpu/eris/batch/DeepLearning/gie_80_r367.nightly",
                          "CUDNN V5.1 CUDA 7.0 r346"       : "//sw/gpgpu/eris/batch/DeepLearning/cudnnV5.1_70.nightly",
                          "CUDNN V5.1 CUDA 7.5 r352"       : "//sw/gpgpu/eris/batch/DeepLearning/cudnnV5.1_75.nightly",
                          "CUDNN V5.1 CUDA 8.0 r361"       : "//sw/gpgpu/eris/batch/DeepLearning/cudnnV5.1_80.nightly",
                          "CUDNN V5.1 CUDA 8.0 r367"       : "//sw/gpgpu/eris/batch/DeepLearning/cudnnV5.1_80_r367.nightly",
                          "ICE 1.1 CUDA 7.5 r352"          : "//sw/gpgpu/eris/batch/ice.nightly",
                          "NCCL Public V1.2 CUDA 7.5 r352" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_75.nightly",
                          "NCCL Public V1.2 CUDA 8.0 r361" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_80.nightly",
                          "NCCL Public V1.2 CUDA 8.0 r367" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_80_r367.nightly",
                          "NCCL Private V1.5 CUDA7.5 r352" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_private_75.nightly",
                          "NCCL Private V1.5 CUDA8.0 r361" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_private_80.nightly",
                          "NCCL Private V1.5 CUDA8.0 r367" : "//sw/gpgpu/eris/batch/DeepLearning/nccl_private_80_r367.nightly",
                          "OpenCL dev r361"                : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.nightly",
                          "OpenCL dev r367"                : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.nightly",
                          "OpenCL gpgpu r361"              : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.nightly",
                          "OpenCL gpgpu r367"              : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.nightly",
                          "OpenCL gpgpu r375"              : "//sw/gpgpu/eris/batch/opencl/r375_00/opencl.nightly",
                          "OpenCL gpgpu r378"              : "//sw/gpgpu/eris/batch/opencl/r378_00/opencl.nightly",
                          "OpenCL gpgpu r384"              : "//sw/gpgpu/eris/batch/opencl/r384_00/opencl.nightly",
                          "OpenCL gpgpu cuda_a"            : "//sw/gpgpu/eris/batch/opencl/cuda_a/opencl.nightly",
                          "CUDA 8.0 r361"                  : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda.nightly",
                          "OpenMPI CUDA 8.0 r361"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/openmpi.nightly",
                          "OpenMPI CUDA 8.0 r367"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/openmpi_r367_gp.nightly",
                          "OpenMPI CUDA 8.0 r375"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/openmpi_r375.nightly",
                          "OpenMPI CUDA 8.0 r378"          : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/openmpi_r378.nightly",
                          "OpenMPI CUDA 9.0 r384"          : "//sw/rel/gpgpu/toolkit/r9.0/eris/batch/openmpi_r384.nightly",
                          "OpenMPI gpgpu cuda_a"           : "//sw/gpgpu/eris/batch/openmpi.nightly",
                          "Heterogeneous OpenMP Runtime gpgpu cuda_a" : "//sw/gpgpu/eris/batch/omp.nightly"
                        }
            elif (uname == "sw-cuda-qa-sh" or uname == "erisuser") and tags == "weekly" :
                batch = { "CUDA Development"     : "//sw/gpgpu/eris/batch/cuda.weekly",
                          "OpenCL Development"   : "//sw/gpgpu/eris/batch/opencl/cuda_a/opencl.weekly",
                          "OpenCL r361_00"       : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.weekly",
                          "OpenCL r367_00 GP"    : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.weekly",
                          "CUDA 8.0"             : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda.weekly",
                          "CUDA 8.0 r367"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r367.weekly",
                          "CUDA 8.0 r367 GP"     : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r367_gp.weekly",
                          #new product
                          "OpenCL dev r361"      : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.weekly",
                          "OpenCL dev r367"      : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.weekly",
                          "CUDA 8.0 r361"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda.weekly",
                          "CUDA 8.0 r375"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r375.weekly",
                          "CUDA 8.0 r378"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_r378.weekly",
                          "CUDA 9.0 r384"        : "//sw/rel/gpgpu/toolkit/r9.0/eris/batch/cuda_r384.weekly",
                          "OpenCL gpgpu r361"    : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.weekly",
                          "OpenCL gpgpu r367"    : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.weekly",
                          "OpenCL gpgpu r375"    : "//sw/gpgpu/eris/batch/opencl/r375_00/opencl.weekly",
                          "OpenCL gpgpu r378"    : "//sw/gpgpu/eris/batch/opencl/r378_00/opencl.weekly",
                          "OpenCL gpgpu r384"    : "//sw/gpgpu/eris/batch/opencl/r384_00/opencl.weekly",
                          "CUDA gpgpu cuda_a"    : "//sw/gpgpu/eris/batch/cuda.weekly"
                        }
            elif uname == "sw-cuda-qa-sh" and tags == "nightly_pascal":
                batch = { "CUDA 8.0 r361"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_pascal.nightly"
                        }
            elif uname == "sw-cuda-qa-sh" and tags == "weekly_pascal":
                batch = { "CUDA 8.0 r361"        : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cuda_pascal.weekly"
                        }
            elif (uname == "sw-cuda-qa-sh" or uname == "erisuser") and  tags == "biweekly":
                batch = {
                          "OpenCL r361_00"       : "//sw/gpgpu/eris/batch/opencl/r361_00/opencl.biweekly",
                         "OpenCL Development"   : "//sw/gpgpu/eris/batch/opencl/cuda_a/opencl.biweekly",
                          #new product
                          "OpenCL dev r361"      :"//sw/gpgpu/eris/batch/opencl/r361_00/opencl.biweekly",
                          "OpenCL dev r367"      : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.biweekly",
                          "OpenCL gpgpu r361"    :"//sw/gpgpu/eris/batch/opencl/r361_00/opencl.biweekly",
                          "OpenCL gpgpu r367"    : "//sw/gpgpu/eris/batch/opencl/r367_00/opencl.biweekly",
                          "OpenCL gpgpu r375"    : "//sw/gpgpu/eris/batch/opencl/r375_00/opencl.biweekly",
                          "OpenCL gpgpu r378"    : "//sw/gpgpu/eris/batch/opencl/r378_00/opencl.biweekly"
                        }
            elif uname == "devtools-compute-qa" and tags == "nightly":
                batch = { "CUDA Development"     : "//sw/gpgpu/eris/batch/cudatools.nightly",
                          "CUDA 8.0"             : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cudatools.nightly"
                        }
            elif uname == "devtools-compute-qa" and tags == "weekly":
               batch = { "CUDA Development"     : "//sw/gpgpu/eris/batch/cudatools.weekly",
                          "CUDA 8.0"             : "//sw/rel/gpgpu/toolkit/r8.0/eris/batch/cudatools.weekly"
                        }
            else :
                print 'Error: The username or the tags or the product is incorrect'
                sys.exit(1)

            self.proc('p4 sync -f %s@%s' %(batch[branch],self.cl))
            batch_path = p4root + batch[branch][1:]
        
        if os.path.isfile(batch_path):    
            print "The batch file:", batch_path
            return batch_path
        else:
            print 'Error: No such files, you must specify a file'
            sys.exit(1)

    def get_source(self,uuid):
        print '&&&& Login the portal and get data from the portal'
        all_configs_list = GetRunConfigs(uuid)

        source= list()
        for l in all_configs_list:
            name = [ 'components', 'gpu', 'os', 'arch', 'compiler', 'build']
            dic = dict(zip(name,l))
            source.append(dic)

        # This part is for amodel gpu testing.
        for d in source:
            if d['components'] in ['pascal_apps_gp100_amodel_tests_L0','pascal_apps_gp100_amodel_tests_L1','testsuite','appsuite','benchsuite'] and not d['gpu']:
                d['gpu'] = 'amodel_gp100'
            elif d['components'] == 'maxwell_apps_sm52_amodel_tests':
                d['gpu'] = 'amodel_gm204'
            elif d['components'] == 'kepler_apps_sm35_amodel_tests':
                d['gpu'] = 'amodel_gk110'
            elif d['components'] in ['volta_apps_gv100_amodel_tests_L0','volta_apps_gv100_amodel_tests_L1']:
                d['gpu'] = 'amodel_gv100'

        #with open('source.out','w') as files:
        #    files.write(json.dumps(source, sort_keys=True, indent=0))
        return source

    def remove_hash(self,str):
        non_comment = [ l if not l.lstrip().startswith('#') else ' ' for l in str.splitlines() ]
        return '\n'.join(non_comment)

    def get_batch(self,batch):
        with open(batch,'r') as file:
            config = self.remove_hash(file.read())
            try:
                config_json = json.loads(config)
            except Exception as e:
                print '&&&& The batch file%s is not a json file.'%files, e
                sys.exit(1)
            else:
                target = list()
                for testsuites in config_json['commands']:
                    if '--testsuite' in testsuites['command']:
                        components =  testsuites['components']
                        for i in testsuites['targets']:
                            i['components'] = ''.join(components)
                            i['arch']       = ''.join(i['arch'])
                            i['os']         = ''.join(i['os'])
                            i['gpu']        = ''.join(i['gpu'])
                            if i.has_key('compiler'):
                                i['compiler'] = ''.join(i['compiler'])
                            elif not i.has_key('compiler') and 'Windows' in i['os']:
                                i['compiler'] = 'vc10'
                            else:
                                i['compiler'] = ''
                            if i.has_key('build'):
                                i['build']    = ''.join(i['build'])
                            else:
                                i['build']    = 'release'
                            target.append(i)
                print '&&&& Read the batch file and get the config from the batch file'
                #with open('target.out','w') as files:
                #    files.write(json.dumps(target,indent=2))
                exclude = ["caffe_benchmark_teststorch_benchmark_teststheano_benchmark_tests", "caffe_builtin_tests", "theano_builtin_tests"]
                target = [i for i in target if i["components"] not in exclude]
                target_uniq = list()
                for t in target:
                    if t not in target_uniq:
                        target_uniq.append(t)

                return target_uniq

    def diff(self,target,source):
        print '&&&& Diff data between portal and batch file'
        self.num_target = len(target)
        self.num_source = len(source)
        diff_lists = list()
        for t in target:
            mark = 1
            for s in source:
                r = set(t.items())^set(s.items())
                if len(r) == 0:
                    mark = 0
                    break
                else:
                    mark = 1
                    continue
            if mark == 1:
                if t.has_key('compiler') and (t['compiler'] == '' or t['compiler'] == 'vc10'):
                   del t['compiler']
                if t.has_key('build') and t['build'] == 'release':
                   del t['build']
                diff_lists.append(t)
        self.num_not = len(diff_lists)
        print '&&&& Diff is completed and %s testsuites did not run.'%self.num_not
#        print diff_lists
        return diff_lists

    def diff_exclude(self,lists):
        testsuites = [ {"os": "Mac10_11", "gpu": "gtx980", "arch": "x86_64", "bug": "ERIS-1327"},
                       {"components": "caffe_builtin_tests", "bug" : "Not run in daily"},
                       {"components": "theano_builtin_tests", "bug" : "Not run in daily"},
                       {"components": "benchmark_tests_on_titan_x", "bug" : "Not run in daily"},
                       {"components": "benchmark_tests_on_titanZ", "bug" : "Not run in daily"},
                       { "gpu":  "p100",        "arch" :  "x86_64" ,  "os" :  "RHEL7_2",         "compiler" : "clang-llvm-3.8.0" ,  "bug" : "200209321"},
                       { "gpu":  "m60",        "arch" :  "x86_64" ,  "os" :  "RHEL7_2",         "compiler" : "clang-llvm-3.8.0" ,  "bug" : "200209321"},
                       { "gpu":  "k20c",       "arch" :  "x86_64" ,  "os" :   "RHEL7_2",         "compiler" : "clang-llvm-3.8.0"  ,  "bug" : "200209321"},
                       { "gpu":  "gtx980",     "arch" :  "x86_64" ,  "os" :  "Ubuntu16_04",     "compiler" : "clang-llvm-3.8.0"  ,  "bug" : "200209321"},
                       { "gpu":  "k5000",      "arch" :  "x86_64" ,  "os" :   "SLES12",          "compiler" : "clang-llvm-3.8.0" ,  "bug" : "200209321" }
 ]
#        testsuites  = [ {"components": "cublas_cnp_memcheck_tests", "bug" : "67890"},
#                        {"os": "RHEL7_1", "gpu": "m6000", "arch": "x86_64", "bug" : "123456"},
#                        {"components": "npp_tests","os": "RHEL7_1", "gpu": "k80m", "arch": "x86_64", "compiler": "icc15_5", "bug" : "9999999"}]
#
        keep    = list()
        exclude = list()
        for l in lists:
            mark = 1
            for i in testsuites:
                if len(i) == 2:
                    l["bug"] = i["bug"]
                    if l["components"] == i["components"]:
                        mark = 0
                        break
                    else:
                        mark = 1
                        continue
                else:
                    tmp = i.copy()
                    l["bug"] = i["bug"]
                    if not i.has_key("components"):
                        tmp["components"] = l["components"]
                    ret = set(l.items())^set(tmp.items())
                    if len(ret) == 0:
                        mark = 0
                        break
                    else:
                        mark = 1
                        continue
            if mark == 0:
                exclude.append(l)
            elif mark ==1:
                if l.has_key("bug"): del l["bug"]
                keep.append(l)

        return keep, exclude

    def output(self,lists,exclude):
        components = list()
        exclude_comp = list()
        self.log = '%s/not_run_%s_%s_%s_%s.out'%(sys.path[0],"_".join(self.product.split()),self.tags,self.cl,"_".join(self.time.split()))
        for config in lists:
            components.append(config['components'])
        components = list(set(components))
        components.sort()
        for config in exclude:
            exclude_comp.append(config['components'])
        exclude_comp = list(set(exclude_comp))
        exclude_comp.sort()

        num = '&&&& Total tests: %s\n&&&& Run tests: %s\n&&&& Not run tests: %s'%(self.num_target,self.num_source,self.num_not)
        print num
        if os.path.isfile(self.log):
            os.remove(self.log)
        with open(self.log,'a') as files:
            files.write(self.info + '\n\nThe testsuites did not run: \n' + num + '\n')
            for comp in components:
                files.write('\n'+comp+'\n')
                count = 0
                for config in lists:
                    if config.has_key('components') and config['components'] == comp:
                        del config['components']
                        files.write(json.dumps(config) + '\n')
                        count += 1
                    else: continue
#                files.write('#The amount is: '+str(count)+'\n')

            files.write('\n===========================================\n\nThe testsuites did not run due to known bug: \n')
            for comp in exclude_comp:
                files.write('\n'+comp+'\n')
                for config in exclude:
                    if config.has_key('components') and config['components'] == comp:
                        del config['components']
                        files.write(json.dumps(config) + '\n')
                    else: continue


        print '&&&& The output file is "%s"'%self.log

    def email(self,user,branch):
        cmd='mail -s "Report for testsuites not run on %s started at %s in eris %s testing." %s@exchange.nvidia.com < %s'%(branch,self.time,self.tags,user,self.log)
        out = self.proc(cmd)
        print '&&&& Sending email to %s... Done!'%user

    def infor(self,uuid):
        url = 'https://eris-portal.nvidia.com/GetSubmissionHeaderOneUuidServlet?uuid=%s'%uuid
        #url_open = urllib2.urlopen(url)
        #url_source = url_open.read()
        url_source = GetURLSource(url)
        title = testsuite_config = re.findall("<td>(.{,80}?)<\\\/td>",url_source)
        self.product = title[0]
        self.time    = title[1]
        self.uname   = title[2]
        self.cl      = title[3]
        self.tags    = title[4]
        self.duration= title[5]
        self.re_rerun  = False
        if "AUTO_NOT_RUN" in self.tags:
            org_uuid = self.tags.split("_")[-1]
            org_url = 'https://eris-portal.nvidia.com/GetSubmissionHeaderOneUuidServlet?uuid=%s'%org_uuid
            org_url_source = GetURLSource(org_url)
            org_title = re.findall("<td>(.{,80}?)<\\\/td>",org_url_source)
            self.tags = org_title[4]
            self.re_rerun = True
            self.org_uuid = org_uuid
        link = 'https://eris-portal.nvidia.com/secure/DoOneSubmissionViewCommand?osuuid=%s'%uuid
        self.info = 'Product: %s\nStart Time: %s\nChangelist: %s\nTags: %s\nUsername: %s\nDuration: %s\nRe_rerun: %s\nEris link: %s' %(self.product,self.time,self.cl,self.tags,self.uname,self.duration,self.re_rerun,link)
        print self.info

    def return_info(self):
        return self.product, self.cl, self.p4root

    def proc(self,cmd):
        proc = subprocess.Popen( cmd, shell = True, stderr = subprocess.PIPE, stdout = subprocess.PIPE )
        err = proc.stderr.read()
        out = proc.stdout.read()
        ret = proc.wait()
        if ret != 0:
            print err
            sys.exit(1)
        return out

if __name__ == '__main__':
    main()
