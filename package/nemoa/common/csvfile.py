#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, nemoa, csv

def csvGetColLabels(file, delim = None, type = None):
    """Return list with column labels (first row) from csv file."""

    # get delimiter
    if not delim: delim = csvGetDelimiter(file)

    # get first line
    with open(file, 'r') as f: firstline = f.readline()

    # parse first line depending on type
    regEx = r'''\s*([^DELIM"']+?|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')\s*(?:DELIM|$)'''.replace('DELIM', re.escape(delim))
    r = re.compile(regEx, re.VERBOSE)
    if type == None: return r.findall(firstline)
    elif type == 'r-table': return [label.strip('\"\'')
        for label in ['label'] + r.findall(firstline)]

    return []

def csvGetDelimiter(file):
    """Return estimated delimiter of csv file."""

    found = False
    lines = 10
    while not found and lines < 100:
        with open(file, 'rb') as csvfile:
            probe = csvfile.read(len(csvfile.readline()) * lines)
            try:
                dialect = csv.Sniffer().sniff(probe)
                found = True
            except:
                lines += 10
    if found: return dialect.delimiter
    nemoa.log('warning', """
        could not import csv file '%s':
        could not determine delimiter!""" % (file))
    return None

def csvGetData(name, conf):
    #conf    = self.cfg['table'][name]['source']
    file    = conf['file']
    delim   = conf['delimiter'] if 'delimiter' in conf else csvGetDelimiter(file)
    cols    = conf['usecols']
    names   = tuple(self.getColLabels())
    formats = tuple(['<f8' for x in names])
    if not 'rows' in conf or conf['rows']:
        cols = (0,) + cols
        names = ('label',) + names
        formats = ('<U12',) + formats
    dtype = {'names': names, 'formats': formats}

    nemoa.log('info', "import data from csv file: " + file)

    try:
        #data = numpy.genfromtxt(file, skiprows = 1, delimiter = delim,
            #usecols = cols, dtype = dtype)
        data = numpy.loadtxt(file, skiprows = 1, delimiter = delim,
            usecols = cols, dtype = dtype)
    except:
        nemoa.log('error', 'could not import data from file!')
        return None

    return data