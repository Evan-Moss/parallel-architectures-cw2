from cache import Cache
from stats import Stats
from directory import Directory

no_processors = 4
block_size = 4
no_cache_blocks = 512

stats = Stats(verbose=True)
directory = Directory(no_cache_blocks, no_processors, stats)

# Set up processors
caches = {}
for p in range(no_processors):
    cache = Cache(p, block_size, no_cache_blocks, directory, stats)
    caches['P{}'.format(p)] = cache

# print(list(caches.keys())[(4+1 )% 4])

'''
caches['P1'].read(1)
stats.reset()

caches['P0'].write(1)
print(stats.cycles)
'''

# B6
caches['P1'].read(1)
stats.reset()
print('\n')
caches['P0'].write(1)
print(stats.cycles)

