class Stats:
    # Class to track the statistics of the cache simulator.
    def __init__(self, verbose=False):
        self.cycles = 0
        self.verbose = verbose

    def reset(self):
        self.cycles = 0

    def cache_probe(self):
        # Tag and state access.
        if self.verbose:
            print("Cache probe.")
        self.cycles += 1

    def cache_access(self):
        # Read or write.
        if self.verbose:
            print("Cache access.")
        self.cycles += 1

    def sram_access(self):
        if self.verbose:
            print("SRAM access.")
        self.cycles += 1

    def directory_access(self):
        if self.verbose:
            print("Directory access.")
        self.cycles += 1

    def hop_between_processors(self):
        if self.verbose:
            print("Hop between processors.")
        self.cycles += 3

    def hop_between_processor_and_directory(self):
        if self.verbose:
            print("Hop between processor and directory.")
        self.cycles += 5

    def memory_access_latency(self):
        if self.verbose:
            print("Access memory.")
        self.cycles += 15
