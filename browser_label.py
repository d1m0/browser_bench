#! /usr/bin/env python

from sys import argv

def browserLabel(binary):
  if 'vanilla' in binary:
  	return 'vanilla'
  elif 'inverted_single_branch_with_vmethod_checks' in binary:
	return 'inverted-single-branch-with-vmethod-checks'
  elif 'inverted-single-branch-with-vmethod-checks' in binary:
	return 'inverted-single-branch-with-vmethod-checks'
  elif 'single-cmp-with-vmethod-checks' in binary:
	return 'single-cmp-with-vmethod-checks'
  elif 'instr-single-optimized' in binary:
  	return 'single-optimized'
  elif 'instr-single' in binary:
  	return 'single'
  elif 'one_64_one_32' in binary:
  	return 'one-64-one-32'
  elif 'instr-two-64' in binary:
  	return 'two-64'
  elif 'two-32-with-mptrs' in binary:
	return 'two-32-with-mptrs'
  elif 'instr-two-32' in binary:
  	return 'two-32'
  elif 'instr-optimized' in binary:
  	return 'double-optimized'
  elif 'instr' in binary:
  	return 'double'
  elif 'hybrid' in binary:
  	return 'safedisp'

if (__name__ == '__main__'):
  print browserLabel(argv[1])
