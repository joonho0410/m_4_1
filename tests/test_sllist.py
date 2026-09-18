import unittest

from mini_redis.sllist import SinglyLinkedList


class TestSinglyLinkedList(unittest.TestCase):
    def test_append_node_reuses_existing_node(self):
        src = SinglyLinkedList()
        node = src.insert_back(1)
        dst = SinglyLinkedList()
        dst.append_node(node)
        self.assertIs(dst.head, node)  # same object, no reallocation
        self.assertIs(dst.tail, node)
        self.assertEqual(list(dst), [1])
        self.assertEqual(dst.size(), 1)
        self.assertIsNone(node.next)  # detached from any prior chain

    def test_append_node_onto_existing_tail(self):
        dst = SinglyLinkedList()
        dst.insert_back(1)
        other = SinglyLinkedList()
        node2 = other.insert_back(2)
        dst.append_node(node2)
        self.assertEqual(list(dst), [1, 2])
        self.assertIs(dst.tail, node2)
        self.assertEqual(dst.size(), 2)

    def test_insert_back(self):
        sll = SinglyLinkedList()
        sll.insert_back(1)
        sll.insert_back(2)
        sll.insert_back(3)
        self.assertEqual(list(sll), [1, 2, 3])
        self.assertEqual(sll.size(), 3)
        self.assertEqual(sll.head.data, 1)
        self.assertEqual(sll.tail.data, 3)

    def test_remove_after_head(self):
        sll = SinglyLinkedList()
        nodes = [sll.insert_back(v) for v in (1, 2, 3)]
        sll.remove_after(None, nodes[0])  # remove head (1)
        self.assertEqual(list(sll), [2, 3])
        self.assertEqual(sll.head.data, 2)
        self.assertEqual(sll.size(), 2)

    def test_remove_after_middle(self):
        sll = SinglyLinkedList()
        nodes = [sll.insert_back(v) for v in (1, 2, 3, 4)]
        sll.remove_after(nodes[0], nodes[1])  # remove 2
        self.assertEqual(list(sll), [1, 3, 4])
        self.assertEqual(sll.size(), 3)

    def test_remove_after_tail_updates_tail(self):
        sll = SinglyLinkedList()
        nodes = [sll.insert_back(v) for v in (1, 2, 3)]
        sll.remove_after(nodes[1], nodes[2])  # remove tail (3)
        self.assertEqual(list(sll), [1, 2])
        self.assertIs(sll.tail, nodes[1])
        self.assertEqual(sll.size(), 2)

    def test_remove_only_node_empties_list(self):
        sll = SinglyLinkedList()
        node = sll.insert_back(1)
        sll.remove_after(None, node)
        self.assertEqual(list(sll), [])
        self.assertIsNone(sll.head)
        self.assertIsNone(sll.tail)
        self.assertEqual(sll.size(), 0)

    def test_empty_list_is_empty(self):
        sll = SinglyLinkedList()
        self.assertTrue(sll.is_empty())
        sll.insert_back(1)
        self.assertFalse(sll.is_empty())


if __name__ == "__main__":
    unittest.main()
