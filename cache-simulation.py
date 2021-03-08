from cache import Cache
from stats import Stats
from directory import Directory
from os import path


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
    for k, c in cs.items():
        print('----{0}----\n'.format(k))
        print(c)

no_processors = 4
block_size = 4
no_cache_blocks = 512

stats = Stats()
directory = Directory(no_cache_blocks, no_processors, stats)

# Set up processors
caches = {}
for p in range(no_processors):
    cache = Cache(p, block_size, no_cache_blocks, directory, stats)
    caches['P{}'.format(p)] = cache
    directory.connect_cache(cache)

file = path.join('./cache-traces', 'trace-1.txt')

with open(file) as f:
    for line in f:
        p, action, mem = parse_line(line)
        if action == 'R':
            caches[p].read(mem)
        elif action == 'W':
            caches[p].write(mem)
        elif action == 'v':
            # Full line by line explanation should be toggled
            pass
        elif action == 'p':
            # Complete content of cache should be output in some suitable format
            print_caches(caches)
        elif action == 'h':
            # Hit-rate achieved so far should be output
            pass
        else:
            raise Exception('Invalid line in trace file.')


