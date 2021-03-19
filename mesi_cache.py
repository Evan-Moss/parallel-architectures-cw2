from cache import CacheLine, CacheState


class MESICache:
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
                st += 'Idx: {} {}\n'.format(i, l)
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
        self.cache_lines[index].state = CacheState.INVALID
        self.cache_lines[index].tag = None
        return

    def write(self, address):
        # If in E state can just change to M
        # if In M just write

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

        elif cache_line.state == CacheState.EXCLUSIVE and cache_line.tag == tag:
            # You can just write, state stays the same
            if self.verbose:
                print("Cache line is in E state and tags match, the cache is free to write. E->M Transition.")

            cache_line.state = CacheState.MODIFIED
            self.cache_lines[index] = cache_line

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
        return

    def read(self, address):
        # If in E or S or M can just read, don't change state.
        if self.verbose:
            print("P{} reading to word {}.".format(self.p_num, address))
        index, tag = self.calculate_cache_line(address)
        cache_line = self.cache_lines[index]

        # If in shared or modified or exclusive state, you can read freely.
        if (cache_line.state == CacheState.MODIFIED or cache_line.state == CacheState.SHARED
                or cache_line.state == CacheState.EXCLUSIVE) and cache_line.tag == tag:
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

    def write_miss(self,  index, tag, address):
        cache_line = self.cache_lines[index]

        # Contact the directory, we want to invalidate other copies if shared.
        self.directory.write_miss(index, tag, self.p_num)

        # Change state, will change to MODIFIED this is the same for either I or E.
        if self.verbose:
            print("Local cache line state becomes M.")
        cache_line.state = CacheState.MODIFIED
        cache_line.tag = tag

        self.cache_lines[index] = cache_line

        # Write to cache.
        self.write(address)

    def read_miss(self, index, tag, address):
        # State is invalid, contact the directory and check if anyone else has got it, if they do get it and go to
        # shared, if they don't fetch from memory and got to Exclusive state

        state = self.directory.read_miss(index, tag, self.p_num)

        # Change state, becomes SHARED or EXCLUSIVE.
        if self.verbose:
            print("Local cache line state becomes {}.".format(state))
        cache_line = self.cache_lines[index]
        cache_line.state = state
        cache_line.tag = tag

        self.cache_lines[index] = cache_line

        # Read from cache.
        self.read(address)
