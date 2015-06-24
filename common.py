#! /usr/bin/env python

import os
import sys

def debug(s):
  sys.stderr.write(s + '\n');

def error(s):
  debug(s);
  sys.exit(-1)

