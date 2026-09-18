"""Singly linked list used for hash map chaining.

Bucket chaining only ever walks forward from the bucket head to find a key,
so callers already have the predecessor node in hand by the time they need
to remove something -- there's no need to pay for a `prev` pointer on every
node just to support O(1) removal (that's what DoublyLinkedList is for,
e.g. the LRU tracker, which removes by node reference alone).
"""


class SLLNode:
    __slots__ = ("next", "data")

    def __init__(self, data):
        self.data = data
        self.next = None


class SinglyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def insert_back(self, data):
        node = SLLNode(data)
        if self.tail is not None:
            self.tail.next = node
        else:
            self.head = node
        self.tail = node
        self._size += 1
        return node

    def remove_after(self, prev, node):
        """Remove `node` in O(1), given the predecessor found while scanning
        for it (`prev=None` means `node` is the head)."""
        if prev is None:
            self.head = node.next
        else:
            prev.next = node.next
        if node is self.tail:
            self.tail = prev
        self._size -= 1

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next
