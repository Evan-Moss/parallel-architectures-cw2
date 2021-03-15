from cache import CacheState
from stats import AccessType


class Directory:
    # Class to represent the Directory, which keeps track of the cache lines in each processor.
    # The directory fetches from memory
    def __init__(self, no_cache_blocks, no_processors, stats, verbose = False):
        # Sets up the directory, each line holds the line state and the sharer vector.
        self.lines = [[CacheState.INVALID, [0 for i in range(no_processors)]] for x in range(no_cache_blocks)]
        self.stats = stats
        self.connected_caches = []
        self.verbose = verbose

    def connect_cache(self, cache):
        self.connected_caches.append(cache)

    def closest_p(self, sharer_vector, p_num):
        # Finds the closest processor in the sharer_vector where the sharing bit is set to true. TODO: And not current p
        sharing_ps = [i for i, v in enumerate(sharer_vector) if v == 1 and i != p_num]
        closest = max([p for p in sharing_ps if p < p_num], default=-1)
        if closest == -1:
            closest = max(sharing_ps, default=-1)
        return closest

    def furthest_p(self, sharer_vector, p_num):
        # Finds the furthest processor in the sharer_vector where the sharing bit is set to true.
        sharing_ps = [i for i, v in enumerate(sharer_vector) if v == 1 and i != p_num]
        dist = 0
        furthest = -1
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
        self.stats.invalidations_sent += 1
        self.connected_caches[p].invalidate_line(index)

    def read_miss(self, index, tag, p_num):
        self.stats.access_type = AccessType.REMOTE
        self.stats.hop_between_processor_and_directory()

        line_state, sharer_vector = self.state_and_vector(index)
        if self.verbose:
            print("Line state: {}. Sharer vector: {}.".format(line_state, sharer_vector))
        if line_state == CacheState.SHARED or line_state == CacheState.MODIFIED:
            # Find closest P and ask it to send the data

            closest = self.closest_p(sharer_vector, p_num)
            if closest != -1:
                self.stats.hop_between_processor_and_directory()
                shared_processors = [i for i, v in enumerate(sharer_vector) if v == 1]

                # Closest processor probes and accesses its cache TO CHECK TAG
                closest_tag, closest_state = self.connected_caches[closest].calculate_cache_line(index)

            if closest == -1:
                if self.verbose:
                    print("No Sharers.")
                pass
            elif closest_tag != tag:
                # if in modified it will be written back in the cache class TODO: latency (?)
                if self.verbose:
                    print("Closest cache-line P{} tag doesn't match. "
                          "Must invalidate all other cache lines.".format(closest))
                for s in shared_processors:
                    self.invalidate_processor(s, index)
                    sharer_vector[s] = 0
                self.update_cache_line(index, CacheState.INVALID, sharer_vector)
            else:
                # Otherwise there is a sharer.
                # Send data, find distance between processors and hop between
                # Access cache to forward line
                self.stats.cache_access()
                distance = self.distance_between_processors(p_num, closest)
                for i in range(distance):
                    self.stats.hop_between_processors()

                # If modified, must become shared
                if line_state == CacheState.MODIFIED:
                    self.connected_caches[closest].cache_lines[index].state = CacheState.SHARED
                    self.stats.coherence_writebacks += 1
                    # TODO: is this coherence or replacement

                # Update sharer vector. Stays in shared state.
                sharer_vector[p_num] = 1
                self.update_cache_line(index, CacheState.SHARED, sharer_vector)
                return
        # Otherwise
        # There are no sharers, you must contact memory.
        if self.verbose:
            print("There are no sharers, must fetch the data from memory.")
        self.stats.memory_access_latency()
        self.stats.access_type = AccessType.OFF_CHIP

        # Update Directory state
        sharer_vector[p_num] = 1
        self.update_cache_line(index, CacheState.SHARED, sharer_vector)
        if self.verbose:
            print("Updated cache line has state {} and sharer vector {}.".format(CacheState.SHARED, sharer_vector))
        # Send back to processor
        self.stats.hop_between_processor_and_directory()
        return

    def write_miss(self, index, tag, p_num):
        # If P1 write miss: Send invalidates to all sharers, communicate the number of sharers to P1, sharers send
        # acknowledgements directly to P1. If P1 was in I state, the data must be forwarded by a sharer, or from memory
        # Once P1 has received all acknowledgements it can perform its write.
        self.stats.hop_between_processor_and_directory()

        self.stats.access_type = AccessType.REMOTE

        line_state, sharer_vector = self.state_and_vector(index)

        num_other_sharers = sum(sharer_vector) - (sharer_vector[p_num])

        forward = True

        if self.verbose:
            print("Line state: {}. Sharer vector: {}.".format(line_state, sharer_vector))

        if line_state == CacheState.SHARED or line_state == CacheState.MODIFIED:
            if self.verbose:
                print("Must invalidate all other sharers.")
            # Need to invalidate all other copies.

            closest = self.closest_p(sharer_vector, p_num)
            shared_processors = [i for i, v in enumerate(sharer_vector) if v == 1 and i != p_num]
            # If there are no sharers
            if num_other_sharers == 0:
                if self.verbose:
                    print("There are no sharers, cache is free to just write.")
                # There are no sharers so you can just write
                self.stats.hop_between_processor_and_directory()
                return
            # Closest processor probes and accesses its cache TO CHECK TAG
            self.stats.hop_between_processor_and_directory()
            closest_tag, closest_state = self.connected_caches[closest].calculate_cache_line(index)

            if closest_tag != tag:
                # if in modified it will be written back in the cache class TODO: latency (?)
                if self.verbose:
                    print("Tag of closest sharer doesn't match. Can't forward the data.")
                forward = False

            # Send message to invalidate the line (the invalidation requests overlap), if in invalid state, closest
            # also forwards the data
            local_state = CacheState.INVALID if sharer_vector[p_num] == 0 else CacheState.SHARED
            shared_processors = [i for i, v in enumerate(sharer_vector) if v == 1]
            closest_processor = self.closest_p(sharer_vector, p_num)
            furthest_processor = self.furthest_p(sharer_vector, p_num)

            # Send invalidate requests
            # These all overlap in time so we only need to calculate stats for 1 TODO: (?)
            for p in shared_processors:
                if p == closest_processor and local_state == CacheState.INVALID and forward is True:
                    # Also forward data, only measure latency if there is one sharer
                    if self.verbose:
                        print("Forward data from P{}.".format(closest_processor))
                    if num_other_sharers == 1:
                        self.stats.cache_access()
                self.invalidate_processor(p, index)

            # Send requesting processor how many acknowledgements to expect.
            # TODO: Does this have to be simulated?

            # Send acknowledgment from furthest processor.
            if self.verbose:
                print("Send acknowledgement from other sharers.".format(closest_processor))
            dist = self.distance_between_processors(p_num, furthest_processor)
            for i in range(dist):
                self.stats.hop_between_processors()
            # Now all processors have sent their acknowledgement, it can perform its write.

            # Update sharer vector and state
            for s in shared_processors:
                sharer_vector[s] = 0
            sharer_vector[p_num] = 1
            if self.verbose:
                print("Cache line state becomes {} and sharer vector is {}.".format(CacheState.MODIFIED, sharer_vector))
            self.update_cache_line(index, CacheState.MODIFIED, sharer_vector)

            return
        # Otherwise there are no sharers.
        if self.verbose:
            print("No sharers, must contact memory.")
        self.stats.memory_access_latency()
        self.stats.access_type = AccessType.OFF_CHIP

        # Update Directory state
        sharer_vector[p_num] = 1
        self.update_cache_line(index, CacheState.MODIFIED, sharer_vector)
        if self.verbose:
            print("Cache line state becomes {} and sharer vector is {}.".format(CacheState.MODIFIED, sharer_vector))

        # Send back to processor
        self.stats.hop_between_processor_and_directory()
        return
