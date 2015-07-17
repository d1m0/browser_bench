#! /usr/bin/env python
import gspread
import argparse
from format import *
import sys
from stats import getMean
import pdb
import json
from oauth2client.client import SignedJwtAssertionCredentials
from gsheets import openSS, Table, putRawTable

p = argparse.ArgumentParser(description=\
  "Given a set of runs for several browsers build a GoogleDocs spread sheet comparing the results")
p.add_argument('--key', type=str, help='Path to JSON key for Google Dev Project')
p.add_argument('--title', type=str, help='Title of an existing empty spreadsheet in which to work')
p.add_argument('results_file', type=str, help='File with raw results')
p.add_argument('--baseline', type=str, help='Label for the browser which should be considered baseline', required=False)
p.add_argument('--sheet', type=str, help='Worksheet name where we to put results', default='Sheet1', required=False)

args = p.parse_args()

baseline = args.baseline if 'baseline' in args else None

ss = openSS(args.key, args.title)
ws = ss.worksheet(args.sheet);

r = load(args.results_file) 

# Put general info about the test at the top
putRawTable(ws, 1, 1, [ [ 'CPU:', cpuInfoStr(r)], \
			   ['Arch:', arch(r)], \
			   ['Ram:', str(ram(r)) + 'MB'],\
			   ['OS:', os(r)], \
			   ['Date:', time(r)] ])

def isRectangular(tbl):
	return len(set([len(x) for x in tbl])) == 1

def meansCol(col):
  bench = col_benchmark(col)
  return [getMean(x, bench) for x in col_scores(col)]

def transpose(m):
  t = [[None for i in xrange(0, len(m))] for j in xrange(0, len(m[0]))]
  for i in xrange(0, len(m)):
    for j in xrange(0, len(m[i])):
      t[j][i] = m[i][j]

  return t

def buildResultsTable(ws, startRow, startCol, r):
  nruns = len(col_scores(cols(r)[0]))
  resCols = [[col_label(x), col_benchmark(x)] + meansCol(x) for x in cols(r)]

  def cname(col):   return str(col[1]) + ',' + str(col[0])

	# Furthermore we impose an ordering for neatness, and remember where vanilla values are
  def sortF(c1, c2):
    bench1 = col_benchmark(c1)
    bench2 = col_benchmark(c2)
    if (bench1 == bench2):
      lbl1 = col_label(c1)
      lbl2 = col_label(c2)
      if (lbl1 == lbl2):
        return 0
      elif lbl1 == 'vanilla':
        return -1
      elif lbl2 == 'vanilla':
        return 1
      else:	return cmp(lbl1, lbl2)
    else:
      return cmp(bench1, bench2)

  resCols.sort(cmp=sortF)
  if (baseline):
    rowNames = range(1, 1 + nruns) + [ 'Mean' ,'Std. Dev.', 'Std. Dev. (%)', 'Mean Overhead (%)', 'Overhead Std. Dev. (%)' ]
  else:
    rowNames = range(1, 1 + nruns) + [ 'Mean' ,'Std. Dev.', 'Std. Dev. (%)' ]

  colNames = [cname(c) for c in resCols]
  resTbl = Table(startRow, startCol, rowNames, colNames, ws)

  meanRow = ['=average({0}:{1})'.format(resTbl.cellLbl(1, colNames[i]), resTbl.cellLbl(nruns, colNames[i])) for i in xrange(0, len(colNames))]

  stdevRow = ['=stdev({0}:{1})'.format(resTbl.cellLbl(1, colNames[i]), resTbl.cellLbl(nruns, colNames[i])) for i in xrange(0, len(colNames))]

  stdevRowPer = ['={0} * 100.0 / {1}'.format(\
	resTbl.cellLbl('Std. Dev.', colNames[i]),
	resTbl.cellLbl('Mean', colNames[i]))
		for i in xrange(0, len(colNames))]

  if (baseline):
    meanOverPerRow = [('=({0}-{1})*100.0/{1}' if col_benchmark(c) != 'octane' else '=({1}-{0})*100.0/{1}').format(\
      resTbl.cellLbl('Mean', cname(c)), \
      resTbl.cellLbl('Mean', col_benchmark(c) + ',' + baseline)) \
      for c in resCols]

    stdevOverPerRow = ['=sqrt({0}*{0}+{1}*{1})*100.0/{2}'.format(\
      resTbl.cellLbl('Std. Dev.', cname(c)), 
      resTbl.cellLbl('Std. Dev.', col_benchmark(c) + ',' + baseline), 
      resTbl.cellLbl('Mean', col_benchmark(c) + ',' + baseline)) 
      for c in resCols]

  if (baseline):
    contents = transpose([x[2:] for x in resCols]) + \
    [ meanRow, stdevRow, stdevRowPer, meanOverPerRow, stdevOverPerRow ]
  else:
    contents = transpose([x[2:] for x in resCols]) + \
    [ meanRow, stdevRow, stdevRowPer ]
  assert isRectangular(contents)
  resTbl.setContents(contents)

  return resTbl

def buildSummaryTable(ws, startRow, startCol, resTbl, r):
  benchmarks = list(set([col_benchmark(x) for x in cols(r)]))
  browsers = list(set([col_label(x) for x in cols(r)]))

  sumTbl = Table(startRow, startCol, browsers, benchmarks + [ 'Average' ], ws)
  contents = [\
    ['=' + resTbl.cellLbl('Mean Overhead (%)', benchmark + ',' + str(browser)) \
      for benchmark in benchmarks] + \
      ['=average({0}:{1})'.format(sumTbl.cellLbl(browser, benchmarks[0]),
			          sumTbl.cellLbl(browser, benchmarks[-1]))] \

	for browser in browsers]
    
  sumTbl.setContents(contents)
  return sumTbl

print "Building Results table"
resTbl = buildResultsTable(ws, 7,1, r)
resTbl.put()
if (baseline):
  print "Building Summary of the Overhead table"
  sumTbl = buildSummaryTable(ws, 8 + resTbl.height(), 1, resTbl, r)
  sumTbl.put()
