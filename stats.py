from enum import Enum
from os import path


class AccessType(Enum):
    # Enumeration of different access types

    def __str__(self):
        return self.name

    PRIVATE = 0
    REMOTE = 1
    OFF_CHIP = 2


class Stats:
    # Class to track the statistics of the cache simulator.
    def __init__(self, verbose=False):
        self.cycles = 0
        self.verbose = verbose
        self.cycle_dict = {AccessType.PRIVATE: [],
                           AccessType.REMOTE: [],
                           AccessType.OFF_CHIP: []}
        self.invalidations_sent = 0
        self.replacement_writebacks = 0
        self.coherence_writebacks = 0
        self.access_type = AccessType.PRIVATE

    def hit_rate(self):
        return len(self.cycle_dict[AccessType.PRIVATE]) / len(self.cycle_dict[AccessType.PRIVATE] +
                                                              self.cycle_dict[AccessType.REMOTE] +
                                                              self.cycle_dict[AccessType.OFF_CHIP])

    def reset(self):
        self.cycles = 0
        self.access_type = AccessType.PRIVATE
        if self.verbose:
            print("\n")

    def save_stats(self):
        self.cycle_dict[self.access_type].append(self.cycles)

    def cache_probe(self):
        # Tag and state access.
        if self.verbose:
            print("Cache probe. (1)")
        self.cycles += 1

    def cache_access(self):
        # Read or write.
        if self.verbose:
            print("Cache access. (1)")
        self.cycles += 1

    def sram_access(self):
        if self.verbose:
            print("SRAM access. (1)")
        self.cycles += 1

    def directory_access(self):
        if self.verbose:
            print("Directory access. (1)")
        self.cycles += 1

    def hop_between_processors(self):
        if self.verbose:
            print("Hop between processors. (3)")
        self.cycles += 3

    def hop_between_processor_and_directory(self):
        if self.verbose:
            print("Hop between processor and directory. (5)")
        self.cycles += 5

    def memory_access_latency(self):
        if self.verbose:
            print("Access memory. (15)")
        self.cycles += 15

    def final_stats(self, filename, to_file=False):
        private_accesses = len(self.cycle_dict.get(AccessType.PRIVATE))
        remote_accesses = len(self.cycle_dict[AccessType.REMOTE])
        off_chip_accesses = len(self.cycle_dict[AccessType.OFF_CHIP])
        total_accesses = private_accesses + remote_accesses + off_chip_accesses
        replacement_writebacks = self.replacement_writebacks
        coherence_writebacks = self.coherence_writebacks
        invalidations_sent = self.invalidations_sent
        private_access_latency = (sum(self.cycle_dict[AccessType.PRIVATE]) / private_accesses) if private_accesses > 0 else 0
        remote_access_latency = (sum(self.cycle_dict[AccessType.REMOTE]) / remote_accesses) if remote_accesses > 0 else 0
        off_chip_access_latency = (sum(self.cycle_dict[AccessType.OFF_CHIP]) / off_chip_accesses) if off_chip_accesses > 0 else 0
        total_latency = sum(self.cycle_dict[AccessType.PRIVATE]) + sum(self.cycle_dict[AccessType.REMOTE]) + \
                        sum(self.cycle_dict[AccessType.OFF_CHIP])
        average_latency = total_latency / total_accesses

        st = "Private-accesses: {}\nRemote-accesses: {}\nOff-chip-accesses: {}\nTotal-accesses: {}" \
               "\nReplacement-writebacks: {}\nCoherence-writebacks: {}\nInvalidations-sent: {}\nAverage-latency: {}" \
               "\nPriv-average-latency: {}\nRem-average-latency: {}\nOff-chip-average-latency: {}" \
               "\nTotal-latency: {}".format(private_accesses, remote_accesses, off_chip_accesses, total_accesses,
                                            replacement_writebacks, coherence_writebacks, invalidations_sent,
                                            average_latency, private_access_latency, remote_access_latency,
                                            off_chip_access_latency, total_latency)

        if to_file:
            outname = 'out_{}'.format(filename)
            outpath = path.join('./out_files', outname)
            with open(outpath, 'w') as f:
                f.write(st)
            print("File {} written with these stats:\n".format(outpath))
        return st