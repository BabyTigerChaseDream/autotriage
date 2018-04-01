#!/usr/bin/env python
# This script is used to re-run the not run testsuite/config in eris nightly and weekly.
import optparse
import subprocess
import sys
import threading

def main():
    parser = optparse.OptionParser()
    parser.add_option('-f','--file',dest='file',action='store',type='string',default=False,help='specify file contains the compoent and config needed to re-run')
    parser.add_option('-p','--product',dest='product',action='store',type='string',default=False,help='specify the product, such as //sw/gpgpu/eris/cuda.vlcp')
    parser.add_option('-c','--cl',dest='cl',action='store',type='string',default=False,help='specify the nightly or weekly cl')
    parser.add_option('-u','--user',dest='user',action='store',type='string',default=False,help='specify the vulcan user')
    options,args = parser.parse_args()
    if options.file and options.product and options.cl:
        config = openfile(options.file)
        for i in config:
            t = threading.Thread(target=run_vulcan, args=(i,options.product,options.cl,options.user))
            t.start()
            t.join(1)
    else:
        print 'ERROR: This script need options "--file" , "--product" and "--cl".'
        sys.exit(1)

def openfile(txt):
    config_list = list()
    with open(txt,'r') as file:
        for line in file.readlines():
            if not line.startswith('{') and not line.startswith('#') and not line == "\n":
                component = line.strip('\n')
            elif line.startswith('{'):
                config = eval(line)
                config["component"] = component
                config_list.append(config)
            else: continue

    print "The following testsuite/config will be submitted:"
    for i in config_list:
       print i
    return config_list

def run_vulcan(config,product,cl,user=False):
    component = config["component"]
    gpu = config["gpu"]
    os = config["os"]
    arch = config["arch"]
    if config.has_key("compiler"):
        compiler = config["compiler"]
        target_compiler= "--target-compiler=%s"%compiler
    else:
        compiler = "default"
        target_compiler=""
    if config.has_key("build"): 
        build = config["build"]
        target_build="--target-build=%s"%build
    else:
        build = "release"
        target_build= ""
    if user:
        target_user="--user=%s"%user
    else:
        target_user=""
    tags = "NOT_RUN_%s_%s_%s_%s_%s_%s_CL%s"%(component,gpu, os,arch,compiler,build,cl)
    cmd =  "vulcan --product=%s --keep-going --build --testsuite %s --eris --target-gpu=%s --target-os=%s --target-arch=%s --target-revision=cl-%s --tags=%s %s %s %s"%(product,component,gpu,os,arch,cl,tags,target_compiler,target_build,target_user)
    proc = subprocess.Popen( cmd  , shell = True,  stdout = subprocess.PIPE )
    out = proc.stdout.read()
    ret = proc.wait()
    print cmd
    print out

if __name__ == '__main__':
    main()
