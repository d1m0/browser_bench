#! /usr/bin/env python
import argparse
from format import loadOld, getInfo, load, col_binary, col_label
from pickle import dumps, dump, dump
from benchmark import error
from browser_label import browserLabel
import re


p = argparse.ArgumentParser(description=\
  "Re-apply labels to a file based on the recorded binary path")
p.add_argument('inp', type=str, nargs='+', help='List of input files')

args = p.parse_args()

inp_files = []
name_pat = re.compile('(?P<benchmark>[^_]*)_(?P<count>[0-9]*)_(?P<label>[^\.]*)\.pickl')

for fname in args.inp:
  f = load(fname)
  def relabelCol(c):
    b = col_binary(c)

    if (b != 'unknown'):
      newL = browserLabel(b)
    else:
      newL = col_label(c)

    return (newL, c[1], c[2], c[3])

  f['cols'] = [relabelCol(c) for c in f['cols']]

  dump(f, open(fname, 'w'))
