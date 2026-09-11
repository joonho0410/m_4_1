import unittest

from mini_redis.store import OOMError, Store


class FakeClock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class TestStoreBasics(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_set_get(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.get("a"), "1")

    def test_get_missing_is_none(self):
        self.assertIsNone(self.store.get("nope"))

    def test_delete(self):
        self.store.set("a", "1")
        self.assertTrue(self.store.delete("a"))
        self.assertFalse(self.store.delete("a"))
        self.assertIsNone(self.store.get("a"))

    def test_exists(self):
        self.store.set("a", "1")
        self.assertTrue(self.store.exists("a"))
        self.assertFalse(self.store.exists("b"))

    def test_dbsize_and_keys(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.assertEqual(self.store.dbsize(), 2)
        self.assertEqual(sorted(self.store.keys()), ["a", "b"])

    def test_overwrite_resets_ttl(self):
        clock = FakeClock()
        self.store._now = clock
        self.store.set("a", "1")
        self.store.expire("a", 10)
        self.assertEqual(self.store.ttl("a"), 10)
        self.store.set("a", "2")  # overwrite must clear TTL
        self.assertEqual(self.store.ttl("a"), -1)

    def test_used_memory_accounting(self):
        self.store.set("ab", "cd")  # 2 + 2 bytes
        self.assertEqual(self.store.used_memory, 4)
        self.store.set("ab", "cdef")  # replace value -> 2 + 4
        self.assertEqual(self.store.used_memory, 6)
        self.store.delete("ab")
        self.assertEqual(self.store.used_memory, 0)

    def test_used_memory_utf8(self):
        # "가" is 3 bytes in utf-8
        self.store.set("가", "나")
        self.assertEqual(self.store.used_memory, 6)


class TestTTL(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.clock = FakeClock()
        self.store._now = self.clock

    def test_ttl_no_key(self):
        self.assertEqual(self.store.ttl("missing"), -2)

    def test_ttl_no_expiry(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.ttl("a"), -1)

    def test_expire_missing_key(self):
        self.assertEqual(self.store.expire("missing", 10), 0)

    def test_expire_and_ttl(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.expire("a", 5), 1)
        self.assertEqual(self.store.ttl("a"), 5)

    def test_expire_zero_deletes_immediately(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.expire("a", 0), 1)
        self.assertFalse(self.store.exists("a"))

    def test_expire_negative_deletes_immediately(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.expire("a", -5), 1)
        self.assertFalse(self.store.exists("a"))

    def test_key_expires_after_ttl_elapses(self):
        self.store.set("a", "1")
        self.store.expire("a", 5)
        self.clock.advance(6)
        self.assertIsNone(self.store.get("a"))
        self.assertEqual(self.store.ttl("a"), -2)
        self.assertFalse(self.store.exists("a"))

    def test_expired_key_get_does_not_touch_lru(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 5)
        self.clock.advance(6)
        # a is expired; getting it should not resurrect it or affect ordering
        self.assertIsNone(self.store.get("a"))
        self.assertEqual(self.store.dbsize(), 1)

    def test_purge_expired_via_heap(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 5)
        self.store.expire("b", 100)
        self.clock.advance(6)
        self.store.purge_expired()
        self.assertEqual(self.store.dbsize(), 1)
        self.assertTrue(self.store.exists("b"))

    def test_stale_heap_entry_after_re_expire(self):
        self.store.set("a", "1")
        self.store.expire("a", 5)
        self.store.expire("a", 50)  # pushes a second heap entry; first becomes stale
        self.clock.advance(6)
        self.store.purge_expired()
        # should NOT be deleted: the *current* expire_at (50s out) hasn't passed
        self.assertTrue(self.store.exists("a"))


class TestLRUEviction(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_no_eviction_when_unlimited(self):
        self.store.config_set_maxmemory(0)
        for i in range(100):
            self.store.set(f"k{i}", "v")
        self.assertEqual(self.store.dbsize(), 100)
        self.assertEqual(self.store.evicted_keys, 0)

    def test_single_entry_too_large_is_oom(self):
        self.store.config_set_maxmemory(3)
        with self.assertRaises(OOMError):
            self.store.set("key", "toolong")
        self.assertEqual(self.store.dbsize(), 0)

    def test_eviction_removes_least_recently_used(self):
        # each entry is "kN"+"v" = 3 bytes; cap fits exactly 2 entries
        self.store.config_set_maxmemory(6)
        self.store.set("k1", "v")
        self.store.set("k2", "v")
        self.store.set("k3", "v")  # forces eviction of k1 (least recently used)
        self.assertFalse(self.store.exists("k1"))
        self.assertTrue(self.store.exists("k2"))
        self.assertTrue(self.store.exists("k3"))
        self.assertEqual(self.store.evicted_keys, 1)

    def test_get_updates_recency_protecting_from_eviction(self):
        self.store.config_set_maxmemory(9)  # fits 3 entries of 3 bytes each
        self.store.set("k1", "v")
        self.store.set("k2", "v")
        self.store.set("k3", "v")
        self.store.get("k1")  # k1 now most-recently-used; k2 becomes LRU
        self.store.set("k4", "v")  # should evict k2, not k1
        self.assertTrue(self.store.exists("k1"))
        self.assertFalse(self.store.exists("k2"))
        self.assertTrue(self.store.exists("k3"))
        self.assertTrue(self.store.exists("k4"))

    def test_used_memory_stays_within_limit_after_eviction(self):
        self.store.config_set_maxmemory(10)
        for i in range(20):
            self.store.set(f"k{i}", "v")
        self.assertLessEqual(self.store.used_memory, 10)
        self.assertGreater(self.store.evicted_keys, 0)

    def test_info_memory_fields(self):
        self.store.config_set_maxmemory(100)
        self.store.set("a", "1")
        info = self.store.info_memory()
        self.assertEqual(info["used_memory"], 2)
        self.assertEqual(info["maxmemory"], 100)
        self.assertEqual(info["evicted_keys"], 0)


if __name__ == "__main__":
    unittest.main()
