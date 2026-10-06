import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gzmember import core, samples


class GzmemberTest(unittest.TestCase):
    def test_single_plain_member(self):
        index = core.open_members(samples.make_member(b"abc"), core.Counter())
        self.assertEqual(index.read(0, core.Counter()), b"abc")

    def test_multi_plain_members(self):
        raw = samples.make_member(b"one") + samples.make_member(b"two")
        index = core.open_members(raw, core.Counter())
        self.assertEqual(len(index.members), 2)

    def test_read_out_of_range(self):
        index = core.open_members(samples.make_member(b"abc"), core.Counter())
        self.assertIsNone(index.read(5, core.Counter()))

    def test_member_size(self):
        index = core.open_members(samples.make_member(b"abcd"), core.Counter())
        self.assertEqual(index.members[0]["size"], 4)

    def test_plain_name_empty(self):
        index = core.open_members(samples.make_member(b"abc"), core.Counter())
        self.assertEqual(index.members[0]["name"], "")

    def test_counter_counts(self):
        counter = core.Counter()
        core.open_members(samples.make_member(b"abc"), counter)
        self.assertGreater(counter.scanned, 0)


if __name__ == "__main__":
    unittest.main()
