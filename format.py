from pickle import load as picklLoad, dump as picklDump
import sigar
from time import ctime

""" Define a on-disk format for raw profile run results"""
def getInfo():
  s = sigar.open();
  return {
    'cpu': map(lambda x:  {'model': x.model(), \
                           'speed': x.mhz_max(), \
                           'cache_size': x.cache_size(), \
                           'vendor':x.vendor()}, s.cpu_info_list()),
    'ram': s.mem().ram(),
    'arch':s.sys_info().arch(),
    'os': s.sys_info().vendor() + '_' + s.sys_info().vendor_version(),
    'name': s.net_info().host_name(),
   }

def getUnknownInfo():
  return {
    'cpu': [],
    'ram': 'unknown',
    'arch': 'unknown',
    'os': 'unknown', 
    'name': 'unknown',
   }

def cpuInfoStr(o):
  cpuInfo = o['sys_info']['cpu']
  if len(cpuInfo) > 0:
    return "{0} core {1} @ {2} Mhz".format(len(cpuInfo), cpuInfo[0]['model'], cpuInfo[0]['speed'])
  else:
    return "unknown"

def ram(o):
  return o['sys_info']['ram']

def os(o):
  return o['sys_info']['os']

def arch(o):
  return o['sys_info']['arch']

def name(o):
  return o['sys_info']['name']

def time(o):
  return o['time']

def cols(o):
  return o['cols']

def col_label(c):
  return c[0]

def col_benchmark(c):
  return c[1]

def col_binary(c):
  return c[2]

def col_scores(c):
  return c[3]

def store(cols, fname):
  o = { 'sys_info': getInfo(),
        'time' : ctime(),
        'cols' : cols }

  # Make sure columns are in the correct format - (label, benchmark, binary, [ scores ])
#  for c in cols:
#    assert isinstance(c, tuple) and len(c) == 4 and \
#           isinstance(c[0], str) and \
#           isinstance(c[1], str) and \
#           isinstance(c[2], str) and \
#           isinstance(c[3], list)

  # Assert all columns of the same length
#  assert(len(set(map(lambda c:  len(c[3]), cols))) == 1)
  picklDump(o, open(fname, 'w'))

def load(fname):
  o = picklLoad(open(fname, 'r'))

  if isinstance(o, dict):
    # Newer version results, just return
    return o;
  else:
    # Older format - single flat list
    assert isinstance(o, list)

    return { 'sys_info' : getUnknownInfo(),
             'time'     : 'unknown',
             'cols'       : [ ('unknown', 'unknown', 'unknown', o) ] }

def loadOld(fname, label, benchmark, sys_info = None):
  o = load(fname)
  assert len(o['cols']) == 1 and o['cols'][0][0] == 'unknown' and o['cols'][0][1] == 'unknown'

  o['cols'][0] = (label, benchmark, o['cols'][0][2], o['cols'][0][3])

  if (sys_info != None):
    o['sys_info'] = sys_info

  return o
