from cache import Cache
from directory import Directory

no_processors = 4
block_size = 4
no_cache_blocks = 512

directory = Directory()

# Set up processors
caches = {}
for p in range(no_processors):
    cache = Cache(p, block_size, no_cache_blocks, directory)
    caches['P{}'.format(p)] = cache

# print(list(caches.keys())[(4+1 )% 4])

caches['P1'].read(1)
caches['P1'].read(1)
caches['P1'].write(1)
caches['P1'].write(1)
