# -*- coding: utf-8 -*-
"""Types."""
from __future__ import annotations

__author__ = 'Patrick Michl'
__email__ = 'frootlab@gmail.com'
__license__ = 'GPLv3'
__docformat__ = 'google'

import array
import collections
import datetime
import io
import os
import types
from typing import Any, Callable, ClassVar, ContextManager, Dict, Hashable, IO
from typing import Iterable, Iterator, List, Optional, Sequence, Set, Tuple
from typing import Type, TypeVar, Union, NamedTuple, Container, Sized

################################################################################
# Static Functions
################################################################################

void: Callable[..., None] = lambda *args, **kwds: None

################################################################################
# Numerical Constants
################################################################################

NaN = float('nan')
Infty = float('inf')

################################################################################
# Classes and ClassInfos
################################################################################

Array = array.ArrayType
OrderedDict = collections.OrderedDict
Date = datetime.datetime
Function = types.FunctionType
Method = types.MethodType
CallableClasses = (Function, Method)
Module = types.ModuleType
Traceback = types.TracebackType
Path = os.PathLike
PathLikeClasses = (str, Path)
BytesIOBaseClass = io.BufferedIOBase
TextIOBaseClass = io.TextIOBase
FileClasses = (BytesIOBaseClass, TextIOBaseClass)
TextFileClasses = (str, Path, TextIOBaseClass)
ClassInfoClasses = (type, tuple)

################################################################################
# Generic Type Variables
################################################################################

# Generic Type-Variables
S = TypeVar('S')
T = TypeVar('T')

################################################################################
# Types for Literals and Collections of Literals
################################################################################

# Unions of Literals
OptType = Optional[type]
OptStr = Optional[str]
OptInt = Optional[int]
OptFloat = Optional[float]
OptComplex = Optional[complex]
OptBool = Optional[bool]
OptBytes = Optional[bytes]
OptArray = Optional[Array]
StrOrBool = Union[str, bool]
OptStrOrBool = Optional[StrOrBool]
StrOrInt = Union[str, int]
BytesLike = Union[bytes, bytearray, memoryview]
BytesLikeOrStr = Union[BytesLike, str]

# Collections of Literals
# TODO (patrick.michl@gmail.com): Hashable currently does not completely
# work in mypi. When it works, the HashableDict shall replace AnyDict:
# AnyDict = Dict[Hashable, Any]
HashDict = Dict[Hashable, Any]
AnyDict = Dict[Any, Any]
StrSet = Set[str]
StrPair = Tuple[str, str]
StrTuple = Tuple[str, ...]
StrList = List[str]
StrDict = Dict[str, Any]
IntSet = Set[int]
IntPair = Tuple[int, int]
IntTuple = Tuple[int, ...]
IntList = List[int]
IntDict = Dict[int, Any]
FloatPair = Tuple[float, float]

# Unions of Collections of Literals
StrOrDict = Union[str, AnyDict]
StrOrType = Union[type, str]
OptSet = Optional[Set[Any]]
OptPair = Optional[Tuple[Any, Any]]
OptTuple = Optional[Tuple[Any, ...]]
OptList = Optional[List[Any]]
OptDict = Optional[Dict[Any, Any]]
OptStrDict = Optional[StrDict]
OptStrList = Optional[StrList]
OptStrTuple = Optional[StrTuple]
OptStrOrDict = Optional[StrOrDict]
OptIntList = Optional[IntList]
OptIntTuple = Optional[IntTuple]

# Compounds of Literals and Collections of Literals
StrPairDict = Dict[StrPair, Any]
StrListPair = Tuple[StrList, StrList]
StrTupleDict = Dict[Union[str, Tuple[str, ...]], Any]
RecDict = Dict[Any, StrDict]
DictOfRecDicts = Dict[Any, RecDict]

# Nested Types
# TODO (patrick.michl@gmail.com): currently recursive type definition is not
# fully supported by the typing module. When recursive type definition is
# available replace the following lines by their respective recursive
# definitions
AnyDict2 = Dict[Any, AnyDict]
AnyDict3 = Dict[Any, AnyDict2]
NestDict = Union[AnyDict, AnyDict2, AnyDict3]
#NestDict = Dict[Any, Union[Any, 'NestDict']]
NestRecDict = Union[StrDict, RecDict, DictOfRecDicts]
# NestStrDict = Dict[Str, Union[StrDict, 'NestStrDict']]
OptNestDict = Optional[NestDict]
IterNestRecDict = Iterable[NestRecDict]

################################################################################
# Define Types for Callables and Collections of Callables
################################################################################

# Elementary Callables
AnyFunc = Callable[..., Any]
VoidFunc = Callable[..., None]
BoolFunc = Callable[..., bool]
UnaryFunc = Callable[[Any], Any]
BinaryFunc = Callable[[Any, Any], Any]
TernaryFunc = Callable[[Any, Any, Any], Any]
TestFunc = Callable[[Any, Any], bool]

# Unions of Callables and Literals
OptVoidFunc = Optional[VoidFunc]
OptCallable = Optional[AnyFunc]
OptFunction = Optional[Function]
OptModule = Optional[Module]

