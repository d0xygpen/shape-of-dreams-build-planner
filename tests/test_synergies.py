"""Tests for the synergies module."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.synergies import (
    get_synergy_for_pair,
    get_pair_score,
    score_essence_set,
    find_all_synergies_in_set,
    get_category_for_types,
    ESSENCE_SYNERGIES,
    SYNERGY_CATEGORIES,
)


class TestGetSynergyForPair(unittest.TestCase):
    def test_known_pair_order_1(self):
        info = get_synergy_for_pair("Glacial Core", "Essence of Clemency")
        self.assertIn("score", info)
        self.assertEqual(info["score"], 25)

    def test_known_pair_order_2(self):
        info = get_synergy_for_pair("Essence of Clemency", "Glacial Core")
        self.assertIn("score", info)
        self.assertEqual(info["score"], 25)

    def test_unknown_pair(self):
        info = get_synergy_for_pair("Nonexistent1", "Nonexistent2")
        self.assertEqual(info, {})


class TestGetPairScore(unittest.TestCase):
    def test_known_pair(self):
        self.assertEqual(get_pair_score("Divine Faith", "Essence of Domination"), 22)

    def test_unknown_pair(self):
        self.assertEqual(get_pair_score("A", "B"), 0)


class TestScoreEssenceSet(unittest.TestCase):
    def test_empty_set(self):
        self.assertEqual(score_essence_set(set()), 0)

    def test_single_synergy_pair(self):
        essences = {"Glacial Core", "Essence of Clemency"}
        score = score_essence_set(essences)
        self.assertEqual(score, 25)

    def test_multiple_synergies(self):
        essences = {
            "Essence of Paranoia", "Essence of Momentum",
            "Essence of Domination", "Essence of Fangs",
        }
        score = score_essence_set(essences)
        # Paranoia+Momentum=20, Domination+Fangs=18, Paranoia solo=15
        self.assertEqual(score, 53)

    def test_solo_essence(self):
        essences = {"Essence of Paranoia"}
        score = score_essence_set(essences)
        self.assertEqual(score, 15)


class TestFindAllSynergiesInSet(unittest.TestCase):
    def test_finds_known_synergies(self):
        essences = {"Essence of Paranoia", "Essence of Momentum", "Essence of Efficiency"}
        found = find_all_synergies_in_set(essences)
        pair_names = [tuple(sorted(s["pair"])) for s in found]
        self.assertIn(
            tuple(sorted(["Essence of Paranoia", "Essence of Momentum"])),
            pair_names,
        )
        self.assertIn(
            tuple(sorted(["Essence of Momentum", "Essence of Efficiency"])),
            pair_names,
        )

    def test_empty_set(self):
        found = find_all_synergies_in_set(set())
        self.assertEqual(found, [])


class TestGetCategoryForTypes(unittest.TestCase):
    def test_single_match(self):
        cats = get_category_for_types({"fire_damage"})
        self.assertIn("damage_conversion", cats)

    def test_multiple_matches(self):
        cats = get_category_for_types({"healing", "cooldown_reduction"})
        self.assertIn("healing", cats)
        self.assertIn("cooldown", cats)

    def test_no_match(self):
        cats = get_category_for_types({"nonexistent_type"})
        self.assertEqual(cats, [])


class TestSynergyDefinitionsIntegrity(unittest.TestCase):
    def test_all_pairs_have_score(self):
        for pair, info in ESSENCE_SYNERGIES.items():
            self.assertIn("score", info, f"Missing score for pair {pair}")
            self.assertIsInstance(info["score"], int)
            self.assertGreater(info["score"], 0)

    def test_all_pairs_have_description(self):
        for pair, info in ESSENCE_SYNERGIES.items():
            self.assertIn("description", info, f"Missing description for pair {pair}")
            self.assertIsInstance(info["description"], str)
            self.assertGreater(len(info["description"]), 0)

    def test_all_categories_have_types(self):
        for cat, types in SYNERGY_CATEGORIES.items():
            self.assertIsInstance(types, list)
            self.assertGreater(len(types), 0)


if __name__ == "__main__":
    unittest.main()
