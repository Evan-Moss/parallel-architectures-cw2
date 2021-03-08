from enum import Enum


class CacheState(Enum):
    # Enumeration of MSI states to be used by each cache-line.

    def __str__(self):
        return self.name[0]

    MODIFIED = 0
    SHARED = 1
    INVALID = 2


class CacheLine:
    # Representation of a single CacheLine to be stored in cache of processor.
    def __init__(self):
        self.state = CacheState.INVALID
        self.tag = None

    def __str__(self):
        return '{} {}'.format(self.tag, self.state)

    def set_state(self, state):
        self.state = state

    def set_tag(self, tag):
        self.tag = tag


class Cache:
    # Representation of Cache.
    # Cache is direct-mapped with a write-back policy.
    def __init__(self, p_num, block_size, no_blocks, directory, stats):
        self.p_num = p_num
        self.block_size = block_size
        self.no_blocks = no_blocks
        self.cache_lines = [CacheLine() for i in range(no_blocks)]
        self.directory = directory
        self.stats = stats
        self.verbose = False

    def __str__(self):
        st = ""
        for i,l in enumerate(self.cache_lines):
            if l.state != CacheState.INVALID:
                st += '{} {}\n'.format(i, l)
        return st

    def calculate_cache_line(self, address):
        # This is a cache probe, I.e finding the state and the tag.
        bin_address = '{0:032b}'.format(address)
        # TODO: This should be changed so it works for any size
        offset = int(bin_address[-2:], 2)
        index = int(bin_address[-11:-2], 2)
        tag = int(bin_address[:-11], 2)
        self.stats.cache_probe()
        return index, tag

    def invalidate_line(self, index):
        # print("Invalidating line {} in processor {}".format(index, self.p_num))
        self.cache_lines[index].state = CacheState.INVALID
        self.cache_lines[index].tag = None
        return

    def write(self, address):
        index, tag = self.calculate_cache_line(address)
        cache_line = self.cache_lines[index]
        # If in modified state, you can write freely
        if cache_line.state == CacheState.MODIFIED and cache_line.tag == tag:
            # You can just write, state stays the same
            self.stats.cache_access()
        else:
            # If State is INVALID or if state is SHARED
            self.write_miss(index, tag, address)

    def read(self, address):
        index, tag = self.calculate_cache_line(address)
        cache_line = self.cache_lines[index]

        # If in shared or modified state, you can read freely
        if (cache_line.state == CacheState.MODIFIED or cache_line.state == CacheState.SHARED) and cache_line.tag == tag:
            # You can just read, state stays the same
            self.stats.cache_access()
        else:
            self.read_miss(index, tag, address)

    def write_miss(self, index, tag, address):
        cache_line = self.cache_lines[index]

        # Contact the directory, we want to invalidate other copies if shared.
        self.directory.write_miss(index, self.p_num)

        # Change state, will change to MODIFIED.
        cache_line.state = CacheState.MODIFIED
        cache_line.tag = tag

        # Write to cache.
        self.write(address)

    def read_miss(self, index, tag, address):
        # Contact the directory to receive the data, the cycles taken are calculated and added to the stats
        # in the directory class.
        self.directory.read_miss(index, self.p_num)

        # Change state, always becomes SHARED.
        cache_line = self.cache_lines[index]
        cache_line.set_state(CacheState.SHARED)
        cache_line.set_tag(tag)

        # Read from cache.
        self.read(address)
