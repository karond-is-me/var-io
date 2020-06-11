TEXT_TYPES = (str,)
INT_TYPES = (int,)
from itertools import islice
import inspect
import sys
import re
import datetime
NUMERIC_TYPES = tuple(list(INT_TYPES) + [float, complex])

#==============================================================================
# FakeObject
#==============================================================================
class FakeObject(object):
    """Fake class used in replacement of missing modules"""
    pass


#==============================================================================
# Numpy arrays and numeric types support
#==============================================================================
try:
    from numpy import (ndarray, array, matrix, recarray,
                       int64, int32, int16, int8, uint64, uint32, uint16, uint8,
                       float64, float32, float16, complex64, complex128, bool_)
    from numpy.ma import MaskedArray
    from numpy import savetxt as np_savetxt
    from numpy import get_printoptions, set_printoptions
except:
    ndarray = array = matrix = recarray = MaskedArray = np_savetxt = \
     int64 = int32 = int16 = int8 = uint64 = uint32 = uint16 = uint8 = \
     float64 = float32 = float16 = complex64 = complex128 = bool_ = FakeObject


def get_numpy_dtype(obj):
    """Return NumPy data type associated to obj
    Return None if NumPy is not available
    or if obj is not a NumPy array or scalar"""
    if ndarray is not FakeObject:
        # NumPy is available
        import numpy as np
        if isinstance(obj, np.generic) or isinstance(obj, np.ndarray):
        # Numpy scalars all inherit from np.generic.
        # Numpy arrays all inherit from np.ndarray.
        # If we check that we are certain we have one of these
        # types then we are less likely to generate an exception below.
            try:
                return obj.dtype.type
            except (AttributeError, RuntimeError):
                #  AttributeError: some NumPy objects have no dtype attribute
                #  RuntimeError: happens with NetCDF objects (Issue 998)
                return


#==============================================================================
# Pandas support
#==============================================================================
try:
    from pandas import DataFrame, Index, Series
except:
    DataFrame = Index = Series = FakeObject


#==============================================================================
# PIL Images support
#==============================================================================
try:
    from spyder import pil_patch
    Image = pil_patch.Image.Image
except:
    Image = FakeObject  # analysis:ignore


#==============================================================================
# BeautifulSoup support (see Issue 2448)
#==============================================================================
try:
    import bs4
    NavigableString = bs4.element.NavigableString
except:
    NavigableString = FakeObject  # analysis:ignore


#==============================================================================
# Misc.
#==============================================================================
def address(obj):
    """Return object address as a string: '<classname @ address>'"""
    return "<%s @ %s>" % (obj.__class__.__name__,
                          hex(id(obj)).upper().replace('X', 'x'))




def get_supported_types():
    """
    Return a dictionnary containing types lists supported by the
    namespace browser.

    Note:
    If you update this list, don't forget to update variablexplorer.rst

    in spyder-docs
    """
    from datetime import date, timedelta
    editable_types = [int, float, complex, list, set, dict, tuple, date,
                      timedelta] + list(TEXT_TYPES) + list(INT_TYPES)
    try:
        from numpy import ndarray, matrix, generic
        editable_types += [ndarray, matrix, generic]
    except:
        pass
    try:
        from pandas import DataFrame, Series, Index
        editable_types += [DataFrame, Series, Index]
    except:
        pass
    picklable_types = editable_types[:]
    try:
        from spyder.pil_patch import Image
        editable_types.append(Image.Image)
    except:
        pass
    return dict(picklable=picklable_types, editable=editable_types)

# =============================================================================
# Types
# =============================================================================
def to_text_string(obj, encoding=None):
    """Convert `obj` to (unicode) text string"""

    # Python 3
    if encoding is None:
        return str(obj)
    elif isinstance(obj, str):
        # In case this function is not used properly, this could happen
        return obj
    else:
        return str(obj, encoding)


def get_type_string(item):
    """Return type string of an object."""
    if isinstance(item, DataFrame):
        return "DataFrame"
    if isinstance(item, Index):
        return type(item).__name__
    if isinstance(item, Series):
        return "Series"

    found = re.findall(r"<(?:type|class) '(\S*)'>",
                       to_text_string(type(item)))
    if found:
        if found[0] == 'type':
            return 'class'
        return found[0]
    else:
        return None



#==============================================================================
# Globals filter: filter namespace dictionaries (to be edited in
# CollectionsEditor)
#==============================================================================
def is_supported(value, check_all=False, filters=None, iterate=False):
    """Return True if value is supported, False otherwise."""
    assert filters is not None
    if value is None:
        return True
    if is_callable_or_module(value):
        return True
    elif not isinstance(value, filters):
        return False
    elif iterate:
        if isinstance(value, (list, tuple, set)):
            valid_count = 0
            for val in value:
                if is_supported(val, filters=filters, iterate=check_all):
                    valid_count += 1
                if not check_all:
                    break
            return valid_count > 0
        elif isinstance(value, dict):
            for key, val in list(value.items()):
                if not is_supported(key, filters=filters, iterate=check_all) \
                   or not is_supported(val, filters=filters,
                                       iterate=check_all):
                    return False
                if not check_all:
                    break
    return True

def strict__supported(value, check_all=False, filters=None, iterate=False):
    """Return True if value is supported, False otherwise."""
    assert filters is not None
    if value is None:
        return False
    if is_callable_or_module(value):
        return False
    elif not isinstance(value, filters):
        return False
    elif iterate:
        if isinstance(value, (list, tuple, set)):
            valid_count = 0
            for val in value:
                if is_supported(val, filters=filters, iterate=check_all):
                    valid_count += 1
                if not check_all:
                    break
            return valid_count > 0
        elif isinstance(value, dict):
            for key, val in list(value.items()):
                if not is_supported(key, filters=filters, iterate=check_all) \
                   or not is_supported(val, filters=filters,
                                       iterate=check_all):
                    return False
                if not check_all:
                    break
    return True


def is_callable_or_module(value):
    """Return True if value is a callable or module, False otherwise."""
    try:
        callable_or_module = callable(value) or inspect.ismodule(value)
    except Exception:
        callable_or_module = False
    return callable_or_module

import inspect

def varname(p):
	for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
		m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
	if m:
		return m.group(1)


def get_size(item):
    """Return size of an item of arbitrary type"""
    if isinstance(item, (list, set, tuple, dict)):
        return len(item)
    elif isinstance(item, (ndarray, MaskedArray)):
        return item.shape
    elif isinstance(item, Image):
        return item.size
    if isinstance(item, (DataFrame, Index, Series)):
        try:
            return item.shape
        except RecursionError:
            # This is necessary to avoid an error when trying to
            # get the shape of these objects.
            # Fixes spyder-ide/spyder-kernels#217
            return (-1, -1)
    else:
        return 1

def memory_usage(item):
    return sys.getsizeof(item)



supported_types = get_supported_types()
filters=tuple(supported_types['picklable'])
def get_var_inf(item,strict):
    var_inf = {}
    if strict == False:
        var_inf['is_supported'] = is_supported(item,filters = filters,iterate=True)
    else:
        var_inf['is_supported'] = strict__supported(item,filters = filters,iterate=True)
    if var_inf['is_supported'] == True:
        var_inf['type'] = get_type_string(item)
        var_inf['size'] = get_size(item)
        var_inf['memory usage'] = memory_usage(item)
    else:
        var_inf['type'] = None
        var_inf['size'] = get_size(item)
        var_inf['memory usage'] = memory_usage(item)
    return var_inf



