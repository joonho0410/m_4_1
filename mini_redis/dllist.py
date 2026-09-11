"""Doubly linked list with O(1) insert/remove/move operations.

Reused by both the hash map (chaining buckets) and the LRU tracker,
which is why every removal/move method works off a direct node
reference instead of searching for the value.
"""


class DLLNode:
    __slots__ = ("prev", "next", "data")

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def size(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def insert_front(self, data):
        node = DLLNode(data)
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1
        return node

    def insert_back(self, data):
        node = DLLNode(data)
        node.prev = self.tail
        if self.tail is not None:
            self.tail.next = node
        self.tail = node
        if self.head is None:
            self.head = node
        self._size += 1
        return node

    def remove_node(self, node):
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = None
        node.next = None
        self._size -= 1

    def remove_front(self):
        if self.head is None:
            return None
        node = self.head
        self.remove_node(node)
        return node.data

    def remove_back(self):
        if self.tail is None:
            return None
        node = self.tail
        self.remove_node(node)
        return node.data

    def move_to_front(self, node):
        if node is self.head:
            return
        self.remove_node(node)
        node.prev = None
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next
