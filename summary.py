#! /usr/bin/env python
import argparse
from format import load
from pickle import dumps, dump
from benchmark import error
import re


p = argparse.ArgumentParser(description=\
  "Print a summary of a given raw result file")
p.add_argument('inp', type=str, help='Name of input file')

args = p.parse_args()
r = load(args.inp)

if (len(r['sys_info']['cpu']) > 0):
  print "Test ran on {0} on machine {1} with a {2} core {3} CPU and {4} MB Ram running {5}".format(r['time'], \
       r['sys_info']['name'], \
       len(r['sys_info']['cpu']), \
       r['sys_info']['cpu'][0]['model'],
       r['sys_info']['ram'],
       r['sys_info']['os'])
else:
  print "Test ran on {0} on machine {1} with a unkown CPU and {2} MB Ram running {3}".format(r['time'], \
       r['sys_info']['name'], \
       r['sys_info']['ram'], \
       r['sys_info']['os'])

print "{0} columns:".format(len(r['cols']))
for c in r['cols']:
  print "Benchmark: {0}, label: {1}, browser_binary: {2}".format(\
    c[1], c[0], c[2])
