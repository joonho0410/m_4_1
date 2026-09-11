import unittest

from mini_redis.cli import MiniRedisCLI


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.cli = MiniRedisCLI()

    def run_cmd(self, line):
        return self.cli.execute(line)

    def test_set_get(self):
        self.assertEqual(self.run_cmd("SET name Alice"), "OK")
        self.assertEqual(self.run_cmd("GET name"), '"Alice"')

    def test_get_missing(self):
        self.assertEqual(self.run_cmd("GET missing"), "(nil)")

    def test_quoted_value_with_spaces(self):
        self.assertEqual(self.run_cmd('SET name "Alice Smith"'), "OK")
        self.assertEqual(self.run_cmd("GET name"), '"Alice Smith"')

    def test_del(self):
        self.run_cmd("SET a 1")
        self.assertEqual(self.run_cmd("DEL a"), "(integer) 1")
        self.assertEqual(self.run_cmd("DEL a"), "(integer) 0")

    def test_exists(self):
        self.run_cmd("SET a 1")
        self.assertEqual(self.run_cmd("EXISTS a"), "(integer) 1")
        self.assertEqual(self.run_cmd("EXISTS b"), "(integer) 0")

    def test_dbsize(self):
        self.run_cmd("SET a 1")
        self.run_cmd("SET b 2")
        self.assertEqual(self.run_cmd("DBSIZE"), "(integer) 2")

    def test_keys_empty(self):
        self.assertEqual(self.run_cmd("KEYS"), "(empty array)")

    def test_keys_nonempty(self):
        self.run_cmd("SET a 1")
        self.run_cmd("SET b 2")
        out = self.run_cmd("KEYS")
        self.assertIn('"a"', out)
        self.assertIn('"b"', out)

    def test_case_insensitive_command(self):
        self.assertEqual(self.run_cmd("set a 1"), "OK")
        self.assertEqual(self.run_cmd("get a"), '"1"')

    def test_unknown_command(self):
        self.assertEqual(self.run_cmd("FOO bar"), "(error) ERR unknown command 'FOO'")

    def test_wrong_number_of_args(self):
        self.assertEqual(
            self.run_cmd("SET onlykey"),
            "(error) ERR wrong number of arguments for 'set' command",
        )

    def test_expire_not_integer(self):
        self.run_cmd("SET a 1")
        self.assertEqual(
            self.run_cmd("EXPIRE a notanumber"),
            "(error) ERR value is not an integer or out of range",
        )

    def test_ttl_flow(self):
        self.run_cmd("SET a 1")
        self.assertEqual(self.run_cmd("TTL a"), "(integer) -1")
        self.assertEqual(self.run_cmd("EXPIRE a 100"), "(integer) 1")
        ttl_out = self.run_cmd("TTL a")
        self.assertTrue(ttl_out.startswith("(integer)"))
        self.assertNotEqual(ttl_out, "(integer) -1")

    def test_ttl_missing_key(self):
        self.assertEqual(self.run_cmd("TTL missing"), "(integer) -2")

    def test_expire_missing_key(self):
        self.assertEqual(self.run_cmd("EXPIRE missing 10"), "(integer) 0")

    def test_config_set_maxmemory_and_info(self):
        self.assertEqual(self.run_cmd("CONFIG SET maxmemory 1000"), "OK")
        info = self.run_cmd("INFO memory")
        self.assertIn("used_memory:0", info)
        self.assertIn("maxmemory:1000", info)
        self.assertIn("evicted_keys:0", info)

    def test_config_set_maxmemory_invalid(self):
        self.assertEqual(
            self.run_cmd("CONFIG SET maxmemory notanumber"),
            "(error) ERR value is not an integer or out of range",
        )

    def test_oom_error(self):
        self.run_cmd("CONFIG SET maxmemory 3")
        out = self.run_cmd("SET key toolongvalue")
        self.assertEqual(out, "(error) OOM command not allowed when used_memory > 'maxmemory'")

    def test_eviction_via_cli(self):
        self.run_cmd("CONFIG SET maxmemory 6")
        self.run_cmd("SET k1 v")
        self.run_cmd("SET k2 v")
        self.run_cmd("SET k3 v")  # evicts k1
        self.assertEqual(self.run_cmd("EXISTS k1"), "(integer) 0")
        info = self.run_cmd("INFO memory")
        self.assertIn("evicted_keys:1", info)

    def test_exit_quit_end_repl(self):
        self.assertIsNone(self.run_cmd("exit"))
        self.assertIsNone(self.run_cmd("quit"))

    def test_empty_line(self):
        self.assertEqual(self.run_cmd(""), "")

    def test_overwrite_resets_ttl_via_cli(self):
        self.run_cmd("SET a 1")
        self.run_cmd("EXPIRE a 100")
        self.run_cmd("SET a 2")
        self.assertEqual(self.run_cmd("TTL a"), "(integer) -1")


if __name__ == "__main__":
    unittest.main()
