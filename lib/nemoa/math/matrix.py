# -*- coding: utf-8 -*-
"""Matrix Norms and Metrices.

.. References:
.. _IEEE 754: https://ieeexplore.ieee.org/document/4610935/

"""

__author__ = 'Patrick Michl'
__email__ = 'frootlab@gmail.com'
__license__ = 'GPLv3'
__docformat__ = 'google'

try:
    import numpy as np
except ImportError as err:
    raise ImportError(
        "requires package numpy: "
        "https://pypi.org/project/numpy") from err

from nemoa.base import assess, check, this
from nemoa.math import vector
from nemoa.types import Any, IntTuple, NpArray, NpArrayLike, StrList
from nemoa.types import StrPairDict, StrListPair, NaN, Number, OptNumber

_NORM_PREFIX = 'norm_'
_DIST_PREFIX = 'dist_'

#
# Matrix Norms
#

def norms() -> StrList:
    """Get sorted list of matrix norms.

    Returns:
        Sorted list of all matrix norms, that are implemented within the module.

    """
    return this.crop_functions(prefix=_NORM_PREFIX)

def norm(x: NpArrayLike, name: str = 'frobenius', **kwds: Any) -> NpArray:
    """Calculate norm of matrix.

    References:
        [1] https://en.wikipedia.org/wiki/magnitude_(mathematics)

    Args:
        x: Any sequence that can be interpreted as a numpy ndarray of two or
            more dimensions. This includes nested lists, tuples, scalars and
            existing arrays.
        name: Name of matrix norm. Accepted values are:
            'pq': pq-norm (induces: pq-distances)
                Remark: requires additional parameters 'p' and 'q'
            'frobenius': Frobenius norm (induces: Frobenius distance)
            Default: 'frobenius'
        **kwds: Parameters of the given norm / class of norms.
            The norm Parameters are documented within the respective 'norm'
            functions.

    Returns:
        NumPy ndarray of dimension <dim x> - 2.

    """
    # Check Type of 'x'
    try:
        x = np.array(x)
    except TypeError as err:
        raise TypeError(
            "first argument 'x' is required to be array-like") from err

    # Check dimension of 'x'
    if x.ndim < 2:
        raise ValueError("'x' is required to have dimension > 1")

    # Get function
    func = this.get_attr(_NORM_PREFIX + name.lower())
    if not callable(func):
        raise ValueError(f"name '{str(name)}' is not supported")

    # Evaluate function
    supp_kwds = assess.get_function_kwds(func, default=kwds)
    return func(x, **supp_kwds) # pylint: disable=E1102

def norm_pq(x: NpArray,
        p: float = 2., q: float = 2., axes: IntTuple = (0, 1)) -> NpArray:
    """Calculate pq-norm of an array along given axes.

    The class of pq-norms generalizes the p-norms by a twice application in
    two dimensions [1]. Thereby a 'p-norm', which is parametrized by 'p', is
    applied to the columns of the matrix (more generally: the first axis index
    withon the parameter 'axes'). Afterwards a further 'p-norm', which is
    parametrized by 'q' is applied to the rows of the matrix (more generally:
    the second axis index within the parameter 'axes'). For the case that
    p = q = 2, the pq-norm is the Frobenius norm.

    Args:
        x: Any sequence that can be interpreted as a numpy ndarray of two or
            more dimensions. This includes nested lists, tuples, scalars and
            existing arrays.
        p: Positive real number, which determines the first p-norm by the p-th
            root of the summed p-th powered absolute values. For p < 1, the
            function does not satisfy the triangle inequality and yields a
            quasi-norm [2]. For p >= 1 the p-norm is a norm.
            Default: 2.
        q: Positive real number, which determines the second p-norm by the q-th
            root of the summed q-th powered absolute values. For q < 1, the
            function does not satisfy the triangle inequality and yields a
            quasi-norm [2]. For q >= 1 the p-norm is a norm.
            Default: 2.
        axes: Axes along which the norm is calculated. A two-dimensional
            array has two corresponding axes: The first running vertically
            downwards across rows (axis 0), and the second running horizontally
            across columns (axis 1).
            Default: (0, 1)

    Returns:
        NumPy ndarray of dimension <dim x> - <number of axes>.

    References:
        [1] https://en.wikipedia.org/wiki/matrix_norm#L2,1_and_Lp,q_norms
        [2] https://en.wikipedia.org/wiki/quasinorm

    """
    # Check type of 'axes'
    if not isinstance(axes, tuple):
        raise TypeError(
            "argument 'axes' is required to be of type 'tuple'"
            f", not '{type(axes)}'")

    # Check value of 'axes'
    if len(axes) != 2:
        raise np.AxisError(
            f"exactly two axes are required but {len(axes)} were given")
    if axes[0] == axes[1]:
        raise np.AxisError(
            "first and second axis have to be different")

    # For special cases prefer specific implementations for faster calculation
    if p == q == 2.: # Use the Frobenius norm
        return norm_frobenius(x, axes=axes)
    if p == q: # Use the p-norm in two dimensions
        return vector.norm_p(x, p=p, axis=axes)

    # If the first axis id is smaller then the second, then the second one
    # has to be corrected by the collapsed dimension of the first sum
    if axes[0] < axes[1]:
        axisp, axisq = axes[0], axes[1] - 1
    else:
        axisp, axisq = axes[0], axes[1]

    psum = np.sum(np.power(np.abs(x), p), axis=axisp)
    qsum = np.sum(np.power(psum, q / p), axis=axisq)
    return np.power(qsum, 1. / q)

