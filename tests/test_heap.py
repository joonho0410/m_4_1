import random
import unittest

from mini_redis.heap import MinHeap


class TestMinHeap(unittest.TestCase):
    def test_push_pop_sorted_order(self):
        heap = MinHeap()
        values = [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]
        for v in values:
            heap.push(v)
        popped = [heap.pop() for _ in range(len(values))]
        self.assertEqual(popped, sorted(values))

    def test_peek_does_not_remove(self):
        heap = MinHeap()
        heap.push((10, "x"))
        heap.push((5, "y"))
        self.assertEqual(heap.peek(), (5, "y"))
        self.assertEqual(heap.size(), 2)

    def test_empty_heap(self):
        heap = MinHeap()
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())
        self.assertTrue(heap.is_empty())

    def test_random_stress_matches_sorted(self):
        random.seed(42)
        values = [(random.randint(0, 1000), f"k{i}") for i in range(200)]
        heap = MinHeap()
        for v in values:
            heap.push(v)
        popped = [heap.pop() for _ in range(len(values))]
        self.assertEqual(popped, sorted(values))


if __name__ == "__main__":
    unittest.main()
