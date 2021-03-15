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

    def reset(self):
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
    def __init__(self, p_num, block_size, no_blocks, directory, stats, verbose=False):
        self.p_num = p_num
        self.block_size = block_size
        self.no_blocks = no_blocks
        self.cache_lines = [CacheLine() for i in range(no_blocks)]
        self.directory = directory
        self.stats = stats
        self.verbose = verbose

    def __str__(self):
        st = ""
        for i, l in enumerate(self.cache_lines):
            if l.state != CacheState.INVALID:
                st += '{} {}\n'.format(i, l)
        return st

    def get_cache_line(self, index):
        self.stats.cache_probe()
        return self.cache_lines[index].tag, self.cache_lines[index].state

    def calculate_cache_line(self, address):
        # This is a cache probe, I.e finding the state and the tag.
        bin_address = '{0:032b}'.format(address)
        # TODO: This should be changed so it works for any size
        offset = int(bin_address[-2:], 2)
        index = int(bin_address[-11:-2], 2)
        tag = int(bin_address[:-11], 2)
        self.stats.cache_probe()
        if self.verbose:
            print("P{}. Index: {}. Tag: {}. Local State: {}.".format(self.p_num, index, tag, self.cache_lines[index].state))
        return index, tag

    def invalidate_line(self, index):
        # print("Invalidating line {} in processor {}".format(index, self.p_num))
        if self.cache_lines[index].state == CacheState.MODIFIED:
            self.stats.coherence_writebacks += 1
            if self.verbose:
                print("COHERENCE WRITE-BACK: Cache line was in M state, and has been invalidated.")
            # TODO: Is the coherence or replacement
        self.cache_lines[index].state = CacheState.INVALID
        self.cache_lines[index].tag = None
        return

    def write(self, address):
        if self.verbose:
            print("P{} write to word {}.".format(self.p_num, address))
        index, tag = self.calculate_cache_line(address)
        cache_line = self.cache_lines[index]
        # If in modified state, you can write freely
        if cache_line.state == CacheState.MODIFIED and cache_line.tag == tag:
            # You can just write, state stays the same
            if self.verbose:
                print("Cache line is in M state and tags match, the cache is free to write.")
            self.stats.cache_access()
            return

        # Replace if tag miss and modified
        if cache_line.tag != tag and cache_line.state == CacheState.MODIFIED:
            # Must write back to memory
            if self.verbose:
                print("REPLACEMENT WRITE-BACK: Tag miss and cache state was M, and is therefore being replaced.")
            self.stats.replacement_writebacks += 1

        # If State is INVALID or if state is SHARED or is a tag miss
        if self.verbose:
            print("Write miss! Must contact the directory.")
        self.write_miss(index, tag, address)

    def read(self, address):
        if self.verbose:
            print("P{} reading to word {}.".format(self.p_num, address))
        index, tag = self.calculate_cache_line(address)
        cache_line = self.cache_lines[index]

        # If in shared or modified state, you can read freely TODO: (?)
        if (cache_line.state == CacheState.MODIFIED or cache_line.state == CacheState.SHARED) and cache_line.tag == tag:
            if self.verbose:
                print("Cache state is {}, cache is free to read.".format(cache_line.state))
            # You can just read, state stays the same
            self.stats.cache_access()
            return

        if cache_line.tag != tag:
            # Tag miss on any state
            if cache_line.state == CacheState.MODIFIED:
                # Must write back to memory
                if self.verbose:
                    print("REPLACEMENT WRITE-BACK: Tag miss and cache state was M, and is therefore being replaced.")
                self.stats.replacement_writebacks += 1

            # If state is shared, we don't need to write-back we can just write over

            # self.cache_lines[index].state = CacheState.INVALID
            # Now the state is invalid and tag remains the same

        # If State is INVALID or (State is SHARED AND tag miss)
        if self.verbose:
            print("Read miss! Must contact the directory.")
        self.read_miss(index, tag, address)

    def write_miss(self, index, tag, address):
        cache_line = self.cache_lines[index]

        # Contact the directory, we want to invalidate other copies if shared.
        self.directory.write_miss(index, tag, self.p_num)

        # Change state, will change to MODIFIED.
        if self.verbose:
            print("Local cache line state becomes M.")
        cache_line.state = CacheState.MODIFIED
        cache_line.tag = tag

        # Write to cache.
        self.write(address)

    def read_miss(self, index, tag, address):
        # Contact the directory to receive the data, the cycles taken are calculated and added to the stats
        # in the directory class.
        self.directory.read_miss(index, tag, self.p_num)

        # Change state, becomes SHARED.
        if self.verbose:
            print("Local cache line state become S.")
        cache_line = self.cache_lines[index]
        cache_line.set_state(CacheState.SHARED)
        cache_line.set_tag(tag)

        # Read from cache.
        self.read(address)
