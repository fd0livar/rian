# -*- coding: utf-8 -*-
import nemoa
import sys

class gene:

    robjects = None
    default  = 'entrezid'

    def __init__(self):

        stdout = sys.stdout
        try:
            sys.stdout = NullDevice()
            import rpy2.robjects
            self.robjects = rpy2.robjects
            sys.stdout = stdout
        except:
            sys.stdout = stdout
            nemoa.log("error", "could not import python package rpy2!")

    def _install(self, packages = [], quiet = True):

        # evaluate bioconductor R script
        base = self.robjects.packages.importr('base')
        base.source("http://bioconductor.org/biocLite.R")
        bioclite = self.robjects.globalenv['biocLite']

        # install bioconductor packages
        if packages == []:
            rCommand = "biocLite()"
            nemoa.log("info", "sending command to R: " + rCommand, quiet = quiet)
            try:
                self.robjects.r(rCommand)
            except:
                nemoa.log("error", "an error occured!")
        else:
            for package in packages:
                rCommand = "biocLite('%s')" % (package)
                nemoa.log("info", "sending command to R: " + rCommand, quiet = quiet)
                try:
                    self.robjects.r(rCommand)
                except:
                    sys.stdout = stdout
                    nemoa.log("error", "an error occured!")

    def convert_list(self, list, input_format, outputFormat, filter = False, quiet = True):
        """
        Return list with converted gene labels using R/bioconductor
        """

        if self.robjects == None:
            nemoa.log("error", "annotation: you have to install python package 'rpy2'")
            return [], list
        if outputFormat == None or outputFormat == 'default':
            outputFormat = self.default
        if input_format == outputFormat:
            return list, []

        # make local copy of list
        list = list[:]

        # convert using annotation packages in bioconductor
        annotation_packages = [
            'hgu95a', 'hgu95av2', 'hgu95b', 'hgu95c', 'hgu95d', 'hgu95e',
            'hgu133a', 'hgu133a2', 'hgu133b', 'hgu133plus2', 'hthgu133a',
            'hgug4100a', 'hgug4101a', 'hgug4110b', 'hgug4111a', 'hgug4112a',
            'hguqiagenv3'
        ]

        original_stdout = sys.stdout
        if input_format in annotation_packages:

            package_name = input_format + '.db'

            # load bioconductor annotation package
            nemoa.log("info", "sending command to R: library('%s')" % (package_name), quiet = quiet)
            try:
                sys.stdout = NullDevice()
                self.robjects.r.library(package_name)
                sys.stdout = original_stdout
            except:
                sys.stdout = original_stdout
                nemoa.log("warning", "could not find R/bioconductor package: '%s'" % (package_name))
                nemoa.log("warning", "trying to install ...")
                self._install([package_name], quiet = quiet)

            # get listvector
            nemoa.log("info", "sending command to R: x <- %s%s" % (input_format, outputFormat.upper()), quiet = quiet)
            try:
                sys.stdout = NullDevice()
                self.robjects.r('x <- %s%s' % (input_format, outputFormat.upper()))
                sys.stdout = original_stdout
            except:
                sys.stdout = original_stdout
                nemoa.log("error", "output format '%s' is not supported by '%s.db'" % (outputFormat, input_format))
                return [], list

            nemoa.log("info", "sending command to R: mapped_genes <- mappedkeys(x)", quiet = quiet)
            self.robjects.r('mapped_genes <- mappedkeys(x)')
            nemoa.log("info", "sending command to R: listmap <- as.list(x[mapped_genes])", quiet = quiet)
            self.robjects.r('listmap <- as.list(x[mapped_genes])')

            # prepare search list
            searchList = []
            for a in list:
                if a[0] == 'X':
                    a = a[1:]
                searchList.append(a)

        elif input_format == 'entrezid':
            # load bioconductor annotation package
            nemoa.log("info", "sending command to R: library('org.Hs.eg.db')", quiet = quiet)
            try:
                sys.stdout = NullDevice()
                self.robjects.r.library("org.Hs.eg.db")
                sys.stdout = original_stdout
            except:
                sys.stdout = original_stdout
                nemoa.log("error", "you have to install the R/bioconductor package: 'org.Hs.eg.db'")
                return [], list

            # get listvector
            nemoa.log("info", "sending command to R: x <- org.Hs.eg%s" % (outputFormat.upper()), quiet = quiet)
            try:
                self.robjects.r('x <- org.Hs.eg%s' % (outputFormat.upper()))
            except:
                nemoa.log("critical", "output format '%s' is not supported by 'org.Hs.eg.db'" % (outputFormat))
                quit()
            
            nemoa.log("info", "sending command to R: mapped_genes <- mappedkeys(x)", quiet = quiet)
            self.robjects.r('mapped_genes <- mappedkeys(x)')
            nemoa.log("info", "sending command to R: listmap <- as.list(x[mapped_genes])", quiet = quiet)
            self.robjects.r('listmap <- as.list(x[mapped_genes])')
            
            # prepare search list
            searchList = list

        elif outputFormat == 'entrezid':
            # load bioconductor annotation package
            nemoa.log("info", "sending command to R: library('org.Hs.eg.db')", quiet = quiet)
            try:
                sys.stdout = NullDevice()
                self.robjects.r.library("org.Hs.eg.db")
                sys.stdout = original_stdout
            except:
                sys.stdout = original_stdout
                nemoa.log("error", "you have to install the R/bioconductor package: 'org.Hs.eg.db'")
                return [], list

            # get listvector
            nemoa.log("info", "sending command to R: x <- org.Hs.eg%s2EG" % (input_format.upper()), quiet = quiet)
            try:
                self.robjects.r('x <- org.Hs.eg%s2EG' % (input_format.upper()))
            except:
                nemoa.log("error", "input format '%s' is not supported by 'org.Hs.eg.db'" % (input_format))
                return [], list

            nemoa.log("info", "sending command to R: mapped_genes <- mappedkeys(x)", quiet = quiet)
            self.robjects.r('mapped_genes <- mappedkeys(x)')
            nemoa.log("info", "sending command to R: listmap <- as.list(x[mapped_genes])", quiet = quiet)
            self.robjects.r('listmap <- as.list(x[mapped_genes])')

            # prepare search list
            searchList = list

        else:
            nemoa.log("error", "conversion from '%s' to '%s' is not supported" % \
                (input_format, outputFormat))
            return [], list

        # search listvector
        blackList = []
        nemoa.log("info", "sending command to R (for each column): sym <- listmap['COLUMNNAME']; sym <- unlist(sym)", quiet = quiet)
        for i, label in enumerate(searchList):
            label = label.strip(' ,\n\t\"')
            try:
                self.robjects.r("sym <- listmap['%s']" % (label))
                self.robjects.r("sym <- unlist(sym)")
                list[i] = self.robjects.globalenv["sym"][0]
            except:
                try:
                    self.robjects.r("sym <- listmap['%s']" % (label.lstrip('X')))
                    self.robjects.r("sym <- unlist(sym)")
                    list[i] = self.robjects.globalenv["sym"][0]
                except:
                    blackList.append(i)

        # filter results
        if filter:
            list = [item for item in list if list.index(item) not in blackList]

        return list, blackList

class NullDevice():
    def write(self, s):
        pass
    def flush(self, s):
        pass