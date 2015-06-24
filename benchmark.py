#! /usr/bin/env python
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os
import json
import subprocess
import sys
import signal
import argparse
from time import sleep
from format import store
from pick_safedispatch import pickSDBrowser
from browser_label import browserLabel
import posixpath
import urllib

base = os.path.dirname(os.path.abspath(__file__)) + '/static/'

def debug(s):
  sys.stderr.write(s + '\n');

def error(s):
  debug(s);
  sys.exit(-1)

def myread(fname, total_tries):
  try:
    fd = os.open(fname, os.O_NONBLOCK | os.O_RDONLY)
    f = os.fdopen(fd, 'rb')
    contents = ''
    tries = 0
    while tries < total_tries:
      try:
        tries += 1
        contents += f.read()
        f.close()
        return contents
      except IOError as e:
        if (e.errno != 11):
          raise e
        else:
          debug("Timeout on {0}".format(fname))
          sleep(1)
  except IOError as e:
    debug("Exception while reading {0}: {1}".format(fname, e))
    return None
  except OSError as e:
    debug("Exception while reading {0}: {1}".format(fname, e))
    return None
  except BaseException as e:
    debug("Other exception while reading {0}: {1}".format(fname, e))
    return None

def killall(pname):
  i = 0;
  while True:
    pids = [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]
    debug("killall({0}) iter {1}".format(pname, i))
    pids.sort()
    debug(str(pids))
    killed_at_least_one = False
    cmdline = None

    for pid in pids:
      try:
    	debug("Starting with pid {0}".format(pid))
        cmdline = myread(os.path.join('/proc', str(pid), 'cmdline'), 100)

    	debug("Read cmdline {0}".format(cmdline))

        if (not cmdline):
	  continue

	comm = os.path.basename(cmdline.split('\x00')[0].split(' ')[0])
        debug(str((pid, comm)))

        if (comm.strip() == pname):
          if i < 10:
            debug("Sending SIGTERM to process {0}, {1}".format(pid, comm))
            os.kill(int(pid), signal.SIGTERM)
          else:
            debug("Sending SIGKILL to process {0}, {1}".format(pid, comm))
            os.kill(int(pid), signal.SIGKILL)
          killed_at_least_one = True
      except IOError as e: # proc has already terminated
        debug("IOError while handling {0}: {1}".format(pid, e))
        continue
      except BaseException as e:
        debug("Other exception while handling {0}: {1}".format(pid, e))
        continue

    debug("Done iterating over pids")

    if (not killed_at_least_one):
      break;
    i+= 1
    sleep(2)