# Collections of Callables
StrDictOfFuncs = Dict[str, AnyFunc]
StrDictOfTestFuncs = Dict[str, TestFunc]

# Unions of Collections of Callables and Literals
OptStrDictOfFuncs = Optional[StrDictOfFuncs]
OptStrDictOfTestFuncs = Optional[StrDictOfTestFuncs]

# Compounds of Collables and Literals
FuncWrapper = Callable[[Callable[..., T]], Callable[..., T]]

################################################################################
# Specific builtin Types
################################################################################

# Numbers
RealNumber = Union[int, float]
Number = Union[RealNumber, complex]
OptNumber = Optional[Number]
RealVector = Sequence[RealNumber]
Vector = Sequence[Number]
RealFunc = Callable[..., RealNumber]
ScalarFunc = Callable[..., Number]
VectorFunc = Callable[..., Vector]

# Classes and Class Variables
Class = Type[Any]
OptClass = Optional[Class]
ClassInfo = Union[Class, Tuple[Class, ...]]
OptClassInfo = Optional[ClassInfo]
ClassStrList = ClassVar[StrList]
ClassDict = ClassVar[AnyDict]
ClassStrDict = ClassVar[StrDict]

################################################################################
# Specific Types that are defined by standard library packages
################################################################################

# Named Tuples
OptNamedTuple = Optional[NamedTuple]

# Dynamic Typed (Duck Typed) Classes
IterAny = Iterator[Any] # methods: __next__
IterNone = Iterator[None] # methods: __next__
OptContainer = Optional[Container] # methods: __contains__
OptSized = Optional[Sized] # methods: __len__

################################################################################
# Specific Types that are used within standard library packages
################################################################################

# PathLike type
OptPath = Optional[Path]
PathList = List[Path]
StrDictOfPaths = Dict[str, Path]
PathLike = Union[str, Path]
PathLikeList = List[PathLike]
OptPathLike = Optional[PathLike]
# Nested paths for tree structured path references
# TODO (patrick.michl@gmail.com): currently (Python 3.7.1) recursive type
# definition is not fully supported by the typing module. When recursive type
# definition is available replace the following lines by their respective
# recursive definitions
PathLikeSeq = Sequence[PathLike]
PathLikeSeq2 = Sequence[Union[PathLike, PathLikeSeq]]
PathLikeSeq3 = Sequence[Union[PathLike, PathLikeSeq, PathLikeSeq2]]
NestPath = Union[PathLike, PathLikeSeq, PathLikeSeq2, PathLikeSeq3]
#NestPath = Sequence[Union[str, Path, 'NestPath']]
NestPathDict = Dict[str, NestPath]
OptNestPathDict = Optional[NestPathDict]

# Exceptions
Exc = BaseException
ExcType = Type[Exc]
ExcInfo = Union[ExcType, Tuple[ExcType, ...]]

# BytesIO Like
BytesIOLike = IO[bytes]
IterBytesIOLike = Iterator[BytesIOLike]
CManBytesIOLike = ContextManager[BytesIOLike]

# StringIO Like
StringIOLike = IO[str]
IterStringIOLike = Iterator[StringIOLike]
CManStringIOLike = ContextManager[StringIOLike]

# FileLike
FileLike = Union[BytesIOLike, StringIOLike]
IterFileLike = Iterator[FileLike]
CManFileLike = ContextManager[FileLike]

# FileOrPathLike
FileOrPathLike = Union[FileLike, PathLike]

################################################################################
# Specific Types that are used within external Packages
################################################################################

# Numpy
# TODO (patrick.michl@gmail.com): Currently (numpy 1.15.3) typing support for
# numpy is not available but a workaround is in progress, see:
# https://github.com/numpy/numpy-stubs
NpShape = Optional[IntTuple]
NpShapeLike = Optional[Union[int, Sequence[int]]]
NpAxes = Union[None, int, IntTuple]
NpFields = Union[None, str, Iterable[str]]
NpArray = Any # TODO: Replace with numpy.ndarray, when supported
NpMatrix = Any # TODO: replace with numpy.matrix, when supported
NpRecArray = Any # TODO: replace with numpy.recarray, when supported
NpDtype = Any # TODO: replace with numpy.dtype, when supported
NpArraySeq = Sequence[NpArray]
NpMatrixSeq = Sequence[NpMatrix]
NpArrayLike = Union[Number, NpArray, NpArraySeq, NpMatrix, NpMatrixSeq]
OptNpRecArray = Optional[NpRecArray]
OptNpArray = Optional[NpArray]
NpArrayFunc = Callable[..., NpArray]
NpRecArrayFunc = Callable[..., NpRecArray]
NpMatrixFunc = Callable[..., NpMatrix]
# TODO (patrick.michl@gmail.com): Currently (Python 3.7.1) the typing module
# does not support argument specification for callables with variing numbers of
# arguments, but this feature is in progress, see:
# https://github.com/python/typing/issues/264
# Use argument specification, when available:
# FuncOfNpArray = Callable[[NpArray, ...], Any]
# NpArrayFuncOfNpArray = Callable[[NpArray, ...], NpArray]

# NetworkX