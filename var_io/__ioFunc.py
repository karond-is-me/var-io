import sys
import os
import os.path as osp
import tarfile
import tempfile
import shutil
import types
import warnings
import json
import inspect
import dis
import copy
import glob
import os
import pickle


try:
    import pandas as pd
except:
    pd = None            #analysis:ignore

try:
    import numpy as np  # analysis:ignore

    def load_array(filename):
        try:
            name = osp.splitext(osp.basename(filename))[0]
            data = np.load(filename)
            if hasattr(data, 'keys'):
                return data, None
            else:
                return {name: data}, None
        except Exception as error:
            return None, str(error)

    def __save_array(data, basename, index):
        """Save numpy array"""
        fname = basename + '_%04d.npy' % index
        np.save(fname, data)
        return fname
except:
    load_array = None




def save_dictionary(data, filename):
    """Save dictionary in a single file .spydata file"""
    filename = osp.abspath(filename)
    old_cwd = os.getcwd()
    os.chdir(osp.dirname(filename))
    error_message = None
    skipped_keys = []
    data_copy = {}

    try:
        # Copy dictionary before modifying it to fix #6689
        for obj_name, obj_value in data.items():
            # Skip modules, since they can't be pickled, users virtually never
            # would want them to be and so they don't show up in the skip list.
            # Skip callables, since they are only pickled by reference and thus
            # must already be present in the user's environment anyway.
            if not (callable(obj_value) or isinstance(obj_value,
                                                      types.ModuleType)):
                # If an object cannot be deepcopied, then it cannot be pickled.
                # Ergo, we skip it and list it later.
                try:
                    data_copy[obj_name] = copy.deepcopy(obj_value)
                except Exception:
                    skipped_keys.append(obj_name)
        data = data_copy
        if not data:
            raise RuntimeError('No supported objects to save')

        saved_arrays = {}
        if load_array is not None:
            # Saving numpy arrays with np.save
            arr_fname = osp.splitext(filename)[0]
            for name in list(data.keys()):
                try:
                    if isinstance(data[name],
                                  np.ndarray) and data[name].size > 0:
                        # Save arrays at data root
                        fname = __save_array(data[name], arr_fname,
                                             len(saved_arrays))
                        saved_arrays[(name, None)] = osp.basename(fname)
                        data.pop(name)
                    elif isinstance(data[name], (list, dict)):
                        # Save arrays nested in lists or dictionaries
                        if isinstance(data[name], list):
                            iterator = enumerate(data[name])
                        else:
                            iterator = iter(list(data[name].items()))
                        to_remove = []
                        for index, value in iterator:
                            if isinstance(value,
                                          np.ndarray) and value.size > 0:
                                fname = __save_array(value, arr_fname,
                                                     len(saved_arrays))
                                saved_arrays[(name, index)] = (
                                    osp.basename(fname))
                                to_remove.append(index)
                        for index in sorted(to_remove, reverse=True):
                            data[name].pop(index)
                except (RuntimeError, pickle.PicklingError, TypeError,
                        AttributeError, IndexError):
                    # If an array can't be saved with numpy for some reason,
                    # leave the object intact and try to save it normally.
                    pass
            if saved_arrays:
                data['__saved_arrays__'] = saved_arrays

        pickle_filename = osp.splitext(filename)[0] + '.pickle'
        # Attempt to pickle everything.
        # If pickling fails, iterate through to eliminate problem objs & retry.
        with open(pickle_filename, 'w+b') as fdesc:
            try:
                pickle.dump(data, fdesc, protocol=2)
            except (pickle.PicklingError, AttributeError, TypeError,
                    ImportError, IndexError, RuntimeError):
                data_filtered = {}
                for obj_name, obj_value in data.items():
                    try:
                        pickle.dumps(obj_value, protocol=2)
                    except Exception:
                        skipped_keys.append(obj_name)
                    else:
                        data_filtered[obj_name] = obj_value
                if not data_filtered:
                    raise RuntimeError('No supported objects to save')
                pickle.dump(data_filtered, fdesc, protocol=2)

        # Use PAX (POSIX.1-2001) format instead of default GNU.
        # This improves interoperability and UTF-8/long variable name support.
        with tarfile.open(filename, "w", format=tarfile.PAX_FORMAT) as tar:
            for fname in ([pickle_filename]
                          + [fn for fn in list(saved_arrays.values())]):
                tar.add(osp.basename(fname))
                os.remove(fname)
    except (RuntimeError, pickle.PicklingError, TypeError) as error:
        error_message = error
    else:
        if skipped_keys:
            skipped_keys.sort()
            error_message = ('Some objects could not be saved: '
                             + ', '.join(skipped_keys))
    finally:
        os.chdir(old_cwd)
    return error_message


def load_dictionary(filename):
    """Load dictionary from .spydata file"""
    filename = osp.abspath(filename)
    old_cwd = os.getcwd()
    tmp_folder = tempfile.mkdtemp()
    os.chdir(tmp_folder)
    data = None
    error_message = None
    try:
        with tarfile.open(filename, "r") as tar:
            tar.extractall()
        pickle_filename = glob.glob('*.pickle')[0]
        # 'New' format (Spyder >=2.2 for Python 2 and Python 3)
        with open(pickle_filename, 'rb') as fdesc:
            data = pickle.loads(fdesc.read())
        saved_arrays = {}
        if load_array is not None:
            # Loading numpy arrays saved with np.save
            try:
                saved_arrays = data.pop('__saved_arrays__')
                for (name, index), fname in list(saved_arrays.items()):
                    arr = np.load( osp.join(tmp_folder, fname) )
                    if index is None:
                        data[name] = arr
                    elif isinstance(data[name], dict):
                        data[name][index] = arr
                    else:
                        data[name].insert(index, arr)
            except KeyError:
                pass
    # Except AttributeError from e.g. trying to load function no longer present
    except (AttributeError, EOFError, ValueError) as error:
        error_message = error
    # To ensure working dir gets changed back and temp dir wiped no matter what
    finally:
        os.chdir(old_cwd)
        try:
            shutil.rmtree(tmp_folder)
        except OSError as error:
            error_message = error
    return data, error_message

if __name__ == '__main__':
    import pandas as pd
    import numpy as np
    # a = pd.Series([1,2,3,4])  
    # b = np.array([2,3,4,5]) 
    # c = 'dsjfkewrnj'
    # data = {'a':a,'b':b,'c':c}
    # save_dictionary(data,'./haha.ipynbdata')
    data = load_dictionary('./haha.ipynbdata')
    print(data)