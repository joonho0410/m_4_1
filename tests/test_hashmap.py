import unittest

from mini_redis.hashmap import HashMap, _LOAD_FACTOR


class TestHashMap(unittest.TestCase):
    def test_put_get_basic(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("b", 2)
        self.assertEqual(hm.get("a"), 1)
        self.assertEqual(hm.get("b"), 2)
        self.assertIsNone(hm.get("missing"))
        self.assertEqual(hm.size(), 2)

    def test_put_overwrites(self):
        hm = HashMap()
        hm.put("a", 1)
        hm.put("a", 2)
        self.assertEqual(hm.get("a"), 2)
        self.assertEqual(hm.size(), 1)

    def test_remove_and_contains(self):
        hm = HashMap()
        hm.put("a", 1)
        self.assertTrue(hm.contains("a"))
        self.assertTrue(hm.remove("a"))
        self.assertFalse(hm.contains("a"))
        self.assertFalse(hm.remove("a"))
        self.assertEqual(hm.size(), 0)

    def test_pop_returns_value(self):
        hm = HashMap()
        hm.put("a", 42)
        self.assertEqual(hm.pop("a"), 42)
        self.assertIsNone(hm.pop("a"))

    def test_keys(self):
        hm = HashMap()
        for k in ("x", "y", "z"):
            hm.put(k, k.upper())
        self.assertEqual(sorted(hm.keys()), ["x", "y", "z"])

    def test_collision_chaining(self):
        # Force two keys into the same bucket of a tiny table and verify
        # both survive (chaining), independent of insertion order.
        hm = HashMap(capacity=4)
        k1, k2 = None, None
        # find two distinct keys that collide in a 4-bucket table
        candidates = [f"k{i}" for i in range(50)]
        buckets = {}
        for c in candidates:
            idx = hm._bucket_index(c)
            buckets.setdefault(idx, []).append(c)
        for idx, ks in buckets.items():
            if len(ks) >= 2:
                k1, k2 = ks[0], ks[1]
                break
        self.assertIsNotNone(k1)
        hm.put(k1, "v1")
        hm.put(k2, "v2")
        self.assertEqual(hm.get(k1), "v1")
        self.assertEqual(hm.get(k2), "v2")

    def test_resize_on_load_factor(self):
        hm = HashMap(capacity=4)
        initial_capacity = hm._capacity
        # load factor 0.75 on capacity 4 -> trips after the 4th insert (4/4 > .75)
        for i in range(4):
            hm.put(f"key{i}", i)
        self.assertGreater(hm._capacity, initial_capacity)
        # all entries survive the resize/rehash
        for i in range(4):
            self.assertEqual(hm.get(f"key{i}"), i)
        self.assertEqual(hm.size(), 4)

    def test_load_factor_never_exceeds_threshold_after_resize(self):
        hm = HashMap(capacity=4)
        for i in range(100):
            hm.put(f"key{i}", i)
        self.assertLessEqual(hm.size() / hm._capacity, _LOAD_FACTOR)

    def test_resize_reuses_nodes_instead_of_reallocating(self):
        hm = HashMap(capacity=4)
        hm.put("a", 1)
        _, _, node_before = hm._find_node("a")
        for i in range(20):  # forces several resizes
            hm.put(f"key{i}", i)
        _, _, node_after = hm._find_node("a")
        self.assertIs(node_before, node_after)
        self.assertEqual(hm.get("a"), 1)


if __name__ == "__main__":
    unittest.main()
