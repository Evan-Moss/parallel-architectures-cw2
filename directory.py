from cache import CacheState


class Directory:
    # Class to represent the Directory, which keeps track of the cache lines in each processor.
    # The directory fetches from memory
    def __init__(self, no_cache_blocks, no_processors, stats):
        # Sets up the directory, each line holds the line state and the sharer vector.
        self.lines = [[CacheState.INVALID, [0 for i in range(no_processors)]] for x in range(no_cache_blocks)]
        self.stats = stats
        self.connected_caches = []

    def connect_cache(self, cache):
        self.connected_caches.append(cache)

    def closest_p(self, sharer_vector, p_num):
        # Finds the closest processor in the sharer_vector where the sharing bit is set to true.
        sharing_ps = [i for i, v in enumerate(sharer_vector) if v == 1]
        closest = max([p for p in sharing_ps if p < p_num], default=-1)
        if closest == -1:
            closest = max(sharing_ps)
        return closest

    def furthest_p(self, sharer_vector, p_num):
        # Finds the furthest processor in the sharer_vector where the sharing bit is set to true.
        sharing_ps = [i for i, v in enumerate(sharer_vector) if v == 1]
        dist = 0
        furthest = p_num
        for p in sharing_ps:
            if self.distance_between_processors(p_num, p) > dist:
                dist = self.distance_between_processors(p_num, p)
                furthest = p

        return furthest

    def distance_between_processors(self, requester, forwarder):
        distance = (4 + (requester - forwarder)) % 4
        return distance

    def state_and_vector(self, index):
        self.stats.directory_access()
        line = self.lines[index]
        line_state = line[0]
        sharer_vector = line[1]
        return line_state, sharer_vector

    def update_cache_line(self, index, state, sharer_vector_state):
        self.lines[index][0] = state
        self.lines[index][1] = sharer_vector_state

    def invalidate_processor(self, p, index):
        self.connected_caches[p].invalidate_line(index)

    def read_miss(self, index, p_num):
        # Asks the closest sharer to forward the cache line...
        self.stats.hop_between_processor_and_directory()

        # TODO: What if line state is Modified? Will it ever be?

        line_state, sharer_vector = self.state_and_vector(index)

        if line_state == CacheState.INVALID:
            # Then there are no sharers, you must contact memory.
            self.stats.memory_access_latency()

            # Update Directory state
            sharer_vector[p_num] = 1
            self.update_cache_line(index, CacheState.SHARED, sharer_vector)

            # Send back to processor
            self.stats.hop_between_processor_and_directory()
            return

        elif line_state == CacheState.SHARED or line_state == CacheState.MODIFIED:
            # Find closest sharer and ask it to forward it to the processor.

            closest = self.closest_p(sharer_vector, p_num)

            # Ask closest to forward to processor.
            self.stats.hop_between_processor_and_directory()

            # Closest processor probes and accesses its cache
            self.stats.cache_probe()
            self.stats.cache_access()

            # Send data, find distance between processors and hop between
            distance = self.distance_between_processors(p_num, closest)
            for i in range(distance):
                self.stats.hop_between_processors()

            # Update sharer vector. Stays in shared state.
            sharer_vector[p_num] = 1
            self.update_cache_line(index, CacheState.SHARED, sharer_vector)

            return

    def write_miss(self, index, p_num):
        # If P1 write miss: Send invalidates to all sharers, communicate the number of sharers to P1, sharers send
        # acknowledgements directly to P1. If P1 was in I state, the data must be forwarded by a sharer, or from memory
        # Once P1 has received all acknowledgements it can perform its write.
        self.stats.hop_between_processor_and_directory()

        line_state, sharer_vector = self.state_and_vector(index)

        if line_state == CacheState.INVALID:
            # No sharers to invalidate, contact memory.
            self.stats.memory_access_latency()

            # Change directory line state to modified, and the sharer vector shows which processor has modified.
            sharer_vector[p_num] = 1
            self.update_cache_line(index, CacheState.MODIFIED, sharer_vector)

            # Send back to processor
            self.stats.hop_between_processor_and_directory()

            return

        elif line_state == CacheState.SHARED or line_state == CacheState.MODIFIED:
            # Need to invalidate all other copies.
            num_other_sharers = sum(sharer_vector) - (sharer_vector[p_num])
            # If there are no sharers
            if num_other_sharers == 0:
                # There are no sharers so you can just write
                self.stats.hop_between_processor_and_directory()
                return
            # Otherwise there are sharers.

            # Send message to invalidate the line (the invalidation requests overlap), if in invalid state, closest also
            # forwards the data
            local_state = CacheState.INVALID if sharer_vector[p_num] == 0 else CacheState.SHARED
            shared_processors = [i for i, v in enumerate(sharer_vector) if v == 1]
            closest_processor = self.closest_p(sharer_vector, p_num)
            furthest_processor = self.furthest_p(sharer_vector, p_num)

            # Send invalidate requests
            # These all overlap in time so we only need to calculate stats for 1 TODO: (?)

            self.stats.hop_between_processor_and_directory()
            self.stats.cache_probe()

            for p in shared_processors:
                self.invalidate_processor(p, index)
                if p == closest_processor and local_state == CacheState.INVALID and num_other_sharers == 1:
                    # Also forward data
                    self.stats.cache_access()
                    pass

            # Send requesting processor how many acknowledgements to expect.
            # TODO: Again, does this have to be simulated?

            # Send acknowledgment from furthest processor.
            dist = self.distance_between_processors(p_num, furthest_processor)
            for i in range(dist):
                self.stats.hop_between_processors()
            # Now all processors have sent their acknowledgement, it can perform its write.

            # Update sharer vector and state
            for s in shared_processors:
                sharer_vector[s] = 0
            sharer_vector[p_num] = 1
            self.update_cache_line(index, CacheState.MODIFIED, sharer_vector)

            return


