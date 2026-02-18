"""Tests for custom build save/load/delete functionality."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from analysis.data_loader import DataLoader


class TestCustomBuilds(unittest.TestCase):
    """Test custom build persistence via DataLoader."""

    def setUp(self):
        """Create a temp directory mimicking the project layout."""
        self.test_dir = Path(tempfile.mkdtemp())

        # Copy real data/ directory for valid essences/memories
        real_data = Path(__file__).parent.parent / "data"
        shutil.copytree(real_data, self.test_dir / "data")

        # Create minimal builds/ with one bundled build
        builds_dir = self.test_dir / "builds"
        builds_dir.mkdir()
        bundled = {
            "character": "Mist",
            "builds": [{
                "name": "Test Bundled Build",
                "concept": "A bundled test build",
                "playstyle": "Test",
                "memories": [{
                    "name": "Vile Strike",
                    "essences": ["Essence of Domination", "Essence of Fangs", "Essence of Crimson"],
                }],
            }],
        }
        with open(builds_dir / "mist_builds.json", "w", encoding="utf-8") as f:
            json.dump(bundled, f)

        # Loader with test dir
        self.loader = DataLoader(base_dir=self.test_dir)
        # Point custom builds to test dir too
        self.loader.custom_builds_dir = self.test_dir / "custom_builds"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _sample_build(self, name="My Custom Build"):
        return {
            "name": name,
            "concept": "Test concept",
            "playstyle": "Test playstyle",
            "_custom": True,
            "memories": [{
                "name": "Vile Strike",
                "essences": ["Essence of Insight", "Essence of Flow", "Essence of Shock"],
                "rationale": "Test rationale",
            }],
            "strategy": "Test strategy",
            "strengths": ["Strong point"],
            "weaknesses": ["Weak point"],
        }

    def test_save_creates_directory_and_file(self):
        """save_custom_build creates custom_builds/ dir and JSON file."""
        build = self._sample_build()
        path = self.loader.save_custom_build("mist", build)

        self.assertTrue(path.exists())
        self.assertTrue(self.loader.custom_builds_dir.exists())
        self.assertEqual(path.name, "mist_builds.json")

    def test_save_and_load_roundtrip(self):
        """Saved build appears in custom_builds property."""
        build = self._sample_build()
        self.loader.save_custom_build("mist", build)

        custom = self.loader.custom_builds
        self.assertIn("mist", custom)
        self.assertEqual(len(custom["mist"]), 1)
        self.assertEqual(custom["mist"][0]["name"], "My Custom Build")

    def test_all_builds_merges_bundled_and_custom(self):
        """all_builds contains both bundled and custom builds."""
        build = self._sample_build()
        self.loader.save_custom_build("mist", build)

        all_b = self.loader.all_builds
        mist_builds = all_b.get("mist", [])
        names = [b["name"] for b in mist_builds]

        self.assertIn("Test Bundled Build", names)
        self.assertIn("My Custom Build", names)

    def test_save_replaces_existing_by_name(self):
        """Saving a build with same name overwrites the previous one."""
        build = self._sample_build()
        self.loader.save_custom_build("mist", build)

        # Modify and re-save
        build["concept"] = "Updated concept"
        self.loader.save_custom_build("mist", build)

        custom = self.loader.custom_builds
        self.assertEqual(len(custom["mist"]), 1)
        self.assertEqual(custom["mist"][0]["concept"], "Updated concept")

    def test_save_multiple_builds_same_character(self):
        """Multiple custom builds for the same character coexist."""
        self.loader.save_custom_build("mist", self._sample_build("Build A"))
        self.loader.save_custom_build("mist", self._sample_build("Build B"))

        custom = self.loader.custom_builds
        names = [b["name"] for b in custom["mist"]]
        self.assertEqual(sorted(names), ["Build A", "Build B"])

    def test_save_different_character(self):
        """Custom builds for a new character create a new file."""
        build = self._sample_build()
        path = self.loader.save_custom_build("yubar", build)

        self.assertEqual(path.name, "yubar_builds.json")
        self.assertIn("yubar", self.loader.custom_builds)

    def test_delete_custom_build(self):
        """delete_custom_build removes a build by name."""
        self.loader.save_custom_build("mist", self._sample_build("To Delete"))
        self.assertTrue(self.loader.delete_custom_build("mist", "To Delete"))
        self.assertEqual(len(self.loader.custom_builds.get("mist", [])), 0)

    def test_delete_nonexistent_returns_false(self):
        """Deleting a build that doesn't exist returns False."""
        self.assertFalse(self.loader.delete_custom_build("mist", "Nope"))

    def test_is_custom_build(self):
        """is_custom_build distinguishes custom from bundled."""
        self.loader.save_custom_build("mist", self._sample_build())

        self.assertTrue(self.loader.is_custom_build("mist", "My Custom Build"))
        self.assertFalse(self.loader.is_custom_build("mist", "Test Bundled Build"))

    def test_all_character_names_includes_custom(self):
        """all_character_names includes characters with custom builds."""
        self.loader.save_custom_build("newchar", self._sample_build())

        names = self.loader.all_character_names
        self.assertIn("mist", names)      # bundled
        self.assertIn("newchar", names)    # custom only

    def test_invalidate_cache_clears_custom(self):
        """invalidate_cache clears the custom builds cache."""
        self.loader.save_custom_build("mist", self._sample_build())
        _ = self.loader.custom_builds  # populate cache

        self.loader.invalidate_cache()
        self.assertIsNone(self.loader._custom_builds)

    def test_empty_custom_dir(self):
        """custom_builds returns empty dict when dir doesn't exist."""
        self.assertEqual(self.loader.custom_builds, {})

    def test_custom_build_flag_preserved(self):
        """The _custom flag is preserved through save/load."""
        build = self._sample_build()
        build["_custom"] = True
        self.loader.save_custom_build("mist", build)

        loaded = self.loader.custom_builds["mist"][0]
        self.assertTrue(loaded.get("_custom"))


if __name__ == "__main__":
    unittest.main()
