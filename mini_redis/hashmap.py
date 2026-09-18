"""Hash map with separate chaining.

Chain nodes are HashMap's own private implementation detail, not a
separate reusable list class -- HashMap is their only ever consumer, so
pointer manipulation (rehashing, unlinking) stays inside the class that
owns it instead of reaching into another class's internals.
"""

_INITIAL_CAPACITY = 8
_LOAD_FACTOR = 0.75


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next=None):
        self.key = key
        self.value = value
        self.next = next


class HashMap:
    def __init__(self, capacity=_INITIAL_CAPACITY):
        self._capacity = capacity
        self._size = 0
        self._buckets = [None] * capacity  # each slot: chain head _Node, or None

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
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                return idx, prev, node
            prev = node
            node = node.next
        return idx, None, None

    def _resize(self):
        # Capacity is always a power of two, so doubling it only ever adds
        # one bit to the index. Each old bucket's chain therefore splits
        # into exactly two new buckets -- same index (that bit is 0, "low")
        # or index + old_capacity (that bit is 1, "high") -- so nodes are
        # relinked into the new buckets in place instead of reallocated.
        old_buckets = self._buckets
        old_capacity = self._capacity
        self._capacity *= 2
        self._buckets = [None] * self._capacity

        for i, node in enumerate(old_buckets):
            low_head = low_tail = None
            high_head = high_tail = None
            while node is not None:
                next_node = node.next
                node.next = None
                if self._hash(node.key) & old_capacity == 0:
                    if low_tail is None:
                        low_head = node
                    else:
                        low_tail.next = node
                    low_tail = node
                else:
                    if high_tail is None:
                        high_head = node
                    else:
                        high_tail.next = node
                    high_tail = node
                node = next_node
            self._buckets[i] = low_head
            self._buckets[i + old_capacity] = high_head

    def put(self, key, value):
        idx, _, node = self._find_node(key)
        if node is not None:
            node.value = value
            return
        self._buckets[idx] = _Node(key, value, next=self._buckets[idx])
        self._size += 1
        if self._size / self._capacity > _LOAD_FACTOR:
            self._resize()

    def get(self, key):
        _, _, node = self._find_node(key)
        return node.value if node is not None else None

    def pop(self, key):
        idx, prev, node = self._find_node(key)
        if node is None:
            return None
        if prev is None:
            self._buckets[idx] = node.next
        else:
            prev.next = node.next
        self._size -= 1
        return node.value

    def remove(self, key):
        idx, prev, node = self._find_node(key)
        if node is None:
            return False
        if prev is None:
            self._buckets[idx] = node.next
        else:
            prev.next = node.next
        self._size -= 1
        return True

    def contains(self, key):
        _, _, node = self._find_node(key)
        return node is not None

    def keys(self):
        result = []
        for node in self._buckets:
            while node is not None:
                result.append(node.key)
                node = node.next
        return result

    def size(self):
        return self._size
