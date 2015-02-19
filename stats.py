#! /usr/bin/env python
from pickle import load
import argparse
from benchmark import availableBenchmarks, error
import sys

def ave(l):	return sum(l) / (1.0 * len(l))
def overhead(a,b):	return (a-b)*100.0/b


def getMeanSunspider(raw):
   return ave([sum(x.values()) for x in raw])

def getMeanWebKit(raw):
   return raw['mean']

def getMeanOctane(raw):
   return int(raw['total'])

def getMeanKraken(raw):
   return ave([sum(x.values()) for x in raw])

def getMean(raw, benchmark):
  if (benchmark == 'sunspider'):
    return getMeanSunspider(raw)
  elif (benchmark == 'html5'):
    return getMeanWebKit(raw)
  elif (benchmark == 'octane'):
    return getMeanOctane(raw)
  elif (benchmark == 'kraken'):
    return getMeanKraken(raw)
  else:
    print "Unknown benchmark " + benchmark
    sys.exit(-1)

def getMeans(raw, benchmark):
  return [[getMean(y, benchmark) for y in x] for x in raw]

def getMeansSingle(raw, benchmark):
  return [getMean(x, benchmark) for x in raw]

def crunch(means):
  ave_vanila = ave([x[0] for x in means])
  overhead_of_means = []
  mean_of_overheads = []
  for ind in xrange(1, len(means[0])):
    overhead_of_means.append(overhead(ave([x[ind] for x in means]), ave_vanila))
    mean_of_overheads.append(ave([overhead(x[ind], x[0]) for x in means]))
  print "Overhead of means:"
  for x in overhead_of_means:
    sys.stdout.write(str(x) + '\t')
  sys.stdout.write('\n')
  print "Mean of overheads:"
  for x in mean_of_overheads:
    sys.stdout.write(str(x) + '\t')
  sys.stdout.write('\n')

if (__name__ == '__main__'):
  parser = argparse.ArgumentParser(description='Compute stats for a given set of results')
  parser.add_argument('command', type=str, help='path of the raw results file', choices=['print-means', 'compute-overhead'] )
  parser.add_argument('raw_results', type=str, help='path of the raw results file')
  parser.add_argument('benchmark', type=str, help='name of benchmark to run. One of: ' + ' '.join(availableBenchmarks()))
  args = parser.parse_args()
  raw = load(open(args.raw_results))
  labels = raw[0]
  values = raw[1:]
  means = getMeansSingle(raw, args.benchmark)

  if (args.command == 'print-means'):
#    for l in labels:
#      sys.stdout.write(str(l) + "\t")
#    sys.stdout.write("\n")

    for r in means:
      #sys.stdout.write(str(r) + "\t")
      sys.stdout.write(str(r))
#      for v in r:
#        sys.stdout.write(str(v) + "\t")
      sys.stdout.write("\n")
  elif (args.command == 'compute-overhead'):
    for l in labels[1:]:
      sys.stdout.write(str(l) + "\t")
    sys.stdout.write("\n")

    crunch(means)
  else:
    error("Unknown command " + args.command)

