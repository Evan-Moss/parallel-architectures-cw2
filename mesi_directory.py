from cache import CacheState, CacheLine
from stats import AccessType


class MESIDirectory:
    def __init__(self, no_cache_blocks, no_processors, stats, verbose=False):
        # Sets up the directory, each line holds the line state and the sharer vector.
        self.lines = [[CacheLine() for i in range(no_processors)] for x in range(no_cache_blocks)]
        self.stats = stats
        self.connected_caches = []
        self.verbose = verbose

    def connect_cache(self, cache):
        self.connected_caches.append(cache)

    def closest_sharer(self, sharers, p_num):
        # Finds the closest processor in the sharer_vector where the sharing bit is set to true. TODO: And not current p
        dists = []
        for s in sharers:
            dists.append(self.distance_between_processors(p_num, s))

        return sharers[min(range(len(dists)), key=lambda x: dists[x])]

    def furthest_sharer(self, sharers, p_num):
        # Finds the furthest processor in the sharer_vector where the sharing bit is set to true.
        dists = []
        for s in sharers:
            dists.append(self.distance_between_processors(p_num, s))

        return sharers[max(range(len(dists)), key=lambda x: dists[x])]

    def print_lines(self, index):
        print("Lines {}".format(['P{}: {}'.format(i, str(l)) for i, l in enumerate(self.lines[index]) if l.tag is not None]))

    def distance_between_processors(self, requester, forwarder):
        distance = (4 + (requester - forwarder)) % 4
        return distance

    def cache_lines_from_index(self, index):
        self.stats.directory_access()
        return self.lines[index]

    def get_sharers(self, lines, tag, p_num):
        sharers = []
        for i, line in enumerate(lines):
            if line.tag == tag and i != p_num:
                sharers.append(i)
        return sharers

    def update_cache_lines(self, index, lines):
        self.lines[index] == lines

    def invalidate_processor(self, p, index):
        self.stats.invalidations_sent += 1
        self.connected_caches[p].invalidate_line(index)

    def read_miss(self, index, tag, p_num):
        self.stats.access_type = AccessType.REMOTE
        self.stats.hop_between_processor_and_directory()

        update_state = CacheState.SHARED

        lines = self.cache_lines_from_index(index)
        if self.verbose:
            self.print_lines(index)

        sharers = self.get_sharers(lines, tag, p_num)

        # Their are either 1-3 sharers in S or one in M, either way we just want to forward from closest sharer
        if len(sharers) > 0:

            if self.verbose:
                print("Sharers: {}.".format(sharers))

            closest = self.closest_sharer(sharers, p_num)

            if self.verbose:
                print("Closest sharer at P{}.".format(closest))

            # Send message to closest sharer to send data
            if self.verbose:
                print("Send message to closest sharer to forward the data.")

            self.stats.hop_between_processor_and_directory()

            # Access cache to forward line
            if self.verbose:
                print("Closest sharer accesses data to send.")

            self.stats.cache_probe()
            self.stats.cache_access()

            distance = self.distance_between_processors(p_num, closest)
            for i in range(distance):
                self.stats.hop_between_processors()

            if lines[closest].state == CacheState.MODIFIED:
                # Must become shared, causes a coherence write-back
                if self.verbose:
                    print("COHERENCE WRITE-BACK: Cache line was in M state, and has been changed to S state.")
                self.connected_caches[closest].cache_lines[index].state = CacheState.SHARED
                self.stats.coherence_writebacks += 1

                # Update directory lines for sharer
                lines[closest] = CacheLine(CacheState.SHARED, tag)
            elif lines[closest].state == CacheState.EXCLUSIVE:
                # Change to S state, this does not require a write-back as it was clean.
                self.connected_caches[closest].cache_lines[index].state = CacheState.SHARED
                if self.verbose:
                    print("Shared cache line was in E state, and has been changed to S state.")

                # Change sharer vector to shared
                lines[closest].state = CacheState.SHARED

        elif len(sharers) == 0:
            if self.verbose:
                print("There are no sharers, must fetch the data from memory.")
            self.stats.memory_access_latency()
            self.stats.access_type = AccessType.OFF_CHIP
            self.stats.hop_between_processor_and_directory()
            update_state = CacheState.EXCLUSIVE

        # Update directory line
        lines[p_num] = CacheLine(update_state, tag)

        if self.verbose:
            self.print_lines(index)

        self.update_cache_lines(index, lines)
        return update_state

    def write_miss(self, index, tag, p_num):
        self.stats.access_type = AccessType.REMOTE
        self.stats.hop_between_processor_and_directory()

        lines = self.cache_lines_from_index(index)
        local_state = lines[p_num].state
        local_tag = lines[p_num].tag

        sharers = self.get_sharers(lines, tag, p_num)

        if self.verbose:
            self.print_lines(index)

        if len(sharers) > 0:
            # There are sharers in either S or M, they must all be invalidated
            # Access cache to forward line

            if self.verbose:
                print("Sharers: {}.".format(sharers))

            closest = self.closest_sharer(sharers, p_num)
            furthest = self.furthest_sharer(sharers, p_num)

            if self.verbose:
                print("Closest sharer at P{}.".format(closest))

            # Send message to closest sharer to invalidate the line (and forward the data)
            if self.verbose:
                print("Send message to closest sharer to invalidate the data.")
            self.stats.hop_between_processor_and_directory()
            self.stats.cache_probe()
            #self.stats.cache_access()

            for s in sharers:
                # TODO: Change to local
                self.invalidate_processor(s, index)
                if s == closest and local_state == CacheState.INVALID:
                    if self.verbose:
                        print("Forward data from P{} since local state was I.".format(s))
                    if len(sharers) == 1:
                        self.stats.cache_access()

            # Send requester how many acknowledgements to expect. Currently not simulated.
            if self.verbose:
                print("Send P{} how many acknowledgements to expect.".format(p_num))

            if self.verbose:
                print("Send acknowledgement from other sharers.")

            dist = self.distance_between_processors(p_num, furthest)

            for i in range(dist):
                self.stats.hop_between_processors()

        elif len(sharers) == 0 and local_state == CacheState.SHARED and local_tag == tag:
            # There are no sharers, you can just write
            if self.verbose:
                print("There are no sharers, cache is free to just write.")
            self.stats.hop_between_processor_and_directory()

        else:
            # This is if there were no sharers in the first place, and the cache line was invalid
            if self.verbose:
                print("No sharers, must contact memory.")
            self.stats.memory_access_latency()
            self.stats.access_type = AccessType.OFF_CHIP
            self.stats.hop_between_processor_and_directory()

        # Update directory sharers
        lines[p_num] = CacheLine(CacheState.MODIFIED, tag)

        for s in sharers:
            lines[s] = CacheLine(CacheState.INVALID, None)
        if self.verbose:
            self.print_lines(index)

        self.update_cache_lines(index, lines)
        return
