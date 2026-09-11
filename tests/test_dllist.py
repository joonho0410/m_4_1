import unittest

from mini_redis.dllist import DoublyLinkedList


class TestDoublyLinkedList(unittest.TestCase):
    def test_insert_front_and_back(self):
        dll = DoublyLinkedList()
        dll.insert_back(1)
        dll.insert_back(2)
        dll.insert_front(0)
        self.assertEqual(list(dll), [0, 1, 2])
        self.assertEqual(dll.size(), 3)
        self.assertEqual(dll.head.data, 0)
        self.assertEqual(dll.tail.data, 2)

    def test_remove_front_back(self):
        dll = DoublyLinkedList()
        for v in (1, 2, 3):
            dll.insert_back(v)
        self.assertEqual(dll.remove_front(), 1)
        self.assertEqual(dll.remove_back(), 3)
        self.assertEqual(list(dll), [2])
        self.assertEqual(dll.size(), 1)

    def test_remove_node_middle(self):
        dll = DoublyLinkedList()
        nodes = [dll.insert_back(v) for v in (1, 2, 3, 4)]
        dll.remove_node(nodes[1])  # remove 2
        self.assertEqual(list(dll), [1, 3, 4])
        self.assertEqual(dll.size(), 3)

    def test_move_to_front(self):
        dll = DoublyLinkedList()
        nodes = [dll.insert_back(v) for v in (1, 2, 3)]
        dll.move_to_front(nodes[2])  # move 3 to front
        self.assertEqual(list(dll), [3, 1, 2])
        dll.move_to_front(nodes[2])  # already at front, no-op
        self.assertEqual(list(dll), [3, 1, 2])
        self.assertEqual(dll.size(), 3)

    def test_empty_list_removals_return_none(self):
        dll = DoublyLinkedList()
        self.assertIsNone(dll.remove_front())
        self.assertIsNone(dll.remove_back())
        self.assertEqual(dll.size(), 0)


if __name__ == "__main__":
    unittest.main()
