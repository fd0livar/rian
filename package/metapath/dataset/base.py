# -*- coding: utf-8 -*-
import metapath.common as mp
import numpy as np
import copy
import os
import re

class dataset:
    """metaPath base class for datasets"""

    #
    # DATASET CONFIGURATION
    #

    def __init__(self, config = {}, **kwargs):
        """Set configuration of dataset from dictionary"""
        self.cfg = None
        self.data = None
        self.setConfig(config)
        self.data = {}

    def setConfig(self, config):
        """Set configuration of dataset from dictionary"""
        self.cfg = config.copy()
        return True

    def getConfig(self):
        """
        Return configuration as dictionary
        """
        return self.cfg.copy()

    def getName(self):
        """
        Return name of dataset
        """
        return self.cfg['name'] if 'name' in self.cfg else ''

    def isEmpty(self):
        """
        Return true if dataset is empty
        """
        return not 'name' in self.cfg or not self.cfg['name']

    def configure(self, network, useCache = True, quiet = False, **kwargs):
        """
        Configure dataset to a given network object

        Keyword arguments:
        network -- metapath network object
        useCache -- shall data be cached
        """

        # load data from cachefile (if caching is used and cachefile exists)
        cacheFile = self.searchCacheFile(network) if useCache else None
        if cacheFile and self.load(cacheFile):
            mp.log('info', 'load cachefile: \'%s\'' % (cacheFile), quiet = quiet)

            # preprocess data
            if 'preprocessing' in self.cfg.keys():
                self.preprocessData(**self.cfg['preprocessing'])
            return True

        # create table with one record for every single dataset files 
        if not 'table' in self.cfg:
            conf = self.cfg.copy()
            self.cfg['table'] = {}
            self.cfg['table'][self.cfg['name']] = conf
            self.cfg['table'][self.cfg['name']]['fraction'] = 1.0

        #
        # ANNOTATION
        #

        import metapath.annotation

        # get nodes from network and convert to common format
        if network.cfg['type'] == 'auto':
            netGroups = {'v': None}
        else:
            # get grouped network node labels and label format
            netGroups = network.getNodeGroups(type = 'visible')
            netLblFmt = network.cfg['label_format']

            # convert network node labels to common format
            mp.log('info', 'search network nodes in dataset sources', quiet = quiet)
            convNetGroups = {}
            convNetGroupsLost = {}
            convNetNodes = []
            convNetNodesLost = []
            for group in netGroups:
                convNetGroups[group], convNetGroupsLost[group] = \
                    metapath.annotation.convert(netGroups[group], input = netLblFmt, quiet = True)
                convNetNodes += convNetGroups[group]
                convNetNodesLost += convNetGroupsLost[group]

            # notify if any network node labels could not be converted
            if convNetNodesLost:
                mp.log('warning', '%s of %s network nodes could not be converted! (see logfile)'
                    % (len(convNetNodesLost), len(convNetNodes)), quiet = quiet)
                ## 2DO get original node labels
                mp.log('logfile', mp.strToList(convNetNodesLost))

        # get columns from dataset files and convert to common format 
        colLabels = {}
        for src in self.cfg['table']:
            mp.log("info", "configure dataset source: '%s'" % (src))
            srcCnf = self.cfg['table'][src]

            # get column labels from csv-file
            if 'csvtype' in srcCnf['source']:
                csvType = srcCnf['source']['csvtype'].strip().lower()
            else:
                csvType = None
            origColLabels = self.csvGetColLabels(srcCnf['source']['file'], type = csvType)

            # set annotation format
            if 'columns' in srcCnf['source']:
                format = srcCnf['source']['columns']
            else:
                format = 'generic:string'

            # convert column labes
            convColLabels, convColLabelsLost = \
                metapath.annotation.convert(origColLabels, input = format, quiet = True)

            # notify if any dataset columns could not be converted
            if convColLabelsLost:
                mp.log("warning", 
                    "%i of %i dataset columns could not be converted! (logfile)"
                        % (len(convColLabelsLost), len(convColLabels)))
                mp.log("logfile", ", ".join([convColLabels[i] for i in convColLabelsLost]))

            if not network.cfg['type'] == 'auto':

                # search converted network nodes in converted column labels
                numLost = 0
                numAll = 0
                lostNodes = {}
                for group in netGroups:
                    lostNodesConv = [val for val in convNetGroups[group] if val not in convColLabels]
                    numAll += len(convNetGroups[group])
                    if not lostNodesConv:
                        continue
                    numLost += len(lostNodesConv)

                    # get original labels
                    lostNodes[group] = []
                    for val in lostNodesConv:
                        pos = convNetGroups[group].index(val)
                        lostNodes[group].append(netGroups[group][pos])

                # notify if any network nodes could not be found
                if numLost:
                    mp.log("warning", "%i of %i network nodes could not be found in dataset source! (logfile)" % (numLost, numAll))
                    for group in lostNodes:
                        mp.log("logfile", "missing nodes (group %s): " % (group) + ", ".join(lostNodes[group]))

            # prepare dictionary for column source ids
            colLabels[src] = {
                'conv': convColLabels,
                'usecols': (),
                'notusecols': convColLabelsLost }

        # intersect converted dataset column labels
        interColLabels = colLabels[colLabels.keys()[0]]['conv']
        for src in colLabels:
            list = colLabels[src]['conv']
            blackList = [list[i] for i in colLabels[src]['notusecols']]
            interColLabels = [val for val in interColLabels if val in list and not val in blackList]

        # if network type is 'auto', set network visible nodes
        # to intersected data from database files (without label column)
        if network.cfg['type'] == 'auto':
            netGroups['v'] = [label for label in interColLabels if not label == 'label']
            convNetGroups = netGroups

        # search network nodes in dataset columns
        self.cfg['columns'] = ()
        for group in netGroups:
            for id, col in enumerate(convNetGroups[group]):
                if not col in interColLabels:
                    continue

                # add column (use network label and group)
                self.cfg['columns'] += ((group, netGroups[group][id]), )

                for src in colLabels:
                    colLabels[src]['usecols'] += (colLabels[src]['conv'].index(col), )

        # update source file config
        for src in colLabels:
            self.cfg['table'][src]['source']['usecols'] = colLabels[src]['usecols']

        #
        # COLUMN & ROW FILTERS
        #

        # add column filters and partitions from network node groups
        self.cfg['colFilter'] = {'*': ['*:*']}
        self.cfg['colPartitions'] = {'groups': []}
        for group in netGroups:
            self.cfg['colFilter'][group] = [group + ':*']
            self.cfg['colPartitions']['groups'].append(group)

        # add row filters and partitions from sources
        self.cfg['rowFilter'] = {'*': ['*:*']}
        self.cfg['rowPartitions'] = {'source': []}
        for source in self.cfg['table']:
            self.cfg['rowFilter'][source] = [source + ':*']
            self.cfg['rowPartitions']['source'].append(source)

        #
        # DATA IMPORT
        #

        # import data from sources
        mp.log('info', 'import data from sources')
        self.data = {}
        for src in self.cfg['table']:
            self.data[src] = {
                'fraction': self.cfg['table'][src]['fraction'],
                'array': self.__csvGetData(src) }

        # save cachefile
        if useCache:
            cacheFile = self.createCacheFile(network)
            mp.log('info', 'save cachefile: \'%s\'' % (cacheFile), quiet = quiet)
            self.save(cacheFile)

        # preprocess data
        if 'preprocessing' in self.cfg.keys():
            self.preprocessData(**self.cfg['preprocessing'])

        return True

    #
    # DATA PREPROCESSING
    #

    def preprocessData(self, quiet = False, **dict):
        """Data preprocessing
        
        1. Stratification
        2. Normalization
        3. Transformation
        """
        if not dict:
            return True

        if 'stratify' in dict.keys():
            self.stratifyData(dict['stratify'])
        if 'normalize' in dict.keys():
            self.normalizeData(dict['normalize'])
        if 'convert' in dict.keys():
            self.transformData(dict['convert'])

        return True

    def stratifyData(self, algorithm = 'auto'):
        """Data preprocessing: Stratify data

        algorithm:
            'none':
                probabilities of sources are
                number of all samples / number of samples in source
            'auto':
                probabilities of sources are hierarchical distributed
                as defined in the configuration
            'equal':
                probabilities of sources are
                1 / number of sources
        """
        mp.log('info', 'preprocessing: stratify data using \'%s\'' % (algorithm))

        if algorithm.lower() in ['auto']:
            return True
        if algorithm.lower() in ['equal']:
            frac = 1.0 / float(len(self.data))
            for src in self.data:
                self.data[src]['fraction'] = frac
        return True

    def normalizeData(self, algorithm = 'gauss'):
        """Data preprocessing: Normalize data

        algorithm:
            'gauss', 'z-trans':
                aussian normalization (aka z-transformation)
        """
        mp.log('info', 'preprocessing: normalize data using \'%s\'' % (algorithm))

        if algorithm.lower() in ['gauss', 'z-trans']:

            # get data for calculation of mean and variance
            # for single source datasets take all data
            # for multi source datasets take a big bunch of stratified data
            if len(self.data.keys()) > 1:
                data = self.getData(size = 500000, output = 'recarray')
            else:
                data = self.getSourceData(source = self.data.keys()[0])

            # iterative update sources
            # get mean and standard deviation per column (recarray)
            # and update the values
            for src in self.data:
                for colName in self.data[src]['array'].dtype.names[1:]:
                    allMean = data[colName].mean()
                    allSdev = data[colName].std()
                    self.data[src]['array'][colName] = \
                        (self.data[src]['array'][colName] - allMean) / allSdev
            return True

        return False

    def transformData(self, algorithm = '', system = None, colLabels = None, **kwargs):
        """Data preprocessing: Transform data

        algorithm:
            'binary', 'bool':
                transform gaussian distributed data
                to binary data
        
        system: 
        """

        if isinstance(algorithm, str) \
            and algorithm.lower() in ['binary', 'bool']:
            mp.log('info', 'preprocessing: transform data using \'%s\'' % (algorithm))
            for src in self.data:

                # update source per column (recarray)
                for colName in self.data[src]['array'].dtype.names[1:]:

                    # update source data columns
                    self.data[src]['array'][colName] = \
                        (self.data[src]['array'][colName] > 0.0).astype(float)
            return True

        if mp.isSystem(system):
            mp.log('info', 'preprocessing: transform data using system \'%s\'' % (system.getName()))
            if not isinstance(colLabels, list):
                mp.log('info', 'transformation is not possible: no column labels have been given')
                return False

            for src in self.data:
                data = self.data[src]['array']
                colList = data.dtype.names[1:]
                dataArray = data[list(colList)].view('<f8').reshape(data.size, len(list(colList)))
                self.__setColLabels(colLabels)

                # transform data
                transArray = system.getDataRepresentation(dataArray, **kwargs)
                
                # create empty record array
                numRows = self.data[src]['array']['label'].size
                colNames = ('label',) + tuple(self.getColLabels())
                colFormats = ('<U12',) + tuple(['<f8' for x in colNames])
                newRecArray = np.recarray((numRows,), dtype = zip(colNames, colFormats))
                
                # set values in record array
                newRecArray['label'] = self.data[src]['array']['label']
                for colID, colName in enumerate(newRecArray.dtype.names[1:]):

                    # update source data columns
                    newRecArray[colName] = (transArray[:, colID]).astype(float)
                
                # set record array
                self.data[src]['array'] = newRecArray

            return True

        return False

    def getData(self, size = None, rows = '*', columns = '*', output = 'array'):
        """
        Return data from cache
        """

        # get stratified and row filtered data
        srcStack = ()
        for src in self.data.keys():
            srcArray = self.getSourceData(src, size, rows)
            if srcArray.size > 0:
                srcStack += (self.getSourceData(src, size, rows), )
        if not srcStack:
            return None
        data = np.concatenate(srcStack)

        # shuffle data
        if size:
            np.random.shuffle(data)

        # get column ids
        colIDs = list(data.dtype.names[1:])

        # output numpy array
        if output == 'array':
            return data[colIDs].view('<f8').reshape(data.size, len(colIDs))

        # output numpy record array
        if output == 'recarray':
            return data[['label'] + colIDs]

        # output row labels as list, data as numpy array
        if output == 'list,array':
            rlist = data['label'].tolist()
            array = data[colIDs].view('<f8').reshape(data.size, len(colIDs))
            return rlist, array

        return None

    def getSourceData(self, source = None, size = None, rows = '*'):
        if not source or not source in self.data:
            mp.log("warning", "unknown data source: '" + source + "'!")
            return None
        if not rows in self.cfg['rowFilter']:
            mp.log("warning", "unknown row group: '" + rows + "'!")
            return None

        # filter rows
        if rows == '*' or source + ':*' in self.cfg['rowFilter'][rows]:
            srcArray = self.data[source]['array']
        else:
            rowFilter = self.cfg['rowFilter'][rows]
            rowFilterFiltered = [
                row.split(':')[1] for row in rowFilter
                        if row.split(':')[0] in [source, '*']]
            rowSelect = np.asarray([
                rowid for rowid, row in enumerate(self.data[source]['array']['label'])
                    if row in rowFilterFiltered])
            if rowSelect.size == 0:
                return rowSelect
            srcArray = np.take(self.data[source]['array'], rowSelect)

        # if size is given, statify data
        if size:
            srcFrac = self.data[source]['fraction']
            rowSelect = np.random.randint(srcArray.size, size = round(srcFrac * size))
            return np.take(srcArray, rowSelect)

        return srcArray

    ## has no use at the moment
    def getMean(self):

        mean = 0
        for src in self.data.keys():
            srcFrac = self.data[source]['fraction']
            srcMean = self.data[source]['mean']
            mean += srcFrac * srcMean

        return mean

    # Labels and Groups

    def getColLabels(self, group = '*'):
        if group == '*':
            return ['%s:%s' % (col[0], col[1]) for col in self.cfg['columns']]
        if not group in self.cfg['colFilter']:
            return []
        colFilter = self.cfg['colFilter'][group]
        colLabels = []
        for col in self.cfg['columns']:
            if ('*', '*') in colFilter \
                or (col[0], '*') in colFilter \
                or ('*', col[1]) in colFilter \
                or (col[0], col[1]) in colFilter:
                colLabels.append('%s:%s' % (col[0], col[1]))
        return colLabels

    def __setColLabels(self, colLabels):
        """
        Set column labels
        """
        self.cfg['columns'] = ()
        for col in colLabels:
            self.cfg['columns'] += (col.split(':'), )
        return True

    def getRowLabels(self):
        labelStack = ()
        for source in self.data:
            labelStack += (self.data[source]['array']['label'],)
        labels = np.concatenate(labelStack).tolist()
        return labels

    def getColGroups(self):
        groups = {}
        for group, label in self.cfg['columns']:
            if not group in groups:
                groups[group] = []
            groups[group].append(label)
        return groups

    def getRowGroups(self):
        pass

    #
    # FILTERS
    #

    def addRowFilter(self, name, filter):
        # create unique name for filter
        filterName = name
        i = 1
        while filterName in self.cfg['rowFilter']:
            i += 1
            filterName = '%s.%i' % (name, i)

        # TODO: check filter
        self.cfg['rowFilter'][filterName] = filter
        return filterName

    def delRowFilter(self, name):
        if name in self.cfg['rowFilter']:
            del self.cfg['rowFilter'][name]
            return True
        return False

    def getRowFilter(self, name):
        if not name in self.cfg['rowFilter']:
            mp.log("warning", "unknown row filter '" + name + "'!")
            return []
        return self.cfg['rowFilter'][name]

    def getRowFilterList(self):
        return self.cfg['rowFilter'].keys()

    def addColFilter(self):
        pass

    def delColFilter(self, name):
        if name in self.cfg['colFilter']:
            del self.cfg['colFilter'][name]
            return True
        return False

    def getColFilters(self):
        return self.cfg['colFilter']

    #
    # PARTITIONS
    #

    def addRowPartition(self, name, partition):
        if name in self.cfg['rowPartitions']:
            mp.log("warning", "row partition '" + name + "' allready exists!")

        # create unique name for partition
        partitionName = name
        i = 1
        while partitionName in self.cfg['rowPartitions']:
            i += 1
            partitionName = '%s.%i' % (name, i)

        filterNames = []
        for id, filter in enumerate(partition):
            filterNames.append(
                self.addRowFilter('%s.%i' % (name, id + 1), filter))

        self.cfg['rowPartitions'][partitionName] = filterNames
        return partitionName

    def delRowPartition(self, name):
        pass

    def getRowPartition(self, name):
        if not name in self.cfg['rowPartitions']:
            mp.log("warning", "unknown row partition '" + name + "'!")
            return []
        return self.cfg['rowPartitions'][name]

    def getRowPartitionList(self):
        return self.cfg['rowPartitions'].keys()

    def createRowPartition(self, algorithm = 'bcca', **params):
        if algorithm == 'bcca':
            partition = self.getBccaPartition(**params)
        else:
            mp.log("warning", "unknown partition function '%s'")

        # add partition
        return self.addRowPartition(algorithm, partition)

    def getBccaPartition(self, **params):
        rowLabels, data = self.getData(output = 'list,array')
        numRows, numCols = data.shape

        # check parameters
        if 'groups' in params:
            groups = params['groups']
        else:
            mp.log("warning", "parameter 'groups' is needed to create BCCA partition!")
            return []

        # get BCCA biclusters
        biclusters = self.getBccaBiclusters(**params)

        # get bicluster distances
        distance = self.getBiclusterDistance(biclusters, **params)

        # cluster samples using k-means
        mp.log("info", 'cluster distances using k-means with k = %i' % (groups))
        clusters = self.getClusters(algorithm = 'k-means', data = distance, k = groups)
        cIDs = np.asarray(clusters)
        partition = []
        for cID in range(groups):
            partition.append(np.where(cIDs == cID)[0].tolist())

        # get labels
        labeledPartition = []
        for pID, c in enumerate(partition):
            labels = []
            for sID in c:
                labels.append(rowLabels[sID])
            labeledPartition.append(list(set(labels)))

        return labeledPartition

    #
    # CLUSTERING
    #

    def getClusters(self, algorithm = 'k-means', **params):
        if algorithm == 'k-means':
            return self.getKMeansClusters(**params)

        mp.log("warning", "unsupported clustering algorithm '" + algorithm + "'!")
        return None

    def getKMeansClusters(self, data, k = 3):
        from scipy.cluster.vq import kmeans,vq
        return vq(data, kmeans(data, k)[0])[0]

    #
    # BICLUSTERING
    #

    def getBiclusters(self, algorithm = 'bcca', **params):
        if algorithm == 'bcca':
            return getBccaBiclusters(**params)

        mp.log("warning", "unsupported biclustering algorithm '" + algorithm + "'!")
        return None

    def getBccaBiclusters(self, **params):
        data = self.getData(output = 'array')
        numRows, numCols = data.shape

        # check params
        if not 'threshold' in params:
            mp.log("info", "param 'threshold' is needed for BCCA Clustering!")
            return []
        if not ('minsize' in params or 'size' in params):
            mp.log("info", "param 'size' or 'minsize' is needed for BCCA Clustering!")
            return []

        # get params
        threshold = params['threshold']
        if 'minsize' in params:
            minsize = params['minsize']
            size = 0
        else:
            minsize = 3
            size = params['size']

        # start clustering
        mp.log("info", 'detecting bi-correlation clusters')
        startTime = time.time()

        biclusters = []
        for i in range(numCols - 1):
            for j in range(i + 1, numCols):

                npRowIDs = np.arange(numRows)

                # drop rows until corr(i, j) > sigma or too few rows are left
                rowIDs = npRowIDs.tolist()
                corr = np.corrcoef(data[:,i], data[:,j])[0, 1]

                while (size and len(rowIDs) > size) or \
                    (not size and len(rowIDs) > minsize and corr < threshold):
                    rowCorr = np.zeros(len(rowIDs))

                    for id in range(len(rowIDs)):
                        mask = rowIDs[:id] + rowIDs[id:][1:]
                        rowCorr[id] = np.corrcoef(data[mask, i], data[mask, j])[0, 1]

                    rowMaxID = rowCorr.argmax()
                    corr = rowCorr[rowMaxID]
                    rowIDs.pop(rowMaxID)

                if i == 0 and j == 1:
                    elapsed = time.time() - startTime
                    estimated = elapsed * numCols ** 2 / 2
                    mp.log("info", 'estimated duration: %.1fs' % (estimated))

                if corr < threshold:
                    continue

                # expand remaining rows over columns
                colIDs = [i, j]
                for id in [id for id in range(numCols) if id not in colIDs]:
                    if np.corrcoef(data[rowIDs, i], data[rowIDs, id])[0, 1] < threshold:
                        continue
                    if np.corrcoef(data[rowIDs, j], data[rowIDs, id])[0, 1] < threshold:
                        continue
                    colIDs.append(id)

                # append bicluster if not yet existing
                bicluster = (list(set(rowIDs)), list(set(colIDs)))
                if not bicluster in biclusters:
                    biclusters.append(bicluster)

        # info
        if size:
            mp.log("info", 'found %i biclusters with: correlation > %.2f, number of samples = %i' \
                % (len(biclusters), threshold, size))
        else:
            mp.log("info", 'found %i biclusters with: correlation > %.2f, number of samples > %i' \
                % (len(biclusters), threshold, minsize - 1))

        return biclusters

    #
    # BICLUSTER DISTANCES
    #

    def getBiclusterDistance(self, biclusters, **params):
        if 'distance' in params:
            type = params['distance']
        else:
            type = 'correlation'

        if type == 'hamming':
            return self.getBiclusterHammingDistance(biclusters)
        elif type == 'correlation':
            return self.getBiclusterCorrelationDistance(biclusters)

        mp.log("warning", "   unknown distance type '" + type + "'!")
        return None

    def getBiclusterHammingDistance(self, biclusters):
        data = self.getData(output = 'array')
        numRows, numCols = data.shape

        # create distance matrix using binary metric
        distance = np.ones(shape = (numRows, len(biclusters)))
        for cID, (cRowIDs, cColIDs) in enumerate(biclusters):
            distance[cRowIDs, cID] = 0

        return distance

    def getBiclusterCorrelationDistance(self, biclusters):
        ## EXPERIMENTAL!!
        data = self.getData(output = 'array')
        numRows, numCols = data.shape

        # calculate differences in correlation
        corrDiff = np.zeros(shape = (numRows, len(biclusters)))
        for cID, (cRowIDs, cColIDs) in enumerate(biclusters):
            
            # calculate mean correlation within bicluster
            cCorr = self.getMeanCorr(data[cRowIDs, :][:, cColIDs])
            
            # calculate mean correlation by appending single rows
            for rowID in range(numRows):
                corrDiff[rowID, cID] = cCorr - self.getMeanCorr(data[cRowIDs + [rowID], :][:, cColIDs])
        
        # calculate distances of samples and clusters
        distance = corrDiff
        #dist = np.nan_to_num(corrDiff / (np.max(np.max(corrDiff, axis = 0), 0.000001)))
        #dist = (dist > 0) * dist
        return distance

    def getMeanCorr(self, array, axis = 1):
        if not axis:
            array = array.T
        cCorr = np.asarray([])
        for i in range(array.shape[1] - 1):
            for j in range(i + 1, array.shape[1]):
                cCorr = np.append(cCorr, np.corrcoef(array[:, i], array[:, j])[0, 1])

        return np.mean(cCorr)

    def __csvGetData(self, srcName):
        fileCfg = self.cfg['table'][srcName]['source']
        file = fileCfg['file']

        if 'delimiter' in fileCfg:
            delim = fileCfg['delimiter']
        else:
            delim = self.csvGetDelimiter(file)

        usecols    = fileCfg['usecols']
        colNames   = tuple(self.getColLabels())
        colFormats = tuple(['<f8' for x in colNames])

        if not ('rows' in fileCfg and not fileCfg['rows']):
            usecols = (0,) + usecols
            colNames = ('label',) + colNames
            colFormats = ('<U12',) + colFormats

        mp.log('info', "import dataset source: " + file)

        return np.loadtxt(file,
            skiprows = 1,
            delimiter = delim,
            usecols = usecols,
            dtype = {'names': colNames, 'formats': colFormats})

    def csvGetColLabels(self, file, delim = None, type = None):
        """
        Return list with column labels (first row) from csv file
        """
        if not delim:
            delim = self.csvGetDelimiter(file)

        f = open(file, 'r')
        firstline = f.readline()
        f.close()

        regEx = r'''\s*([^DELIM"']+?|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')\s*(?:DELIM|$)'''.replace('DELIM', re.escape(delim))
        r = re.compile(regEx, re.VERBOSE)
        
        if type and type == 'r-table':
            colLabels = ['label'] + r.findall(firstline)
        else:
            colLabels = r.findall(firstline)

        return colLabels

    def csvGetDelimiter(self, file):
        """
        Return estimated delimiter of csv file
        """

        csvfile = open(file, 'rb')

        try:
            import csv
            dialect = csv.Sniffer().sniff(csvfile.read(4096))
        except:
            mp.log("warning", 
                "could not load file '" + file + "': could not determine delimiter!")
            return None

        csvfile.close()

        return dialect.delimiter

    #
    # object configuration handling
    #

    def save(self, file):
        np.savez(file,
            cfg = self.cfg,
            data = self.data)

    def getCacheFile(self, network):
        """
        Return cache file path
        """
        return '%sdata-%s-%s.npz' % (
            self.cfg['cache_path'], network.cfg['id'], self.cfg['id'])

    def searchCacheFile(self, network):
        """
        Return cache file path if existent
        """
        file = self.getCacheFile(network)
        return file if os.path.isfile(file) else None

    def createCacheFile(self, network):
        """
        Return empty cache file if existent
        """
        file = self.getCacheFile(network)
        if not os.path.isfile(file):
            basedir = os.path.dirname(file)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            with open(file, 'a'):
                os.utime(file, None)
        return file

    def load(self, file):
        npzfile = np.load(file)
        self.cfg  = npzfile['cfg'].item()
        self.data = npzfile['data'].item()
        return True

    def _get(self, sec = None):
        dict = {
            'data': copy.deepcopy(self.data),
            'cfg': copy.deepcopy(self.cfg)
        }

        if not sec:
            return dict
        if sec in dict:
            return dict[sec]

        return None

    def _set(self, **dict):
        if 'data' in dict:
            self.data = copy.deepcopy(dict['data'])
        if 'cfg' in dict:
            self.cfg = copy.deepcopy(dict['cfg'])

        return True
