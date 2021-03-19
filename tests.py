from cache import Cache, CacheState, CacheLine
from stats import Stats
from directory import Directory


class TestClass:

    def setup(self):
        no_processors = 4
        block_size = 4
        no_cache_blocks = 512

        self.stats = Stats(verbose=True)
        self.directory = Directory(no_cache_blocks, no_processors, self.stats, verbose=True)

        # Set up processors
        self.caches = {}
        for p in range(no_processors):
            cache = Cache(p, block_size, no_cache_blocks, self.directory, self.stats, verbose=True)
            self.caches['P{}'.format(p)] = cache
            self.directory.connect_cache(cache)

    def test_b1(self):
        # P0 performs a Write, local state: M, no sharers
        self.setup()
        self.caches['P0'].write(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.MODIFIED

        self.stats.reset()
        self.caches['P0'].write(1)
        assert self.stats.cycles == 2

    def test_b2(self):
        # P0 performs a Read, local state: S, no sharers
        self.setup()
        self.caches['P0'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].read(1)
        assert self.stats.cycles == 2

    def test_b3(self):
        # P0 performs a Write, local state: I, no sharers
        self.setup()

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID

        self.stats.reset()

        self.caches['P0'].write(1)
        assert self.stats.cycles == 29

    def test_b4(self):
        # P0 performs a Read, local state: I, no sharers
        self.setup()

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID

        self.stats.reset()
        self.caches['P0'].read(1)
        assert self.stats.cycles == 29

    def test_b5(self):
        # P0 performs a Write, local state: S, no sharers
        self.setup()
        self.caches['P0'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].write(1)
        assert self.stats.cycles == 14

    def test_b6(self):
        # P0 performs a Write, local state: I, Remote cache-line at P1 in S state
        self.setup()
        self.caches['P1'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P1'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].write(1)
        assert self.stats.cycles == 25

    def test_b7(self):
        # P0 performs a Write, local state: I, Remote cache-line at P1, P3 in S state
        self.setup()
        self.caches['P1'].read(1)
        self.caches['P3'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P1'].cache_lines[0].state == CacheState.SHARED
        assert self.caches['P3'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].write(1)
        assert self.stats.cycles == 24

    def test_b8(self):
        # P0 performs a Write, local state: I, remote cache-line at P2 in M state
        self.setup()
        self.caches['P2'].write(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P2'].cache_lines[0].state == CacheState.MODIFIED

        self.stats.reset()
        self.caches['P0'].write(1)
        assert self.stats.cycles == 22

    def test_b9(self):
        # P0 performs a Read, local state: I, Remote cache-line at P1, P3 in S state
        self.setup()
        self.caches['P1'].read(1)
        self.caches['P3'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P1'].cache_lines[0].state == CacheState.SHARED
        assert self.caches['P3'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].read(1)
        assert self.stats.cycles == 19

    def test_b10(self):
        # P0 performs a Read, local state: I, Remote cache-line at P1 in S state
        self.setup()
        self.caches['P1'].read(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P1'].cache_lines[0].state == CacheState.SHARED

        self.stats.reset()
        self.caches['P0'].read(1)
        assert self.stats.cycles == 25

    def test_b11(self):
        # P0 performs a Read, local state: I, remote cache-line at P2 in M state
        self.setup()
        self.caches['P2'].write(1)

        assert self.caches['P0'].cache_lines[0].state == CacheState.INVALID
        assert self.caches['P2'].cache_lines[0].state == CacheState.MODIFIED

        self.stats.reset()
        self.caches['P0'].read(1)
        assert self.stats.cycles == 22

    def test_equals(self):
        a = CacheLine()
        a.state = CacheState.MODIFIED
        a.tag = 100

        b = CacheLine()
        b.state = CacheState.MODIFIED
        b.tag = 100

        assert(a.equals(b))

    def test_not_equals(self):
        a = CacheLine()
        a.state = CacheState.MODIFIED
        a.tag = 100

        b = CacheLine()
        b.state = CacheState.MODIFIED
        b.tag = 200

        assert(not a.equals(b))