def norm_frobenius(x: NpArray, axes: IntTuple = (0, 1)) -> NpArray:
    """Calculate Frobenius norm of an array along given axes.

    The Frobenius norm is the Euclidean norm on the space of (m, n) matrices.
    It equals the pq-norm for p = q = 2 and thus is calculated by the entrywise
    root sum of squared values [1]. From this it follows, that the Frobenius is
    sub-multiplicative.

    Args:
        x: Any sequence that can be interpreted as a numpy ndarray of two or
            more dimensions. This includes nested lists, tuples, scalars and
            existing arrays.
        axes: Axes along which the norm is calculated. A two-dimensional
            array has two corresponding axes: The first running vertically
            downwards across rows (axis 0), and the second running horizontally
            across columns (axis 1).
            Default: (0, 1)

    Returns:
        NumPy ndarray of dimension <dim x> - <number of axes>.

    References:
        [1] https://en.wikipedia.org/wiki/frobenius_norm

    """
    return vector.norm_euclid(x, axis=axes)

#
# Matrix Metrices
#

def metrices() -> StrList:
    """Get sorted list of matrix metrices.

    Returns:
        Sorted list of all matrix metrices, that are implemented within the
        module.

    """
    return this.crop_functions(prefix=_DIST_PREFIX)

def distance(
        x: NpArrayLike, y: NpArrayLike, metric: str = 'frobenius',
        **kwds: Any) -> NpArray:
    """Calculate matrix distances of two arrays along given axis.

    A matrix distance function, also known as metric, is a function d(x, y),
    which quantifies the proximity of matrices in a vector space as non-negative
    real numbers. If the distance is zero, then the matrices are equivalent with
    respect to the distance function [1]. Distance functions are often used as
    error, loss or risk functions, to evaluate statistical estimations [2].

    Args:
        x: Any sequence that can be interpreted as a numpy ndarray of two or
            more dimensions. This includes nested lists, tuples, scalars and
            existing arrays.
        y: Any sequence that can be interpreted as a numpy ndarray with the same
            dimension, shape and datatypes as 'x'.
        metric: Name of the matrix distance function. Accepted values are:
            'frobenius': Frobenius distance (induced by Frobenius norm)
            Default: 'frobenius'
        **kwds: Parameters of the given metric or class of metrices.
            The Parameters are documented within the respective 'dist'
            functions.

    Returns:
        NumPy ndarray of dimension <dim x> - <number of axes>.

    References:
        [1] https://en.wikipedia.org/wiki/metric_(mathematics)
        [2] https://en.wikipedia.org/wiki/loss_function

    """
    # Check 'x' and 'y' to be array-like
    try:
        x = np.array(x)
    except TypeError as err:
        raise TypeError(
            "first argument 'x' is required to be array-like") from err
    try:
        y = np.array(y)
    except TypeError as err:
        raise TypeError(
            "second argument 'y' is required to be array-like") from err

    # Check shapes and dtypes of 'x' and 'y'
    if x.shape != y.shape:
        raise ValueError(
            "arrays 'x' and 'y' can not be broadcasted together")

    # Get function
    func = this.get_attr(_DIST_PREFIX + metric.lower())
    if not callable(func):
        raise ValueError(f"name '{str(metric)}' is not supported")

    # Evaluate function
    supp_kwds = assess.get_function_kwds(func, default=kwds)
    return func(x, y, **supp_kwds) # pylint: disable=E1102

def dist_frobenius(x: NpArray, y: NpArray, axes: IntTuple = (0, 1)) -> NpArray:
    """Calculate Frobenius distances of two arrays along given axis.

    The Frobenius distance is induced by the Frobenius norm [1] and the natural
    distance in geometric interpretations.

    Args:
        x: Any sequence that can be interpreted as a numpy ndarray of two or
            more dimensions. This includes nested lists, tuples, scalars and
            existing arrays.
        y: Any sequence that can be interpreted as a numpy ndarray with the same
            dimension, shape and datatypes as 'x'.
        axes: Axes along which the norm is calculated. A two-dimensional
            array has two corresponding axes: The first running vertically
            downwards across rows (axis 0), and the second running horizontally
            across columns (axis 1).
            Default: (0, 1)

    Returns:
        NumPy ndarray of dimension dim *x* - 2.

    References:
        [1] https://en.wikipedia.org/wiki/frobenius_norm

    """
    return norm_frobenius(np.add(x, np.multiply(y, -1)), axes=axes)

#
# Matrix type transformation
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
            Default: `IEEE 754`_ floating point representation of NaN.

    Returns:
        NumPy ndarray of shape (*n*, *m*), where *n* equals the number of
        <*rows*> and *m* the number of <*columns*>.

    """
    # Check type of 'd'
    check.has_type("argument 'd'", d, dict)

    # Declare and initialize return value
    x: NpArray = np.empty(shape=(len(labels[0]), len(labels[1])))

    # Get NumPy ndarray
    setit = getattr(x, 'itemset')
    for i, row in enumerate(labels[0]):
        for j, col in enumerate(labels[1]):
            setit((i, j), d.get((row, col), nan))

    return x

def as_dict(
        x: NpArray, labels: StrListPair, nan: OptNumber = NaN) -> StrPairDict:
    """Convert two dimensional array to dictionary of pairs.

    Args:
        x: NumPy ndarray of shape (*n*, *m*), where *n* equals the number of
            <*rows*> and *m* the number of <*columns*>.
        labels: Tuple of format (<*rows*>, <*columns*>), where <*rows*> is a
            list of row labels, e.g. ['row1', 'row2', ...] and <*columns*> a
            list of column labels, e.g. ['col1', 'col2', ...].
        na: Optional value to mask Not a Number (NaN) entries. For cells in the
            array, which have this value, no entry in the returned dictionary
            is created. If nan is None, then for all numbers entries are
            created. Default: `IEEE 754`_ floating point representation of NaN.

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
