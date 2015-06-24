#! /usr/bin/env python
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os
import json
import subprocess
import sys
import argparse
from benchmark import runOneBenchmark, availableBenchmarks, runBenchmarkSet
from pickle import dump
from pick_safedispatch import pickSDBrowser
from common import error, debug

def compareBrowsers(browsers, benchmark, nruns, port):
  results = [tuple(browsers)]
  for i in xrange(0, args.nruns):
    one_run = []
    for browser in browsers:
      one_run.append(runOneBenchmark(browser, benchmark, port))
    results.append(tuple(one_run))

  return results

if (__name__ == '__main__'):
  parser = argparse.ArgumentParser(description='Run a single benchmark and print the results')
  parser.add_argument('--benchmark', type=str, nargs='+', help='name of benchmark to run. One of: ' + ' '.join(availableBenchmarks()))
  parser.add_argument('--nruns', type=int, help='number of times to run both')
  parser.add_argument('--browsers', type=str, nargs='+', help='path to browser executables to compare')
  parser.add_argument('--labels', type=str, nargs='+', help='human readable labels for each browser')
  args = parser.parse_args()

  if (len(args.browsers) != len(args.labels)):
    error("You must enter the same number of labels and browser")

  browserLabels = dict(zip(args.browsers, args.labels))

  for benchmark in args.benchmark:
    for browser in args.browsers:
      if browser == "safedispatch":
        binary = pickSDBrowser(benchmark)
      else:
        binary = browser

      

      name = benchmark + "_" + str(args.nruns) + "_" + browserLabels[binary] +\
        ".pickl"

      print "Running benchmark {0} for browser {1}".format(benchmark, browser)
      res = runBenchmarkSet(binary, benchmark, 5005, args.nruns)

      dump(res, open(name, 'w'))
