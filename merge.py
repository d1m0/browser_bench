#! /usr/bin/env python
import argparse
from format import loadOld, getInfo, load
from pickle import dumps, dump
from benchmark import error
import re


p = argparse.ArgumentParser(description=\
  "Merge several result files into a single result file")
p.add_argument('-o', type=str, help='Name of output file')
p.add_argument('inp', type=str, nargs='+', help='List of input files')
p.add_argument('--use-sysinfo', dest='use_sysinfo', action='store_const', const=True, default=False, help='Use the current machine\'s sys info for the merged test')

args = p.parse_args()

inp_files = []
name_pat = re.compile('(?P<benchmark>[^_]*)_(?P<count>[0-9]*)_(?P<label>[^\.]*)\.pickl')

for fname in args.inp:
  m = name_pat.match(fname)

  if (not m):
    inp_files.append(load(fname))
  else:
    benchmark = m.groupdict()['benchmark']
    count = m.groupdict()['count']
    label = m.groupdict()['label']
    inp_files.append(loadOld(fname, label, benchmark))


# Make sure that all have the same sys_info and time (both unknown) and same number
# of columns
all_cols = reduce(lambda x,y:  x + y['cols'], inp_files, [])
assert len(set(map(len, all_cols))) == 1

def canonify(d):
  if (isinstance(d, list)):
    return tuple(map(lambda x:	canonify(x), d))
  if (isinstance(d, dict)):
    items = map(lambda x:	(x[0], canonify(x[1])), d.items())
    items.sort()
    return tuple(items)
  else:
    return d

if (args.use_sysinfo):
  sysinfo = getInfo()
else:
  assert len(set(map(lambda x:  canonify(x['sys_info']), inp_files))) == 1
  sysinfo = inp_files[0]['sys_info']

newO = { 'sys_info': sysinfo,
         'time' : inp_files[0]['time'],
         'cols' : all_cols
       }

dump(newO, open(args.o, 'w'))
