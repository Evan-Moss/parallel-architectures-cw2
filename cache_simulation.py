from cache import Cache
from stats import Stats
from directory import Directory
from mesi_directory import MESIDirectory
from mesi_cache import MESICache
from os import path
import sys


def parse_line(l):
    # P3 R 12611
    l = l.split()

    if len(l) == 1:
        # Output command, either v, p, h
        if l[0] not in ['v','p','h']:
            raise Exception('Trace argument \'{}\' is not accepted. Must be \'v\', \'p\', or \'h\''.format(l[0]))
        return -1, l[0], -1

    return l[0], l[1], int(l[2])


def print_caches(cs):
    # print('Idx, Tag, State')
    for k, c in cs.items():
        print('----{0}----\n'.format(k))
        print(c)
    print('==========\n')


class Simulator:
    def __init__(self, no_processors=4, block_size=4, no_cache_blocks=512, optimisation=False):
        self.optimisation = optimisation
        self.no_processors = no_processors
        self.block_size = block_size
        self.no_cache_blocks = no_cache_blocks
        self.stats = Stats()
        if self.optimisation:
            self.directory = MESIDirectory(self.no_cache_blocks, self.no_processors, self.stats)
        else:
            self.directory = Directory(self.no_cache_blocks, self.no_processors, self.stats)
        self.caches = {}
        self.setup_caches()

    def setup_caches(self):
        for p in range(self.no_processors):
            if self.optimisation:
                cache = MESICache(p, self.block_size, self.no_cache_blocks, self.directory, self.stats)
            else:
                cache = Cache(p, self.block_size, self.no_cache_blocks, self.directory, self.stats)
            self.caches['P{}'.format(p)] = cache
            self.directory.connect_cache(cache)

    def run_simulation(self, file):
        pth = path.join('./cache-traces', file)
        with open(pth, 'r') as f:
            for line in f:
                p, action, mem = parse_line(line)
                if action == 'R':
                    self.caches[p].read(mem)
                elif action == 'W':
                    self.caches[p].write(mem)
                elif action == 'v':
                    # Full line by line explanation should be toggled
                    self.stats.verbose = not self.stats.verbose
                    self.directory.verbose = not self.directory.verbose
                    for k, c in self.caches.items():
                        c.verbose = not c.verbose
                elif action == 'p':
                    # Complete content of cache should be output in some suitable format
                    print("\nCACHE TABLES:\n")
                    print_caches(self.caches)
                elif action == 'h':
                    print("HIT RATE: {}".format(self.stats.hit_rate()))
                else:
                    raise Exception('Invalid line in trace file.')
                if action in ['R', 'W']:
                    self.stats.save_stats()
                    self.stats.reset()

        print(self.stats.final_stats(file, to_file=True))


if __name__ == "__main__":
    args = sys.argv[1:]

    optimisation = False

    if len(args) < 1:
        print("You must input a file name for the trace as the first argument.")
        exit(1)
    elif len(args) == 1 and args[0].strip('-') == 'h':
        print("./run_script.sh <FILENAME> <Optimisation Toggle>(optional)")
        print("Use the filename placed in the 'cache-traces' directory that you would like to run, then use ONLY the "
              "filename as the first argument. Optionally, you can enable the optimisation by passing 'o' as the second"
              " argument.")
    elif len(args) == 2:
        if args[1] is not None and args[1].strip("\'-") == 'o':
            optimisation = True
        else:
            print("If you would like to enable the optimisation, pass 'o' as the second argument.")
            exit(1)
    elif len(args) > 2:
        print("Too many arguments.")
        exit(1)

    file = args[0]

    cache_type = Cache
    dir_type = Directory

    s = Simulator(optimisation=optimisation)
    s.run_simulation(file)
