"""Dynamic array (bonus) with capacity doubling, used as the heap's backing store."""


class DynamicArray:
    def __init__(self, capacity=4):
        self._capacity = max(1, capacity)
        self._size = 0
        self._data = [None] * self._capacity

    def __len__(self):
        return self._size

    def _check_index(self, index):
        if not (0 <= index < self._size):
            raise IndexError("DynamicArray index out of range")

    def _resize(self, new_capacity):
        new_data = [None] * new_capacity
        for i in range(self._size):
            new_data[i] = self._data[i]
        self._data = new_data
        self._capacity = new_capacity

    def append(self, value):
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._data[self._size] = value
        self._size += 1

    def get(self, index):
        self._check_index(index)
        return self._data[index]

    def set(self, index, value):
        self._check_index(index)
        self._data[index] = value

    def remove(self, index):
        self._check_index(index)
        value = self._data[index]
        for i in range(index, self._size - 1):
            self._data[i] = self._data[i + 1]
        self._data[self._size - 1] = None
        self._size -= 1
        if self._capacity > 4 and self._size <= self._capacity // 4:
            self._resize(max(4, self._capacity // 2))
        return value

    def pop(self):
        return self.remove(self._size - 1)
