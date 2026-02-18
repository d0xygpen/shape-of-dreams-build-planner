"""Tests for build_comparator, synergy_analyzer, and build_analyzer."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.data_loader import DataLoader
from analysis.build_comparator import BuildComparator
from analysis.synergy_analyzer import SynergyAnalyzer
from analysis.build_analyzer import BuildAnalyzer


class TestBuildComparator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()
        cls.comparator = BuildComparator(cls.loader)

    def test_compare_known_character(self):
        result = self.comparator.compare_builds("mist")
        self.assertNotIn("error", result)
        self.assertEqual(result["character"], "mist")
        self.assertGreater(len(result["builds"]), 0)

    def test_compare_unknown_character(self):
        result = self.comparator.compare_builds("nonexistent")
        self.assertIn("error", result)

    def test_builds_sorted_by_synergy(self):
        result = self.comparator.compare_builds("mist")
        scores = [b["synergy_score"] for b in result["builds"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_recommend_build(self):
        result = self.comparator.recommend_build("mist", {
            "playstyle": "aggressive",
            "focus": "damage",
            "complexity": "any",
        })
        self.assertNotIn("error", result)
        self.assertGreater(len(result["recommendations"]), 0)
        self.assertIsNotNone(result["top_recommendation"])

    def test_recommend_unknown_character(self):
        result = self.comparator.recommend_build("nonexistent", {})
        self.assertIn("error", result)

    def test_all_builds_summary(self):
        summary = self.comparator.get_all_builds_summary()
        self.assertGreater(summary["total_builds"], 0)
        self.assertGreater(len(summary["characters"]), 0)
        self.assertGreater(len(summary["top_synergy_builds"]), 0)

    def test_find_builds_with_essence(self):
        results = self.comparator.find_builds_with_essence("Essence of Paranoia")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("character", r)
            self.assertIn("build", r)

    def test_find_builds_nonexistent_essence(self):
        results = self.comparator.find_builds_with_essence("Nonexistent Essence")
        self.assertEqual(results, [])


class TestSynergyAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()
        cls.analyzer = SynergyAnalyzer(cls.loader)

    def test_find_synergies_known_memory(self):
        # Shadow Walk is a known memory in memories.json
        result = self.analyzer.find_synergies(
            "Shadow Walk",
            ["Essence of Twilight", "Essence of the Abyss"],
        )
        self.assertNotIn("error", result)
        self.assertEqual(result["memory"], "Shadow Walk")
        self.assertIsInstance(result["synergy_score"], int)

    def test_find_synergies_unknown_memory(self):
        result = self.analyzer.find_synergies("Nonexistent", ["Ess1"])
        self.assertIn("error", result)

    def test_cross_memory_synergies(self):
        memories = [
            {"name": "M1", "essences": ["Essence of Paranoia"]},
            {"name": "M2", "essences": ["Essence of Momentum"]},
        ]
        result = self.analyzer.analyze_cross_memory_synergies(memories)
        self.assertIn("cross_memory_synergies", result)
        self.assertGreater(result["cross_memory_score"], 0)

    def test_suggest_substitutes(self):
        subs = self.analyzer.suggest_substitutes("Essence of Paranoia")
        self.assertIsInstance(subs, list)
        self.assertGreater(len(subs), 0)
        for s in subs:
            self.assertIn("essence", s)
            self.assertIn("shared_types", s)

    def test_suggest_substitutes_unknown(self):
        subs = self.analyzer.suggest_substitutes("Nonexistent Essence")
        self.assertEqual(subs, [])


class TestBuildAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = DataLoader()
        cls.analyzer = BuildAnalyzer(cls.loader)

    def test_unified_score(self):
        builds = self.loader.builds_for("mist")
        if builds:
            score = self.analyzer.unified_score(builds[0])
            self.assertIn("total", score)
            self.assertGreaterEqual(score["total"], 0)
            self.assertLessEqual(score["total"], 100)
            # Components should sum to total
            expected = (
                score["synergy"]
                + score["rarity"]
                + score["validity"]
                + score["completeness"]
            )
            self.assertEqual(score["total"], expected)

    def test_gap_analysis(self):
        result = self.analyzer.gap_analysis("mist")
        self.assertNotIn("error", result)
        self.assertIn("covered_archetypes", result)
        self.assertIn("uncovered_archetypes", result)
        self.assertIn("coverage_pct", result)
        self.assertGreaterEqual(result["coverage_pct"], 0)
        self.assertLessEqual(result["coverage_pct"], 100)

    def test_gap_analysis_unknown(self):
        result = self.analyzer.gap_analysis("nonexistent")
        self.assertIn("error", result)

    def test_cross_character_comparison(self):
        result = self.analyzer.cross_character_comparison()
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        for char, info in result.items():
            self.assertIn("build_count", info)
            self.assertIn("avg_score", info)
            self.assertIn("archetype_coverage", info)

    def test_essence_meta_report(self):
        report = self.analyzer.essence_meta_report()
        self.assertIn("total_builds", report)
        self.assertIn("most_used", report)
        self.assertIn("unused_essences", report)
        self.assertIn("most_common_pairs", report)
        self.assertGreater(report["total_builds"], 0)

    def test_build_scorecard(self):
        card = self.analyzer.build_scorecard("mist", "Twilight")
        self.assertIsNotNone(card)
        self.assertIn("grade", card)
        self.assertIn(card["grade"], ["S", "A", "B", "C", "D", "F"])
        self.assertIn("improvements", card)

    def test_build_scorecard_not_found(self):
        card = self.analyzer.build_scorecard("mist", "Nonexistent Build Name XYZ")
        self.assertIsNone(card)

    def test_score_to_grade(self):
        self.assertEqual(BuildAnalyzer._score_to_grade(95), "S")
        self.assertEqual(BuildAnalyzer._score_to_grade(85), "A")
        self.assertEqual(BuildAnalyzer._score_to_grade(70), "B")
        self.assertEqual(BuildAnalyzer._score_to_grade(55), "C")
        self.assertEqual(BuildAnalyzer._score_to_grade(40), "D")
        self.assertEqual(BuildAnalyzer._score_to_grade(20), "F")


if __name__ == "__main__":
    unittest.main()
