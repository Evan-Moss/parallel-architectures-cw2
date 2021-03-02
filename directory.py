from cache import CacheState


class Directory:
    # Class to represent the Directory, which keeps track of the cache lines in each processor.
    # The directory fetches from memory
    def __init__(self, no_cache_blocks, no_processors, stats):
        # Sets up the directory, each line holds the line state and the sharer vector.
        self.lines = [[CacheState.INVALID, [0 for i in range(no_processors)]] for x in range(no_cache_blocks)]
        self.stats = stats

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
        furthest = min([p for p in sharing_ps if p > p_num], default=-1)
        if furthest == -1:
            furthest = min(sharing_ps)
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

    def read_miss(self, index, p_num):
        # Asks the closest sharer to forward the cache line...
        self.stats.hop_between_processor_and_directory()

        # TODO: What if line state is Modified?

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

        elif line_state == CacheState.SHARED:
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

        elif line_state == CacheState.SHARED:
            # Need to invalidate all other copies.

            # If there are no sharers
            if sum(sharer_vector) == 1:
                # TODO: Check if this is always the case.
                # There are no sharers so you can just write
                self.stats.hop_between_processor_and_directory()
                return
            # Otherwise there are sharers.

            # Send invalidate to all sharers and send a reply to the requester telling it how many invalidate
            # acknowledgements to expect. If requester was in Invalid state, the data must ALSO be forwarded to the
            # requester

            # TODO: Differentiate between invalid state to receive data.

            # Invalidate other processors caches

            # This invalidation sends acknowledgement directly to the source processor (over the ring), and to the dir.

            return
