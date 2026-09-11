"""Hash map with separate chaining, built on top of DoublyLinkedList buckets."""

from .dllist import DoublyLinkedList

_INITIAL_CAPACITY = 8
_LOAD_FACTOR = 0.75


class HashMap:
    def __init__(self, capacity=_INITIAL_CAPACITY):
        self._capacity = capacity
        self._size = 0
        self._buckets = [DoublyLinkedList() for _ in range(capacity)]

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
        node = self._buckets[idx].head
        while node is not None:
            if node.data[0] == key:
                return idx, node
            node = node.next
        return idx, None

    def _resize(self):
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [DoublyLinkedList() for _ in range(self._capacity)]
        for bucket in old_buckets:
            for key, value in bucket:
                idx = self._bucket_index(key)
                self._buckets[idx].insert_back((key, value))

    def put(self, key, value):
        idx, node = self._find_node(key)
        if node is not None:
            node.data = (key, value)
            return
        self._buckets[idx].insert_back((key, value))
        self._size += 1
        if self._size / self._capacity > _LOAD_FACTOR:
            self._resize()

    def get(self, key):
        _, node = self._find_node(key)
        return node.data[1] if node is not None else None

    def pop(self, key):
        idx, node = self._find_node(key)
        if node is None:
            return None
        value = node.data[1]
        self._buckets[idx].remove_node(node)
        self._size -= 1
        return value

    def remove(self, key):
        idx, node = self._find_node(key)
        if node is None:
            return False
        self._buckets[idx].remove_node(node)
        self._size -= 1
        return True

    def contains(self, key):
        _, node = self._find_node(key)
        return node is not None

    def keys(self):
        result = []
        for bucket in self._buckets:
            for key, _ in bucket:
                result.append(key)
        return result

    def size(self):
        return self._size
