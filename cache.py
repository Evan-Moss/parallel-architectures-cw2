from stats import Stats
from enum import Enum
# -- Helper Functions


def calculate_cache_line(address):
    bin_address = '{0:032b}'.format(address)
    offset = int(bin_address[-2:],2)
    index = int(bin_address[-11:-2],2)
    tag = int(bin_address[:-11],2)

    return index, tag


# -- Classes


class CacheState(Enum):
    # Enumeration of MSI states to be used by each cache-line.
    MODIFIED = 0
    SHARED = 1
    INVALID = 2


class CacheLine:
    # Representation of a single CacheLine to be stored in cache of processor.
    def __init__(self):
        self.state = CacheState.INVALID
        self.tag = None

    def set_state(self, state):
        self.state = state

    def set_tag(self, tag):
        self.tag = tag


class Cache:
    # Representation of Cache.
    # Cache is direct-mapped with a write-back policy.
    def __init__(self, p_num, block_size, no_blocks, directory):
        self.p_num = p_num
        self.block_size = block_size
        self.no_blocks = no_blocks
        self.cache_lines = [CacheLine() for i in range(no_blocks)]
        self.directory = directory
        self.stats = Stats()

    def write(self, address):
        index, tag = calculate_cache_line(address)
        cache_line = self.cache_lines[index]
        # If in modified state, you can write freely
        if cache_line.state == CacheState.MODIFIED and cache_line.tag == tag:
            # You can just write, state stays the same
            print('Write Success. \tWord: {}, Line: {}, Tag: {}.'.format(address, index, tag))
        else:
            print('Write Miss. \tWord: {}, Line: {}, Tag: {}.'.format(address, index, tag))
            self.write_miss(index, tag)

    def read(self, address):
        index, tag = calculate_cache_line(address)
        cache_line = self.cache_lines[index]
        # If in shared or modified state, you can read freely
        if (cache_line.state == CacheState.MODIFIED or cache_line.state == CacheState.SHARED) and cache_line.tag == tag:
            # You can just read, state stays the same
            print('Read Success. \tWord: {}, Line: {}, Tag: {}.'.format(address, index, tag))
        else:
            print('Read Miss. \t\tWord: {}, Line: {}, Tag: {}.'.format(address, index, tag))
            self.read_miss(index, tag)

    def write_miss(self, index, tag):
        cache_line = self.cache_lines[index]

        if cache_line.state == CacheState.INVALID:

            # TODO: Request data from directory and invalidate other copies.
            #       Receive data from Directory.

            # Change state
            # Write data to cache
            cache_line.state = CacheState.MODIFIED
            cache_line.tag = tag

        if cache_line.state == CacheState.SHARED:
            # TODO: Request data from directory and invalidate other copies.
            #       Receive data from Directory. This might be able to be merged
            #       with above.

            # Change state
            # Write data to cache
            cache_line.state = CacheState.MODIFIED
            cache_line.tag = tag

    def read_miss(self, index, tag):
        # TODO: Request data from directory.
        #       Receive data.
        #       Change state.
        #       Read data from local cache.

        # Change state.
        cache_line = self.cache_lines[index]
        cache_line.set_state(CacheState.SHARED)
        cache_line.set_tag(tag)
