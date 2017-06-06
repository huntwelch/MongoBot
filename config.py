import yaml
import sys
import copy

from os import path, listdir
from collections import OrderedDict, Sequence, Mapping

class Config(yaml.Loader):

    eidetic = dict()

    def __init__(self, stream):
        self._root = path.split(stream.name)[0]
        super(Config, self).__init__(stream)


    def include(self, node):
        """Include a YAML file within another YAML file"""

        filepath = path.join(self._root, self.construct_scalar(node))
        if path.isdir(filepath):
            for filename in listdir(filepath):
                if path.isfile(filename):
                    return self.load(filename)
        else:
            return self.load(filepath)


    def sequence(self, node):
        return YamlList(self.construct_object(child) for child in node.value)

    def mapping(self, node):
        make_obj = self.construct_object

        return YamlDict((make_obj(k), make_obj(v)) for k, v in node.value)

    def load(self, path):
        if path not in self.eidetic:
            with open(path, 'r') as filestream:
                self.eidetic.update({ path: yaml.load(filestream, Config) })

        return self.eidetic.get(path, dict())


class YamlDict(OrderedDict):

    def __init__(self, *args, **kwargs):
        super(YamlDict, self).__init__(*args, **kwargs)
        self.__root = self


    def __getattr__(self, key):
        if key in self:
            return self[key]

        return super(YamlDict, self).__getattribute__(key)


    def __getitem__(self, key):
        v = super(YamlDict, self).__getitem__(key)

        if isinstance(v, basestring):
            v = v.format(**self.__root)

        return v


    def __setitem__(self, key, value):

        if isinstance(value, Mapping) and not isinstance(value, YamlDict):
            value = YamlDict(value)
        elif isinstance(value, basestring):
            pass
        elif isinstance(value, Sequence) and not isinstance(value, YamlList):
            value = YamlList(value)

        super(YamlDict, self).__setitem__(key, value)

    def copy(self):
        return copy.deepcopy(self)

    def setAsRoot(self, root=None):
        if root is None:
            root = self

        self.__root = root

        for k, v in self.iteritems():
            if hasattr(v, 'setAsRoot'):
                v.setAsRoot(root)


class YamlList(list):

    ROOT_NAME = 'root'

    def __init__(self, *args, **kwargs):
        super(YamlList, self).__init__(*args, **kwargs)
        self.__root = {YamlList.ROOT_NAME: self}


    def __getitem__(self, key):
        v = super(YamlList, self).__getitem__(key)
        if isinstance(v, basestring):
            v = v.format(**self.__root)

        return v

    def __setitem__(self, key, value):

        if isinstance(value, Mapping) and not isinstance(value, YamlDict):
            value = YamlDict(value)
        elif isinstance(value, Sequence) and not isinstance(value, YamlList):
            value = YamlList(value)

        super(YamlList, self).__setitem__(key, value)

    def copy(self, *args):
        return copy.deepcopy(self)

    def setAsRoot(self, root=None):
        if root is None:
            root = {YamlList.ROOT_NAME: self}

        self.__root = root

        for v in self:
            if hasattr(v, 'setAsRoot'):
                v.setAsRoot(root)


def load_config(config_file):
    try:
        stream = file(config_file, 'r')
        data = yaml.load(stream, Config)

        if data is not None:
            data.setAsRoot()

        return data

    except Exception as e:
        pass

Config.add_constructor('!include', Config.include)
Config.add_constructor(u'tag:yaml.org,2002:seq', Config.sequence)
Config.add_constructor(u'tag:yaml.org,2002:map', Config.mapping)
