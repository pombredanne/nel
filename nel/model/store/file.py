import mmap
import cPickle as pickle
import operator
from functools32 import lru_cache

class mmdict(object):
    def __init__(self, path):
        self.path = path
        self.index = {}
        
        index_path = self.path + '.index'
        log.debug('Loading mmap store: %s ...' % index_path)
        with open(index_path, 'rb') as f:
            while True:
                try:
                    key, offset = self.deserialise(f)
                    self.index[key] = offset
                except EOFError: break

        self.data_file = open(path + '.data', 'rb')
        self.data_mmap = mmap.mmap(self.data_file.fileno(), 0, prot=mmap.PROT_READ)

    @staticmethod
    def serialise(obj, f):
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def deserialise(f):
        return pickle.load(f)

    @staticmethod
    def static_itervalues(path):
        with open(path + '.data', 'rb') as f:
            while True:
                try:
                    yield mmdict.deserialise(f)
                except EOFError: break

    def iteritems(self):
        sorted_idx = sorted(self.index.iteritems(), key=operator.itemgetter(1))

        for i, v in enumerate(self.itervalues()):
            yield (sorted_idx[i][0], v)

    def iterkeys(self):
        return self.index.iterkeys()

    def itervalues(self):
        self.data_mmap.seek(0)
        while True:
            try:
                yield self.deserialise(self.data_mmap)
            except EOFError: break

    def __len__(self):
        return len(self.index)

    def __contains__(self, key):
        return key in self.index

    @lru_cache(maxsize=20000)
    def __getitem__(self, key):
        if key not in self:
            return None

        self.data_mmap.seek(self.index[key])
        return self.deserialise(self.data_mmap)

    def __enter__(self):
        return self

    def close(self):
        if hasattr(self, 'data_mmap') and self.data_mmap != None:
            self.data_mmap.close()
        if hasattr(self, 'data_file') and self.data_file != None:
            self.data_file.close()

    def __exit__(self, type, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    @staticmethod
    def write(path, iter_kvs):
        with open(path + '.index','wb') as f_index, open(path + '.data', 'wb') as f_data:
            for key, value in iter_kvs:
                mmdict.serialise((key,f_data.tell()), f_index)
                mmdict.serialise(value, f_data)