class BenchHTTPRequestHandler(SimpleHTTPRequestHandler):
  def do_POST(self):
    if (self.path.startswith('/results?')):
      res = json.loads(self.rfile.readline())
      self.send_response(200)
      self.server.results = res
      debug("Got Results. Terminating All Chrome processes" + str(self.server.proc.pid))
      killall(self.server.browser_name)
    else:
      self.send_error(404)

  # Copied from SimpleHTTPServer so we can override its default behavior
  # of looking for files starting in the current directory and look
  # starting in the script directory
  def translate_path(self, path):
    """Translate a /-separated PATH to the local filename syntax.
       Components that mean special things to the local file system
       (e.g. drive or directory names) are ignored.  (XXX They should
       probably be diagnosed.)
       """
    # abandon query parameters
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = posixpath.normpath(urllib.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = base 
    for word in words:
        drive, word = os.path.splitdrive(word)
        head, word = os.path.split(word)
        if word in (os.curdir, os.pardir): continue
        path = os.path.join(path, word)
    return path

def getContents(path):
  f = open(path)
  res = ''
  
  while True:
    t = f.read()
    if (t == ''): break
    res += t;

  return res

class HTTPD(HTTPServer):
  allow_reuse_address = True;

def runServer(port):
  s = HTTPD(('', port), BenchHTTPRequestHandler)
  s.serve_forever()

def runBenchmarkSet(browser, browser_args, benchmark, port, nruns):
  results = [];

  for i in xrange(0, nruns):
    results.append(runOneBenchmark(browser, browser_args, benchmark, port))

  return (browserLabel(browser), benchmark, browser, results)

def runOneBenchmark(browser, browser_args, benchmark, port):
  debug("Running one {0} benchmark for browser {1} on port {2}".format(\
	benchmark, browser, port))
  sleep(1);
  s = HTTPD(('', port), BenchHTTPRequestHandler)
  benchmark_url = benchmarkURLMap[benchmark] % { 'host': 'localhost', 'port': port }
  s.done = False

  def runServer(): 
    debug("Starting server thread")
    s.serve_forever(poll_interval=1)
    debug("Server thread finished")

  t = Thread(target = runServer)
  t.start()

  debug("Clearing cache directory...")
  subprocess.call(['rm', '-r', '/home/safedispatch/.cache/chromium'])
  debug("Starting Browser...")
  p = subprocess.Popen([browser] + browser_args + [benchmark_url])
  debug("Started browser process " + str(p.pid))
  s.browser_name = os.path.basename(browser).strip()
  s.proc = p;
  p.wait()

  debug("Browser finished. Shutting down server")
  s.shutdown()
  t.join();
  debug("Server thread has successfully finished")
  s.socket.close()
  try:
    return s.results
  except AttributeError:
    error("Browser {0} died on benchmark {1} before publishing results".format(\
      browser, benchmark))

benchmarkURLMap = {
# HTML5
  'html5':  "http://%(host)s:%(port)d/PerformanceTests/Parser/html5-full-render.html",
# SUNSPIDER
  'sunspider': "http://%(host)s:%(port)d/sunspider-1.0.2/sunspider-1.0.2/driver.html",
# OCTANE 
  'octane': "http://%(host)s:%(port)d/octane/index.html",
# KRAKEN 
  'kraken': "http://%(host)s:%(port)d/kraken/hosted/kraken-1.1/driver.html",
# ANIMATION
  'balls':  "http://%(host)s:%(port)d/PerformanceTests/Animation/balls.html",
# BINDINGS
  'append-child': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/append-child.html',
  'create-element': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/create-element.html',
  'document-implementation': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/document-implementation.html',
#  'event-target-wrapper': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/event-target-wrapper.html',
  'first-child': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/first-child.html',
  'gc-forest': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/gc-forest.html',
  'gc-mini-tree': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/gc-mini-tree.html',
  'gc-tree': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/gc-tree.html',
  'get-attribute': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/get-attribute.html',
  'get-element-by-id': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/get-element-by-id.html',
  'get-elements-by-tag-name': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/get-elements-by-tag-name.html',
  'id-getter': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/id-getter.html',
  'id-setter': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/id-setter.html',
  'insert-before': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/insert-before.html',
  'node-list-access': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/node-list-access.html',
  'scroll-top': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/scroll-top.html',
  'set-attribute': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/set-attribute.html',
  'typed-array-construct-from-array': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/typed-array-construct-from-array.html',
  'typed-array-construct-from-same-type': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/typed-array-construct-from-same-type.html',
  'typed-array-construct-from-typed': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/typed-array-construct-from-typed.html',
  'typed-array-set-from-typed': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/typed-array-set-from-typed.html',
  'undefined-first-child': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/undefined-first-child.html',
  'undefined-get-element-by-id': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/undefined-get-element-by-id.html',
  'undefined-id-getter': 'http://%(host)s:%(port)d/PerformanceTests/Bindings/undefined-id-getter.html',
# CANVAS
  'drawimage': 'http://%(host)s:%(port)d/PerformanceTests/Canvas/drawimage.html',
# CSS
  'CSSPropertySetterGetter': 'http://%(host)s:%(port)d/PerformanceTests/CSS/CSSPropertySetterGetter.html',
  'CSSPropertyUpdateValue': 'http://%(host)s:%(port)d/PerformanceTests/CSS/CSSPropertyUpdateValue.html',
  'PseudoClassSelectors': 'http://%(host)s:%(port)d/PerformanceTests/CSS/PseudoClassSelectors.html',
  'StyleSheetInsert': 'http://%(host)s:%(port)d/PerformanceTests/CSS/StyleSheetInsert.html',
#  'cssquery-dojo': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/cssquery-dojo.html',
  'cssquery-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/cssquery-jquery.html',
#  'cssquery-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/cssquery-prototype.html',
# DOM
  'Accessors': 'http://%(host)s:%(port)d/PerformanceTests/DOM/Accessors.html',
  'CloneNodes': 'http://%(host)s:%(port)d/PerformanceTests/DOM/CloneNodes.html',
  'CreateNodes': 'http://%(host)s:%(port)d/PerformanceTests/DOM/CreateNodes.html',
  'DOMDivWalk': 'http://%(host)s:%(port)d/PerformanceTests/DOM/DOMDivWalk.html',
  'DOMTable': 'http://%(host)s:%(port)d/PerformanceTests/DOM/DOMTable.html',
  'DOMWalk': 'http://%(host)s:%(port)d/PerformanceTests/DOM/DOMWalk.html',
  'Events': 'http://%(host)s:%(port)d/PerformanceTests/DOM/Events.html',
  'GetElement': 'http://%(host)s:%(port)d/PerformanceTests/DOM/GetElement.html',
  'GridSort': 'http://%(host)s:%(port)d/PerformanceTests/DOM/GridSort.html',
  'ModifyAttribute': 'http://%(host)s:%(port)d/PerformanceTests/DOM/ModifyAttribute.html',
  'Template': 'http://%(host)s:%(port)d/PerformanceTests/DOM/Template.html',
  'textarea-dom': 'http://%(host)s:%(port)d/PerformanceTests/DOM/textarea-dom.html',
  'textarea-edit': 'http://%(host)s:%(port)d/PerformanceTests/DOM/textarea-edit.html',
  'TraverseChildNodes': 'http://%(host)s:%(port)d/PerformanceTests/DOM/TraverseChildNodes.html',
# DROMAEO
  'dom-attr': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dom-attr.html',
  'dom-modify': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dom-modify.html',
  'dom-query': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dom-query.html',
  'dom-traverse': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dom-traverse.html',
  'dromaeo-3d-cube': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-3d-cube.html',
  'dromaeo-core-eval': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-core-eval.html',
  'dromaeo-object-array': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-object-array.html',
  'dromaeo-object-regexp': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-object-regexp.html',
  'dromaeo-object-string': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-object-string.html',
  'dromaeo-string-base64': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/dromaeo-string-base64.html',
#  404s - investigate
#  'jslib-attr-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-attr-jquery.html',
#  'jslib-attr-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-attr-prototype.html',
#  'jslib-event-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-event-jquery.html',
#  'jslib-event-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-event-prototype.html',
#  'jslib-modify-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-modify-jquery.html',
#  'jslib-modify-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-modify-prototype.html',
#  'jslib-style-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-style-jquery.html',
#  'jslib-style-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-style-prototype.html',
#  'jslib-traverse-jquery': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-traverse-jquery.html',
#  'jslib-traverse-prototype': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/jslib-traverse-prototype.html',
  'sunspider-3d-morph': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-3d-morph.html',
  'sunspider-3d-raytrace': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-3d-raytrace.html',
  'sunspider-access-binary-trees': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-access-binary-trees.html',
  'sunspider-access-fannkuch': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-access-fannkuch.html',
  'sunspider-access-nbody': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-access-nbody.html',
  'sunspider-access-nsieve': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-access-nsieve.html',
  'sunspider-bitops-3bit-bits-in-byte': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-bitops-3bit-bits-in-byte.html',
  'sunspider-bitops-bits-in-byte': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-bitops-bits-in-byte.html',
  'sunspider-bitops-bitwise-and': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-bitops-bitwise-and.html',
  'sunspider-bitops-nsieve-bits': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-bitops-nsieve-bits.html',
  'sunspider-controlflow-recursive': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-controlflow-recursive.html',
  'sunspider-crypto-aes': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-crypto-aes.html',
  'sunspider-crypto-md5': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-crypto-md5.html',
  'sunspider-crypto-sha1': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-crypto-sha1.html',
  'sunspider-date-format-tofte': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-date-format-tofte.html',
  'sunspider-date-format-xparb': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-date-format-xparb.html',
  'sunspider-math-cordic': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-math-cordic.html',
  'sunspider-math-partial-sums': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-math-partial-sums.html',
  'sunspider-math-spectral-norm': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-math-spectral-norm.html',
  'sunspider-regexp-dna': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-regexp-dna.html',
  'sunspider-string-fasta': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-string-fasta.html',
  'sunspider-string-tagcloud': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-string-tagcloud.html',
  'sunspider-string-unpack-code': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-string-unpack-code.html',
  'sunspider-string-validate-input': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/sunspider-string-validate-input.html',
  'v8-crypto': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/v8-crypto.html',
  'v8-deltablue': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/v8-deltablue.html',
  'v8-earley-boyer': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/v8-earley-boyer.html',
  'v8-raytrace': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/v8-raytrace.html',
  'v8-richards': 'http://%(host)s:%(port)d/PerformanceTests/Dromaeo/v8-richards.html',
  # INSPECTOR
#  'console-300-lines': 'http://%(host)s:%(port)d/PerformanceTests/inspector/console-300-lines.html',
#  'first-open-elements': 'http://%(host)s:%(port)d/PerformanceTests/inspector/first-open-elements.html',
#  'first-open-resources': 'http://%(host)s:%(port)d/PerformanceTests/inspector/first-open-resources.html',
#  'heap-snapshot-advanced': 'http://%(host)s:%(port)d/PerformanceTests/inspector/heap-snapshot-advanced.html',
#  'heap-snapshot': 'http://%(host)s:%(port)d/PerformanceTests/inspector/heap-snapshot.html',
#  'inspector-startup-time': 'http://%(host)s:%(port)d/PerformanceTests/inspector/inspector-startup-time.html',
# 'native-memory-snapshot': 'http://%(host)s:%(port)d/PerformanceTests/inspector/native-memory-snapshot.html',
  # INTERACTIVE
#  'window-resize': 'http://%(host)s:%(port)d/PerformanceTests/Interactive/window-resize.html',
  # LAYOUT
  'chapter-reflow': 'http://%(host)s:%(port)d/PerformanceTests/Layout/chapter-reflow.html',
  'chapter-reflow-once': 'http://%(host)s:%(port)d/PerformanceTests/Layout/chapter-reflow-once.html',
  'chapter-reflow-once-random': 'http://%(host)s:%(port)d/PerformanceTests/Layout/chapter-reflow-once-random.html',
  'chapter-reflow-thrice': 'http://%(host)s:%(port)d/PerformanceTests/Layout/chapter-reflow-thrice.html',
  'chapter-reflow-twice': 'http://%(host)s:%(port)d/PerformanceTests/Layout/chapter-reflow-twice.html',
  'flexbox-column-nowrap': 'http://%(host)s:%(port)d/PerformanceTests/Layout/flexbox-column-nowrap.html',
  'flexbox-column-wrap': 'http://%(host)s:%(port)d/PerformanceTests/Layout/flexbox-column-wrap.html',
  'flexbox-row-nowrap': 'http://%(host)s:%(port)d/PerformanceTests/Layout/flexbox-row-nowrap.html',
  'flexbox-row-wrap': 'http://%(host)s:%(port)d/PerformanceTests/Layout/flexbox-row-wrap.html',
  'floats_100_100': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_100_100.html',
  'floats_100_100_nested': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_100_100_nested.html',
  'floats_20_100': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_20_100.html',
  'floats_20_100_nested': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_20_100_nested.html',
  'floats_2_100': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_2_100.html',
  'floats_2_100_nested': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_2_100_nested.html',
  'floats_50_100': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_50_100.html',
  'floats_50_100_nested': 'http://%(host)s:%(port)d/PerformanceTests/Layout/floats_50_100_nested.html',
  'hindi-line-layout': 'http://%(host)s:%(port)d/PerformanceTests/Layout/hindi-line-layout.html',
  'line-layout': 'http://%(host)s:%(port)d/PerformanceTests/Layout/line-layout.html',
  'subtree-detaching': 'http://%(host)s:%(port)d/PerformanceTests/Layout/subtree-detaching.html',
  # MUTATION
#  'append-child-deep': 'http://%(host)s:%(port)d/PerformanceTests/Mutation/append-child-deep.html',
#  'append-child': 'http://%(host)s:%(port)d/PerformanceTests/Mutation/append-child.html',
#  'inner-html': 'http://%(host)s:%(port)d/PerformanceTests/Mutation/inner-html.html',
#  'remove-child-deep': 'http://%(host)s:%(port)d/PerformanceTests/Mutation/remove-child-deep.html',
#  'remove-child': 'http://%(host)s:%(port)d/PerformanceTests/Mutation/remove-child.html',
  # PARSER
  'css-parser-yui': 'http://%(host)s:%(port)d/PerformanceTests/Parser/css-parser-yui.html',
  'html5-full-render': 'http://%(host)s:%(port)d/PerformanceTests/Parser/html5-full-render.html',
  'html-parser': 'http://%(host)s:%(port)d/PerformanceTests/Parser/html-parser.html',
  'html-parser-srcdoc': 'http://%(host)s:%(port)d/PerformanceTests/Parser/html-parser-srcdoc.html',
  'innerHTML-setter': 'http://%(host)s:%(port)d/PerformanceTests/Parser/innerHTML-setter.html',
  'query-selector-deep': 'http://%(host)s:%(port)d/PerformanceTests/Parser/query-selector-deep.html',
  'query-selector-first': 'http://%(host)s:%(port)d/PerformanceTests/Parser/query-selector-first.html',
  'query-selector-last': 'http://%(host)s:%(port)d/PerformanceTests/Parser/query-selector-last.html',
  'simple-url': 'http://%(host)s:%(port)d/PerformanceTests/Parser/simple-url.html',
  'textarea-parsing': 'http://%(host)s:%(port)d/PerformanceTests/Parser/textarea-parsing.html',
  'tiny-innerHTML': 'http://%(host)s:%(port)d/PerformanceTests/Parser/tiny-innerHTML.html',
  'url-parser': 'http://%(host)s:%(port)d/PerformanceTests/Parser/url-parser.html',
  'xml-parser': 'http://%(host)s:%(port)d/PerformanceTests/Parser/xml-parser.html',
  # SHADOWDOM
  'ChangingClassName': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ChangingClassName.html',
  'ChangingClassNameShadowDOM': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ChangingClassNameShadowDOM.html',
  'ChangingSelect': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ChangingSelect.html',
  'ChangingSelectWithoutShadow': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ChangingSelectWithoutShadow.html',
#  'ContentReprojection': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ContentReprojection.html',
  'DistributionWithMultipleShadowRoots': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/DistributionWithMultipleShadowRoots.html',
  'LargeDistributionWithLayout': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/LargeDistributionWithLayout.html',
  'MultipleInsertionPoints': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/MultipleInsertionPoints.html',
  'ShadowReprojection': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/ShadowReprojection.html',
  'SmallDistributionWithLayout': 'http://%(host)s:%(port)d/PerformanceTests/ShadowDOM/SmallDistributionWithLayout.html',
  # SVG
  'AzLizardBenjiPark': 'http://%(host)s:%(port)d/PerformanceTests/SVG/AzLizardBenjiPark.html',
  'Bamboo': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Bamboo.html',
  'Cactus': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Cactus.html',
  'Cowboy': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Cowboy.html',
  'CrawFishGanson': 'http://%(host)s:%(port)d/PerformanceTests/SVG/CrawFishGanson.html',
  'Debian': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Debian.html',
  'DropsOnABlade': 'http://%(host)s:%(port)d/PerformanceTests/SVG/DropsOnABlade.html',
  'FlowerFromMyGarden': 'http://%(host)s:%(port)d/PerformanceTests/SVG/FlowerFromMyGarden.html',
  'FoodLeifLodahl': 'http://%(host)s:%(port)d/PerformanceTests/SVG/FoodLeifLodahl.html',
  'France': 'http://%(host)s:%(port)d/PerformanceTests/SVG/France.html',
  'FrancoBolloGnomeEzechi': 'http://%(host)s:%(port)d/PerformanceTests/SVG/FrancoBolloGnomeEzechi.html',
  'GearFlowers': 'http://%(host)s:%(port)d/PerformanceTests/SVG/GearFlowers.html',
  'HarveyRayner': 'http://%(host)s:%(port)d/PerformanceTests/SVG/HarveyRayner.html',
  'HereGear': 'http://%(host)s:%(port)d/PerformanceTests/SVG/HereGear.html',
  'MtSaintHelens': 'http://%(host)s:%(port)d/PerformanceTests/SVG/MtSaintHelens.html',
  'Samurai': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Samurai.html',
  'SierpinskiCarpet': 'http://%(host)s:%(port)d/PerformanceTests/SVG/SierpinskiCarpet.html',
  'SvgCubics': 'http://%(host)s:%(port)d/PerformanceTests/SVG/SvgCubics.html',
  'SvgHitTesting': 'http://%(host)s:%(port)d/PerformanceTests/SVG/SvgHitTesting.html',
#  'SvgNestedUse': 'http://%(host)s:%(port)d/PerformanceTests/SVG/SvgNestedUse.html',
  'UnderTheSee': 'http://%(host)s:%(port)d/PerformanceTests/SVG/UnderTheSee.html',
  'Worldcup': 'http://%(host)s:%(port)d/PerformanceTests/SVG/Worldcup.html',
  'WorldIso': 'http://%(host)s:%(port)d/PerformanceTests/SVG/WorldIso.html',
  # XSS Auditor
  #'large-post-many-events': 'http://%(host)s:%(port)d/PerformanceTests/XSSAuditor/large-post-many-events.html',
  #'large-post-many-inline-scripts-and-events': 'http://%(host)s:%(port)d/PerformanceTests/XSSAuditor/large-post-many-inline-scripts-and-events.html',
}

def availableBenchmarks(): return benchmarkURLMap.keys()

if (__name__ == '__main__'):
  parser = argparse.ArgumentParser(description='Run a single benchmark and print the results')
  parser.add_argument('command', type=str, choices=['run-server', 'list-available-benchmarks', 'run-benchmark'])
  parser.add_argument('--browser', type=str, nargs='+', help='path to browser executable')
  parser.add_argument('--browser_args', type=str, nargs='+', help='additional arguments to pass browser before the URL', default='')
  parser.add_argument('--benchmark', type=str, nargs='+', help='name of benchmark to run. One of: ' + ' '.join(availableBenchmarks()))
  parser.add_argument('--nruns', type=int, help='number of times to repeat a benchmark', default=1, required=False)
  parser.add_argument('--out', type=str, help='filename where to dump the outputs (as a pickled Python array)', default=1, required=False)
  args = parser.parse_args()

  if (args.command == 'run-server'):
    runServer(5005)
  elif (args.command == 'list-available-benchmarks'):
    print ' '.join(availableBenchmarks())
  elif (args.command == 'run-benchmark'):
    if (not args.browser or not args.benchmark):
      error('--browser and --benchmark requried for run-benchmark command')

    results = []
    for browser in args.browser:
      for benchmark in args.benchmark:
        if browser == "safedispatch":
          binary = pickSDBrowser(benchmark)
        else:
          binary = browser

        results.append(runBenchmarkSet(binary, args.browser_args, benchmark, 5005, args.nruns))

    if (args.out):
      store(results, args.out)
    else:
      for r in results:
        print r;
