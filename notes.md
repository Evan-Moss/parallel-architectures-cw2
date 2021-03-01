# Notes for CW2

# Useful Resources

[Directory Protocol Video](https://www.youtube.com/watch?v=rTnp1PdTE4k&ab_channel=Prof.Dr.BenH.Juurlink)

[Understanding Direct Mapping](https://www.youtube.com/watch?v=pSarQQTJbDA&ab_channel=PacketPrep)

## MSI States

**Modified**: The data in the cache is then inconsistent with the backing store (e.g. memory). A cache with a block in the "M" state has the responsibility to write the block to the backing store when it is evicted

**Shared**: This block is unmodified and exists in read-only state in at least one cache. The cache can evict the data without writing it to the backing store.

**Invalid**: This block is either not present in the current cache or has been invalidated by a bus request, and must be fetched from memory or another cache if the block is to be stored in this cache.

### Simpler

**Invalid**: no node has copy.

**Shared**: 1 or more nodes have a copy.

**Modified**: 1 node has the copy, the memory copy is out of date.

Cache-line/block size is 4 words, 512 cache lines in the private cache of each processor. 

**Mapping**: Given address, how to find out whether in the cache and how to retrieve?

**Direct-mapped**: A way to find the block if it is in cache. 

**Write-back**: initially, writing is done only to the cache. The write to the backing store is postponed until the modified content is about to be replaced by another cache block.



Pretty sure that index is $\text{address}\mod{\text{# cache lines}}  $

