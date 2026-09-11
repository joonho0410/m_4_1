"""Mini Redis storage engine: string commands, TTL, and memory-bounded LRU eviction."""

import math
import time

from .dllist import DoublyLinkedList
from .hashmap import HashMap
from .heap import MinHeap


def _byte_len(s):
    return len(s.encode("utf-8"))


class Entry:
    __slots__ = ("value", "expire_at", "lru_node")

    def __init__(self, value, expire_at=None, lru_node=None):
        self.value = value
        self.expire_at = expire_at
        self.lru_node = lru_node


class OOMError(Exception):
    """Raised when a single key+value alone would exceed maxmemory."""


class Store:
    def __init__(self):
        self.data = HashMap()
        self.lru_list = DoublyLinkedList()  # head = most recently used
        self.ttl_heap = MinHeap()
        self.maxmemory = 0  # 0 = unlimited
        self.used_memory = 0
        self.evicted_keys = 0

    # -- internal helpers -------------------------------------------------

    def _now(self):
        return time.time()

    def _is_live(self, entry, now):
        return entry.expire_at is None or entry.expire_at > now

    def _delete_key(self, key, count_evicted=False):
        entry = self.data.pop(key)
        if entry is None:
            return False
        self.used_memory -= _byte_len(key) + _byte_len(entry.value)
        if entry.lru_node is not None:
            self.lru_list.remove_node(entry.lru_node)
        if count_evicted:
            self.evicted_keys += 1
        return True

    def purge_expired(self):
        """Actively drain the heap of anything already expired (lazy deletion
        for stale/superseded entries left behind by overwrite/EXPIRE)."""
        now = self._now()
        while not self.ttl_heap.is_empty():
            expire_at, key = self.ttl_heap.peek()
            entry = self.data.get(key)
            if entry is None or entry.expire_at != expire_at:
                self.ttl_heap.pop()  # stale heap entry, key changed/removed since
                continue
            if expire_at > now:
                break  # heap top is the earliest; nothing else is expired yet
            self.ttl_heap.pop()
            self._delete_key(key)

    def _check_expired(self, key):
        """Passive check for a single key: delete-and-report-missing if expired."""
        entry = self.data.get(key)
        if entry is None:
            return None
        if entry.expire_at is not None and entry.expire_at <= self._now():
            self._delete_key(key)
            return None
        return entry

    # -- string commands ----------------------------------------------------

    def set(self, key, value):
        entry_size = _byte_len(key) + _byte_len(value)
        if self.maxmemory > 0 and entry_size > self.maxmemory:
            raise OOMError()

        existing = self._check_expired(key)
        if existing is not None:
            self.used_memory -= _byte_len(key) + _byte_len(existing.value)
            existing.value = value
            existing.expire_at = None  # overwriting resets TTL
            self.used_memory += entry_size
            self.lru_list.move_to_front(existing.lru_node)
        else:
            node = self.lru_list.insert_front(key)
            self.data.put(key, Entry(value=value, expire_at=None, lru_node=node))
            self.used_memory += entry_size

        if self.maxmemory > 0:
            while self.used_memory > self.maxmemory and self.lru_list.tail is not None:
                lru_key = self.lru_list.tail.data
                if lru_key == key:
                    break  # nothing left to evict but the key we just wrote
                self._delete_key(lru_key, count_evicted=True)

    def get(self, key):
        entry = self._check_expired(key)
        if entry is None:
            return None
        self.lru_list.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key):
        entry = self._check_expired(key)
        if entry is None:
            return False
        return self._delete_key(key)

    def exists(self, key):
        return self._check_expired(key) is not None

    def dbsize(self):
        return self.data.size()

    def keys(self):
        live = []
        for key in self.data.keys():
            if self._check_expired(key) is not None:
                live.append(key)
        return live

    # -- TTL commands ---------------------------------------------------------

    def expire(self, key, seconds):
        entry = self._check_expired(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete_key(key)
            return 1
        entry.expire_at = self._now() + seconds
        self.ttl_heap.push((entry.expire_at, key))
        return 1

    def ttl(self, key):
        entry = self._check_expired(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        remaining = entry.expire_at - self._now()
        if remaining <= 0:
            self._delete_key(key)
            return -2
        return int(math.ceil(remaining))

    # -- memory / config --------------------------------------------------

    def config_set_maxmemory(self, num_bytes):
        self.maxmemory = num_bytes

    def info_memory(self):
        return {
            "used_memory": self.used_memory,
            "maxmemory": self.maxmemory,
            "evicted_keys": self.evicted_keys,
        }
