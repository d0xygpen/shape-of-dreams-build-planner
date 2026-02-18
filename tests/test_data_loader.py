"""Tests for the DataLoader module."""

import sys
import unittest
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.data_loader import DataLoader, DataLoadError


class TestDataLoader(unittest.TestCase):
    """Test DataLoader with real project data."""

    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()

    def test_loads_builds(self):
        builds = self.loader.builds
        self.assertIsInstance(builds, dict)
        self.assertGreater(len(builds), 0)
        # All keys should be lowercase character names
        for key in builds:
            self.assertEqual(key, key.lower())

    def test_builds_for_known_character(self):
        builds = self.loader.builds_for("mist")
        self.assertIsInstance(builds, list)
        self.assertGreater(len(builds), 0)
        # Each build should have a name
        for build in builds:
            self.assertIn("name", build)

    def test_builds_for_unknown_character(self):
        builds = self.loader.builds_for("nonexistent")
        self.assertEqual(builds, [])

    def test_builds_for_case_insensitive(self):
        builds_lower = self.loader.builds_for("mist")
        builds_upper = self.loader.builds_for("MIST")
        self.assertEqual(len(builds_lower), len(builds_upper))

    def test_loads_essences(self):
        essences = self.loader.essences
        self.assertIsInstance(essences, list)
        self.assertGreater(len(essences), 50)
        for e in essences:
            self.assertIn("name", e)
            self.assertIn("rarity", e)

    def test_loads_memories(self):
        memories = self.loader.memories
        self.assertIsInstance(memories, list)
        self.assertGreater(len(memories), 50)
        for m in memories:
            self.assertIn("name", m)

    def test_loads_characters(self):
        characters = self.loader.characters
        self.assertIsInstance(characters, list)
        self.assertGreater(len(characters), 0)
        for c in characters:
            self.assertIn("name", c)

    def test_essence_by_name_lookup(self):
        lookup = self.loader.essence_by_name
        self.assertIn("Essence of Paranoia", lookup)
        self.assertEqual(lookup["Essence of Paranoia"]["rarity"], "Legendary")

    def test_essence_rarity_map(self):
        rmap = self.loader.essence_rarity_map
        self.assertIn("Essence of Paranoia", rmap)
        self.assertEqual(rmap["Essence of Paranoia"], "Legendary")

    def test_memory_by_name_lookup(self):
        lookup = self.loader.memory_by_name
        self.assertIsInstance(lookup, dict)
        self.assertGreater(len(lookup), 0)

    def test_character_names(self):
        names = self.loader.character_names
        self.assertIsInstance(names, list)
        self.assertIn("mist", names)

    def test_get_rarity_symbol(self):
        self.assertEqual(self.loader.get_rarity_symbol("Essence of Paranoia"), "[L]")
        self.assertEqual(self.loader.get_rarity_symbol("nonexistent"), "[?]")

    def test_get_all_essences_in_build(self):
        builds = self.loader.builds_for("mist")
        if builds:
            essences = self.loader.get_all_essences_in_build(builds[0])
            self.assertIsInstance(essences, list)
            self.assertGreater(len(essences), 0)

    def test_count_rarity(self):
        builds = self.loader.builds_for("mist")
        if builds:
            rarity = self.loader.count_rarity(builds[0])
            self.assertIn("Legendary", rarity)
            self.assertIn("Epic", rarity)
            total = sum(rarity.values())
            self.assertGreater(total, 0)

    def test_invalidate_cache(self):
        # Should not crash
        self.loader.invalidate_cache()
        # Data should reload on next access
        builds = self.loader.builds
        self.assertGreater(len(builds), 0)

    def test_missing_file_raises_error(self):
        bad_loader = DataLoader(base_dir=Path("/nonexistent"))
        with self.assertRaises(DataLoadError):
            _ = bad_loader.essences


if __name__ == "__main__":
    unittest.main()
