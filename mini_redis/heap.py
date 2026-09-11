"""Binary min-heap, backed by DynamicArray, used to track TTL expirations.

Elements are (expire_at, key) pairs. A min-heap keyed on expire_at lets the
store find "which key expires soonest" in O(1) (peek) and keep that
invariant after push/pop in O(log n), instead of scanning every key.
"""

from .dynamic_array import DynamicArray


class MinHeap:
    def __init__(self):
        self._arr = DynamicArray()

    def size(self):
        return len(self._arr)

    def is_empty(self):
        return len(self._arr) == 0

    def peek(self):
        if len(self._arr) == 0:
            return None
        return self._arr.get(0)

    def push(self, item):
        self._arr.append(item)
        self._heapify_up(len(self._arr) - 1)

    def pop(self):
        n = len(self._arr)
        if n == 0:
            return None
        top = self._arr.get(0)
        last = self._arr.pop()
        if len(self._arr) > 0:
            self._arr.set(0, last)
            self._heapify_down(0)
        return top

    def _swap(self, i, j):
        a, b = self._arr.get(i), self._arr.get(j)
        self._arr.set(i, b)
        self._arr.set(j, a)

    def _heapify_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self._arr.get(i) < self._arr.get(parent):
                self._swap(i, parent)
                i = parent
            else:
                break

    def _heapify_down(self, i):
        n = len(self._arr)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self._arr.get(left) < self._arr.get(smallest):
                smallest = left
            if right < n and self._arr.get(right) < self._arr.get(smallest):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest
