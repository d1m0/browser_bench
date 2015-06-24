#! /usr/bin/env python
import gspread
import argparse
from format import *
import sys
from stats import getMean
import pdb
import json
from oauth2client.client import SignedJwtAssertionCredentials

p = argparse.ArgumentParser(description=\
  "Given a set of runs for several browsers build a GoogleDocs spread sheet comparing the results")
p.add_argument('--key', type=str, help='Path to JSON key for Google Dev Project')
p.add_argument('--title', type=str, help='Title of an existing empty spreadsheet in which to work')
p.add_argument('results_file', type=str, help='File with raw results')
p.add_argument('--baseline', type=str, help='Label for the browser which should be considered baseline', required=False)

args = p.parse_args()

baseline = args.baseline if 'baseline' in args else None

print "Logging in ..."
json_key = json.load(open(args.key))                                                                                                                       
scope = ['https://spreadsheets.google.com/feeds']                                                                                                          
credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)                                                      
gc = gspread.authorize(credentials)                                                                                                                        
print "Opening {0}".format(args.title)
ws = gc.open(args.title).sheet1                 

print "Setting up document"
r = load(args.results_file) 

def putCol(ws, start_row, start_col, col):
	for i in xrange(0, len(col)):
		ws.update_cell(start_row + i, start_col, col[i])

# Table is assumed in row-major order
def putTblRowMajor(ws, start_row, start_col, tbl):
	rows = len(tbl)
	cols = len(tbl[0])
	sys.stderr.write("Uploading {0}x{1} table: {2}% Done\r".format(rows, cols, 0))
	for row in xrange(0, len(tbl)):
		for col in xrange(0, len(tbl[row])):
			sys.stderr.write("Uploading {0}x{1} table: {2}% Done\r".format(\
				rows, cols, (row*cols + col) * 100.0 /(rows*cols)))
			ws.update_cell(start_row + row, start_col + col, tbl[row][col])

def isRectangular(tbl):
	return len(set([len(x) for x in tbl])) == 1

def getRange(ws, startRow, startCol, endRow, endCol):
  return ws.get_addr_int(startRow, startCol) + ':' + ws.get_addr_int(endRow, endCol) 

def _putTblRowMajorFast(ws, start_row, start_col, tbl):
	assert isRectangular(tbl)
	rows = len(tbl)
	cols = len(tbl[0])
	end_row = start_row + rows - 1
	end_col = start_col + cols - 1
	windowHeight = 20
	windowWidth = 20

	for i in xrange(0, rows / windowHeight):
          wStartRow = i * windowHeight
	  for j in xrange(0, cols / windowWidth):
	    wStartCol = j * windowWidth
            window = [x[wStartCol:wStartCol + windowWidth] \
		for x in tbl[wStartRow:wStartRow+windowHeight]]
            _putTblRowMajorFast(ws, \
		start_row + wStartRow, start_col + wStartCol, window)


def putTblRowMajorFast(ws, start_row, start_col, tbl):
	assert isRectangular(tbl)
	rows = len(tbl)
	cols = len(tbl[0])
	end_row = start_row + rows - 1
	end_col = start_col + cols - 1
	rng = getRange(ws, start_row, start_col, end_row, end_col)

	sys.stderr.write("Uploading {0}x{1} table in range {2}...".format(rows, cols, rng))
	cell_list = ws.range(rng)

	# cell_list is in row major order. Build the value list in the same order
	values = []
	for row in xrange(0, len(tbl)):
		for col in xrange(0, len(tbl[row])):
			cell_list[row * cols + col].value = tbl[row][col]

	ws.update_cells(cell_list)
	sys.stderr.write("Done\n")


# Put general info about the test at the top
putTblRowMajorFast(ws, 1, 1, [ [ 'CPU:', cpuInfoStr(r)], \
			   ['Arch:', arch(r)], \
			   ['Ram:', str(ram(r)) + 'MB'],\
			   ['OS:', os(r)], \
			   ['Date:', time(r)] ])

def insertCol(tbl, beforeInd, col):
  for i in xrange(0, len(col)):
    tbl[i].insert(beforeInd, col[i]) 

  return tbl

def meansCol(col):
  bench = col_benchmark(col)
  return [getMean(x, bench) for x in col_scores(col)]

class Table:
  def __init__(self, row, col, rowNames, colNames, ws):
    self._row = row
    self._col = col
    self._rowNames = rowNames
    self._colNames = colNames
    self._rowInd = dict(zip(rowNames, range(0, len(rowNames))))
    self._colInd = dict(zip(colNames, range(0, len(colNames))))
    self._ws = ws
    self._contents = None

  def put(self):
    header = [ '' ] + self._colNames
    prepRows = [ [ x[0] ] + x[1] for x in zip(self._rowNames, self._contents)]
    try:
      putTblRowMajorFast(self._ws, self._row, self._col, [ header ] + prepRows)
    except gspread.httpsession.HTTPError as e:
      print e
      print dir(e)
      print e.code
      print e.message
      print e.response
      pdb.set_trace()
      raise e

  def cellLbl(self, rowName, colName):
    return self._ws.get_addr_int(self._row + self._rowInd[rowName] + 1, self._col + 1 + self._colInd[colName])

  def height(self):   return len(self._rowNames) + 1
  def width(self):   return len(self._colNames) + 1
  def setContents(self, c):   self._contents = c
  def colNames(self):   return self._colInd.keys()
  def rowNames(self):   return self._rowInd.keys()

def transpose(m):
  t = [[None for i in xrange(0, len(m))] for j in xrange(0, len(m[0]))]
  for i in xrange(0, len(m)):
    for j in xrange(0, len(m[i])):
      t[j][i] = m[i][j]

  return t

def buildResultsTable2(ws, startRow, startCol, r):
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

  contents = transpose([x[2:] for x in resCols]) + \
	[ meanRow, stdevRow, stdevRowPer, meanOverPerRow, stdevOverPerRow ]
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
resTbl = buildResultsTable2(ws, 7,1, r)
resTbl.put()
if (baseline):
  print "Building Summary of the Overhead table"
  sumTbl = buildSummaryTable(ws, 8 + resTbl.height(), 1, resTbl, r)
  sumTbl.put()
