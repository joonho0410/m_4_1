import unittest

from mini_redis.dynamic_array import DynamicArray


class TestDynamicArray(unittest.TestCase):
    def test_append_and_get(self):
        arr = DynamicArray(capacity=2)
        for i in range(10):
            arr.append(i)
        self.assertEqual(len(arr), 10)
        for i in range(10):
            self.assertEqual(arr.get(i), i)

    def test_capacity_doubles(self):
        arr = DynamicArray(capacity=2)
        self.assertEqual(arr._capacity, 2)
        arr.append(1)
        arr.append(2)
        arr.append(3)  # triggers resize
        self.assertEqual(arr._capacity, 4)

    def test_set(self):
        arr = DynamicArray()
        arr.append(1)
        arr.set(0, 99)
        self.assertEqual(arr.get(0), 99)

    def test_remove_shifts_elements(self):
        arr = DynamicArray()
        for i in range(5):
            arr.append(i)
        removed = arr.remove(1)
        self.assertEqual(removed, 1)
        self.assertEqual([arr.get(i) for i in range(len(arr))], [0, 2, 3, 4])

    def test_pop(self):
        arr = DynamicArray()
        arr.append(1)
        arr.append(2)
        self.assertEqual(arr.pop(), 2)
        self.assertEqual(len(arr), 1)

    def test_index_error(self):
        arr = DynamicArray()
        with self.assertRaises(IndexError):
            arr.get(0)


if __name__ == "__main__":
    unittest.main()
