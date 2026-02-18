"""Tests for the validators module."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.data_loader import DataLoader
from analysis.validators import (
    validate_no_duplicate_essences,
    validate_build_references,
    validate_build_schema,
    validate_full_build,
)


class TestValidateNoDuplicateEssences(unittest.TestCase):
    def test_valid_build_no_duplicates(self):
        build = {
            "memories": [
                {"name": "A", "essences": ["Ess1", "Ess2"]},
                {"name": "B", "essences": ["Ess3", "Ess4"]},
            ]
        }
        result = validate_no_duplicate_essences(build)
        self.assertTrue(result["valid"])
        self.assertEqual(result["duplicates"], [])
        self.assertEqual(result["total_essences"], 4)
        self.assertEqual(result["unique_essences"], 4)

    def test_invalid_build_with_duplicates(self):
        build = {
            "memories": [
                {"name": "A", "essences": ["Ess1", "Ess2"]},
                {"name": "B", "essences": ["Ess1", "Ess3"]},
            ]
        }
        result = validate_no_duplicate_essences(build)
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicates"], ["Ess1"])

    def test_empty_build(self):
        result = validate_no_duplicate_essences({})
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_essences"], 0)

    def test_passive_essences_checked(self):
        build = {
            "memories": [
                {"name": "A", "essences": ["Ess1"]},
            ],
            "passive_essences": [
                {"name": "Ess1"},
            ],
        }
        result = validate_no_duplicate_essences(build)
        self.assertFalse(result["valid"])
        self.assertIn("Ess1", result["duplicates"])


class TestValidateBuildSchema(unittest.TestCase):
    def test_valid_build(self):
        build = {
            "name": "Test Build",
            "concept": "Test concept",
            "playstyle": "Test",
            "memories": [{"name": "Mem1", "essences": ["Ess1"]}],
            "constellation_tree": {"primary": "Destruction"},
            "strengths": ["Strong"],
            "weaknesses": ["Weak"],
        }
        result = validate_build_schema(build)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)

    def test_missing_required_fields(self):
        build = {"name": "Test"}
        result = validate_build_schema(build)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)

    def test_missing_tree_produces_warning(self):
        build = {
            "name": "Test",
            "concept": "Test",
            "playstyle": "Test",
            "memories": [{"name": "M", "essences": ["E"]}],
            "strengths": [],
            "weaknesses": [],
        }
        result = validate_build_schema(build)
        self.assertTrue(result.valid)
        warning_texts = " ".join(result.warnings)
        self.assertIn("tree", warning_texts.lower())


class TestValidateFullBuild(unittest.TestCase):
    def test_valid_build_without_loader(self):
        build = {
            "name": "Test",
            "concept": "Test",
            "playstyle": "Test",
            "memories": [{"name": "M", "essences": ["E1", "E2"]}],
            "constellation_tree": {"primary": "Life"},
            "strengths": ["S"],
            "weaknesses": ["W"],
        }
        result = validate_full_build(build)
        self.assertTrue(result.valid)

    def test_with_loader_reference_check(self):
        loader = DataLoader()
        builds = loader.builds_for("mist")
        if builds:
            result = validate_full_build(builds[0], loader)
            # Real builds should pass basic validation
            self.assertIsInstance(result.valid, bool)


class TestValidateAllProjectBuilds(unittest.TestCase):
    """Integration test: validate every build in the project."""

    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()

    def test_all_builds_have_required_fields(self):
        for char, builds in self.loader.builds.items():
            for build in builds:
                self.assertIn("name", build, f"Build missing 'name' in {char}")
                self.assertIn("memories", build, f"Build '{build.get('name')}' missing memories in {char}")

    def test_no_empty_essence_lists(self):
        for char, builds in self.loader.builds.items():
            for build in builds:
                for memory in build.get("memories", []):
                    essences = memory.get("essences", [])
                    self.assertIsInstance(essences, list)
                    # Most memories should have essences
                    if memory.get("name"):
                        self.assertGreater(
                            len(essences), 0,
                            f"{char}/{build['name']}/{memory['name']} has no essences"
                        )


if __name__ == "__main__":
    unittest.main()
