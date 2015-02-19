#! /usr/bin/env python

from sys import argv
import os

base = os.path.dirname(os.path.abspath(__file__)) + '/../browsers/Release_hybrid/'

def pickSDBrowser(bench):
  if 'html5' == bench:
    return base + 'chrome_fp_html5_forced_hybrid'
  elif 'sunspider' == bench:
    return base + 'chrome_fp_sunspider'
  elif 'octane' == bench:
    return base + 'chrome_fp_octane'
  elif 'kraken' == bench:
    return base + 'chrome_fp_kraken'
  elif 'balls' == bench:
    return base + 'chrome_fp_balls'
  else:
    return base + 'chrome_fp_html5_forced_hybrid'

if (__name__ == "__main__"):
  print pickSDBrowser(argv[1])
