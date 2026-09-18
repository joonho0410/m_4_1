"""Hash map with separate chaining, built on top of SinglyLinkedList buckets."""

from .sllist import SinglyLinkedList

_INITIAL_CAPACITY = 8
_LOAD_FACTOR = 0.75


class HashMap:
    def __init__(self, capacity=_INITIAL_CAPACITY):
        self._capacity = capacity
        self._size = 0
        self._buckets = [SinglyLinkedList() for _ in range(capacity)]

    def _hash(self, key):
        # djb2: cheap to compute and spreads short ASCII keys (typical Redis
        # keys) well enough to keep chains short.
        h = 5381
        for ch in key:
            h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
        return h

    def _bucket_index(self, key):
        return self._hash(key) % self._capacity

    def _find_node(self, key):
        idx = self._bucket_index(key)
        prev = None
        node = self._buckets[idx].head
        while node is not None:
            if node.data[0] == key:
                return idx, prev, node
            prev = node
            node = node.next
        return idx, None, None

    def _resize(self):
        # Capacity is always a power of two, so doubling it only ever adds
        # one bit to the index. Each old bucket's chain therefore splits
        # into exactly two new buckets -- same index (that bit is 0, "low")
        # or index + old_capacity (that bit is 1, "high") -- so nodes can be
        # relinked into the new buckets in place instead of reallocated.
        old_buckets = self._buckets
        old_capacity = self._capacity
        self._capacity *= 2
        self._buckets = [SinglyLinkedList() for _ in range(self._capacity)]
        for i, bucket in enumerate(old_buckets):
            node = bucket.head
            while node is not None:
                next_node = node.next
                if self._hash(node.data[0]) & old_capacity == 0:
                    self._buckets[i].append_node(node)
                else:
                    self._buckets[i + old_capacity].append_node(node)
                node = next_node

    def put(self, key, value):
        idx, _, node = self._find_node(key)
        if node is not None:
            node.data = (key, value)
            return
        self._buckets[idx].insert_back((key, value))
        self._size += 1
        if self._size / self._capacity > _LOAD_FACTOR:
            self._resize()

    def get(self, key):
        _, _, node = self._find_node(key)
        return node.data[1] if node is not None else None

    def pop(self, key):
        idx, prev, node = self._find_node(key)
        if node is None:
            return None
        value = node.data[1]
        self._buckets[idx].remove_after(prev, node)
        self._size -= 1
        return value

    def remove(self, key):
        idx, prev, node = self._find_node(key)
        if node is None:
            return False
        self._buckets[idx].remove_after(prev, node)
        self._size -= 1
        return True

    def contains(self, key):
        _, _, node = self._find_node(key)
        return node is not None

    def keys(self):
        result = []
        for bucket in self._buckets:
            for key, _ in bucket:
                result.append(key)
        return result

    def size(self):
        return self._size
