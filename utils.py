import json
import yaml
import numpy as np


class ConfigDict(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """
    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(ConfigDict, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(ConfigDict, self).__delitem__(key)
        del self.__dict__[key]

def JsonifyResult(result):
    for k,v in result.items():
        if isinstance(v,dict):
            result[k]=JsonifyResult(v)
        elif isinstance(v,np.ndarray):
            result[k]=v.tolist()
        elif isinstance(v,list):
            ll=[]
            for value in v:
                if isinstance(value,dict):
                    ll.append(JsonifyResult(value))
                else:
                    ll.append(value)
            result[k]=ll
        else:
            result[k]=v
    return result

def read_config(filename):
    configs=yaml.safe_load(open(filename))
    return ConfigDict(configs)

