class Stats:
    # Class to track the statistics of the cache simulator.
    def __init__(self):
        self.cycles = 0

    def cache_probe(self):
        self.cycles += 1

    def cache_access(self):
        self.cycles += 1

    def sram_access(self):
        self.cycles += 1

    def directory_access(self):
        self.cycles += 1

    def hop_between_processors(self):
        self.cycles += 3

    def hop_between_processor_and_directory(self):
        self.cycles += 5

    def memory_access_latency(self):
        self.cycles += 15
