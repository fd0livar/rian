# -*- coding: utf-8 -*-
"""Numpy array functions."""

__author__ = 'Patrick Michl'
__email__ = 'frootlab@gmail.com'
__license__ = 'GPLv3'
__docformat__ = 'google'

import numpy as np
from numpy.lib import recfunctions as nprec
from nemoa.base import check
from nemoa.types import NpArray, NpRecArray, NpFields
from nemoa.types import StrPairDict, StrListPair, NaN, OptList
from nemoa.types import Number, OptNumber, List, OptStrList

#
# Array transformations
#

def from_dict(
        d: StrPairDict, labels: StrListPair, nan: Number = NaN) -> NpArray:
    """Convert dictionary to array.

    Args:
        d: Dictionary with keys (<*row*>, <*col*>), where the elemns <*row*> are
            row labels from the list <*rows*> and <*col*> column labels from the
            list *columns*.
        labels: Tuple of format (<*rows*>, <*columns*>), where <*rows*> is a
            list of row labels, e.g. ['row1', 'row2', ...] and <*columns*> a
            list of column labels, e.g. ['col1', 'col2', ...].
        nan: Value to mask Not Not a Number (NaN) entries. Missing entries in
            the dictionary are replenished by the NaN value in the array.
            Default: [IEEE754]_ floating point representation of NaN.

    Returns:
        :class:`numpy.ndarray` of shape (*n*, *m*), where *n* equals the number
        of <*rows*> and *m* the number of <*columns*>.

    """
    # Check type of 'd'
    check.has_type("argument 'd'", d, dict)

    # Declare and initialize return value
    x: NpArray = np.empty(shape=(len(labels[0]), len(labels[1])))

    # Get numpy ndarray
    setit = getattr(x, 'itemset')
    for i, row in enumerate(labels[0]):
        for j, col in enumerate(labels[1]):
            setit((i, j), d.get((row, col), nan))

    return x

def as_dict(
        x: NpArray, labels: StrListPair, nan: OptNumber = NaN) -> StrPairDict:
    """Convert two dimensional array to dictionary of pairs.

    Args:
        x: Numpy ndarray of shape (*n*, *m*), where *n* equals the number of
            <*rows*> and *m* the number of <*columns*>.
        labels: Tuple of format (<*rows*>, <*columns*>), where <*rows*> is a
            list of row labels, e.g. ['row1', 'row2', ...] and <*columns*> a
            list of column labels, e.g. ['col1', 'col2', ...].
        na: Optional value to mask Not a Number (NaN) entries. For cells in the
            array, which have this value, no entry in the returned dictionary
            is created. If nan is None, then for all numbers entries are
            created. Default: [IEEE754]_ floating point representation of NaN.

    Returns:
         Dictionary with keys (<*row*>, <*col*>), where the elemns <*row*> are
         row labels from the list <*rows*> and <*col*> column labels from the
         list *columns*.

    """
    # Check type of 'x'
    check.has_type("argument 'x'", x, np.ndarray)

    # Check dimension of 'x'
    if x.ndim != 2:
        raise TypeError(
            "Numpy ndarray 'x' is required to have dimension 2"
            f", not '{x.ndim}'")

    # Get dictionary with pairs as keys
    d: StrPairDict = {}
    for i, row in enumerate(labels[0]):
        for j, col in enumerate(labels[1]):
            val = x.item(i, j)
            if nan is None or not np.isnan(val):
                d[(row, col)] = val

    return d

def from_tuples(
        tuples: List[tuple], names: OptStrList = None,
        formats: OptList = None) -> NpArray:
    """Convert list of tuples into two dimensional array.

    Args:
        tuples: List of tuples

    Returns:
        :class:`numpy.ndarray` of shape (*n*, *m*), where *n* equals the number
        of <*rows*> and *m* the number of <*columns*>.

    """
    first_row = tuples[0]

    # Determine names from column index, if not given
    if names is None:
        names = [f'col{colid}' for colid in range(len(first_row))]

    # Determine formats, if not given
    if formats is None:
        formats = []
        for index, value in enumerate(first_row):
            if isinstance(value, str):
                # Determine maximum length
                maxlen = len(value)
                for row in tuples:
                    if len(row[index]) > maxlen:
                        maxlen = len(row[index])
                formats.append((str, maxlen))
            else:
                formats.append(type(value))

    # Get dtype from names and formats
    dtype = np.dtype({'names': names, 'formats': formats})

    return np.array(tuples, dtype=dtype)

def as_tuples(x: NpArray) -> List[tuple]:
    """Convert two dimensional array list of tuples.

    Args:
        x: Numpy ndarray of shape (*n*, *m*), where *n* equals the number of
            <*rows*> and *m* the number of <*columns*>.

    Returns:
        List of tuples.

    """
    # Check type of 'x'
    check.has_type("argument 'x'", x, np.ndarray)

    return x.tolist()

def add_cols(
        base: NpRecArray, data: NpRecArray,
        cols: NpFields = None) -> NpRecArray:
    """Add columns from source table to target table.

    Wrapper function to numpy's `rec_append_fields`_.

    Args:
        base: Numpy record array with table like data
        data: Numpy record array storing the fields to add to the base.
        cols: String or sequence of strings corresponding to the names of the
            new columns. If cols is None, then all columns of the data table
            are appended. Default: None

    Returns:
        Numpy record array containing the base array, as well as the
        appended columns.

    """
    cols = cols or getattr(data, 'dtype').names
    check.has_type("'cols'", cols, (tuple, str))
    cols = list(cols) # make cols mutable

    # Append fields
    return nprec.rec_append_fields(base, cols, [data[c] for c in cols])