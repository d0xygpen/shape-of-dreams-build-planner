"""
Build Analyzer for Shape of Dreams

Provides unified build scoring, gap analysis, cross-build insights,
and archetype coverage analysis.
"""

from typing import Dict, List, Optional, Set, Tuple

try:
    from analysis.data_loader import DataLoader, get_loader
    from analysis.validators import validate_no_duplicate_essences
    from analysis.synergies import (
        score_essence_set,
        find_all_synergies_in_set,
        SYNERGY_CATEGORIES,
    )
except ImportError:
    from data_loader import DataLoader, get_loader
    from validators import validate_no_duplicate_essences
    from synergies import (
        score_essence_set,
        find_all_synergies_in_set,
        SYNERGY_CATEGORIES,
    )


# Build archetypes for gap analysis
ARCHETYPES = {
    "damage_burst": {
        "keywords": ["burst", "execution", "damage", "assassin", "dps", "nuke"],
        "description": "High burst damage dealer",
    },
    "damage_sustained": {
        "keywords": ["sustained", "dps", "basic attack", "attack speed", "continuous"],
        "description": "Sustained damage over time",
    },
    "tank": {
        "keywords": ["tank", "defense", "shield", "fortress", "guardian", "barrier"],
        "description": "Tanky survivability build",
    },
    "healer_support": {
        "keywords": ["heal", "support", "ally", "buff", "restore"],
        "description": "Healing and support focus",
    },
    "scaling_infinite": {
        "keywords": ["scaling", "infinite", "faith", "domination", "divine", "stacks"],
        "description": "Infinite scaling late-game build",
    },
    "automation": {
        "keywords": ["auto", "paranoia", "retaliation", "automated", "passive"],
        "description": "Automated/low-management build",
    },
    "crowd_control": {
        "keywords": ["stun", "slow", "crowd", "control", "freeze", "cc"],
        "description": "Crowd control and utility",
    },
    "mobility": {
        "keywords": ["mobility", "speed", "dash", "movement", "agile"],
        "description": "Mobile hit-and-run playstyle",
    },
    "summoner": {
        "keywords": ["summon", "pack", "minion", "companion", "pet"],
        "description": "Summon/pet-based build",
    },
    "elemental_fire": {
        "keywords": ["fire", "burn", "flame", "inferno", "solar"],
        "description": "Fire/burn damage specialist",
    },
    "elemental_cold": {
        "keywords": ["cold", "frost", "freeze", "ice", "glacial"],
        "description": "Cold/freeze specialist",
    },
    "elemental_dark": {
        "keywords": ["dark", "shadow", "twilight", "abyss", "void"],
        "description": "Dark damage specialist",
    },
    "elemental_light": {
        "keywords": ["light", "radiant", "thunder", "lightning", "beam"],
        "description": "Light/thunder damage specialist",
    },
}


class BuildAnalyzer:
    """Unified build analysis engine combining scoring, gap detection, and insights."""

    def __init__(self, loader: Optional[DataLoader] = None):
        self.loader = loader or get_loader()

    def unified_score(self, build: Dict) -> Dict:
        """
        Calculate a unified build score (0-100) combining multiple factors.

        Breakdown:
        - Synergy score (0-40): Based on known synergy pairs
        - Rarity score (0-20): Quality of essences
        - Validity score (0-20): Passes game rules
        - Completeness score (0-20): Has all build components
        """
        # Synergy component (0-40)
        all_essences: Set[str] = set()
        for m in build.get("memories", []):
            all_essences.update(m.get("essences", []))
        raw_synergy = score_essence_set(all_essences)
        synergy_component = min(40, raw_synergy * 40 // 120)  # Normalize: 120+ = max

        # Rarity component (0-20)
        rarity = self.loader.count_rarity(build)
        leg = rarity.get("Legendary", 0)
        epic = rarity.get("Epic", 0)
        unique = rarity.get("Unique", 0)
        rarity_component = min(20, leg * 5 + epic * 2 + unique * 3)

        # Validity component (0-20)
        dup = validate_no_duplicate_essences(build)
        validity_component = 20 if dup["valid"] else 0

        # Completeness component (0-20)
        completeness = 0
        if build.get("memories"):
            completeness += 5
        if build.get("constellation_tree") or build.get("astrology_tree"):
            completeness += 5
        if build.get("strategy"):
            completeness += 4
        if build.get("strengths"):
            completeness += 3
        if build.get("weaknesses"):
            completeness += 3

        total = synergy_component + rarity_component + validity_component + completeness

        return {
            "total": total,
            "synergy": synergy_component,
            "rarity": rarity_component,
            "validity": validity_component,
            "completeness": completeness,
            "raw_synergy_score": raw_synergy,
            "synergy_details": find_all_synergies_in_set(all_essences),
        }

    def gap_analysis(self, character: str) -> Dict:
        """
        Identify which build archetypes are missing for a character.
        Returns covered and uncovered archetypes.
        """
        builds = self.loader.builds_for(character)
        if not builds:
            return {"error": f"Character '{character}' not found"}

        covered: Dict[str, List[str]] = {}  # archetype -> list of build names
        for build in builds:
            build_text = " ".join([
                build.get("name", ""),
                build.get("concept", ""),
                build.get("playstyle", ""),
                build.get("strategy", ""),
            ]).lower()

            for arch_name, arch_info in ARCHETYPES.items():
                matches = sum(1 for kw in arch_info["keywords"] if kw in build_text)
                if matches >= 2:
                    covered.setdefault(arch_name, []).append(build.get("name", ""))

        uncovered = []
        for arch_name, arch_info in ARCHETYPES.items():
            if arch_name not in covered:
                uncovered.append({
                    "archetype": arch_name,
                    "description": arch_info["description"],
                    "keywords": arch_info["keywords"],
                })

        return {
            "character": character,
            "total_builds": len(builds),
            "covered_archetypes": {
                k: {
                    "builds": v,
                    "description": ARCHETYPES[k]["description"],
                }
                for k, v in covered.items()
            },
            "uncovered_archetypes": uncovered,
            "coverage_pct": len(covered) / len(ARCHETYPES) * 100,
        }

    def cross_character_comparison(self) -> Dict:
        """Compare build quality and coverage across all characters."""
        results = {}

        for char_name in self.loader.character_names:
            builds = self.loader.builds_for(char_name)
            if not builds:
                continue

            scores = [self.unified_score(b)["total"] for b in builds]
            gap = self.gap_analysis(char_name)

            results[char_name] = {
                "build_count": len(builds),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "archetype_coverage": gap.get("coverage_pct", 0),
                "uncovered_count": len(gap.get("uncovered_archetypes", [])),
            }

        return results

    def essence_meta_report(self) -> Dict:
        """
        Analyze essence usage across all builds to identify meta trends,
        overused/underused essences, and balance insights.
        """
        usage: Dict[str, int] = {}
        cooccurrence: Dict[Tuple[str, str], int] = {}

        for builds in self.loader.builds.values():
            for build in builds:
                build_essences = set()
                for m in build.get("memories", []):
                    for e in m.get("essences", []):
                        usage[e] = usage.get(e, 0) + 1
                        build_essences.add(e)

                # Track which essences appear together
                sorted_ess = sorted(build_essences)
                for i, e1 in enumerate(sorted_ess):
                    for e2 in sorted_ess[i + 1:]:
                        pair = (e1, e2)
                        cooccurrence[pair] = cooccurrence.get(pair, 0) + 1

        total_builds = sum(len(b) for b in self.loader.builds.values())
        all_essence_names = {e["name"] for e in self.loader.essences}

        # Most used
        sorted_usage = sorted(usage.items(), key=lambda x: x[1], reverse=True)

        # Unused
        unused = sorted(all_essence_names - set(usage.keys()))

        # Most common pairs (emergent synergies)
        sorted_pairs = sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)

        # Usage by rarity
        rarity_usage: Dict[str, Dict[str, int]] = {}
        for ess_name, count in usage.items():
            rarity = self.loader.essence_rarity_map.get(ess_name, "Unknown")
            if rarity not in rarity_usage:
                rarity_usage[rarity] = {"used": 0, "total_uses": 0}
            rarity_usage[rarity]["used"] += 1
            rarity_usage[rarity]["total_uses"] += count

        return {
            "total_builds": total_builds,
            "total_essences": len(all_essence_names),
            "used_essences": len(usage),
            "unused_essences": unused,
            "most_used": sorted_usage[:15],
            "least_used": [
                (name, count) for name, count in sorted_usage
                if count <= 2
            ],
            "most_common_pairs": [
                {"pair": list(pair), "count": count}
                for pair, count in sorted_pairs[:10]
            ],
            "usage_by_rarity": rarity_usage,
        }

    def build_scorecard(self, character: str, build_name: str) -> Optional[Dict]:
        """
        Generate a comprehensive scorecard for a specific build.
        Combines unified score, synergy details, archetype classification,
        and improvement suggestions.
        """
        builds = self.loader.builds_for(character)
        target = None
        for b in builds:
            if build_name.lower() in b.get("name", "").lower():
                target = b
                break

        if not target:
            return None

        score = self.unified_score(target)

        # Classify archetype
        archetypes = []
        build_text = " ".join([
            target.get("name", ""),
            target.get("concept", ""),
            target.get("playstyle", ""),
        ]).lower()
        for arch_name, arch_info in ARCHETYPES.items():
            matches = sum(1 for kw in arch_info["keywords"] if kw in build_text)
            if matches >= 2:
                archetypes.append(arch_name)

        # Find potential improvements
        improvements = []
        dup = validate_no_duplicate_essences(target)
        if not dup["valid"]:
            improvements.append(
                f"Fix duplicate essences: {', '.join(dup['duplicates'])}"
            )
        if score["synergy"] < 20:
            improvements.append(
                "Low synergy score - consider swapping essences for known synergy pairs"
            )
        if score["rarity"] < 10:
            improvements.append(
                "Few high-rarity essences - try incorporating Legendary/Epic essences"
            )
        if not (target.get("constellation_tree") or target.get("astrology_tree")):
            improvements.append("Missing constellation tree configuration")

        return {
            "character": character,
            "build": target.get("name", "Unknown"),
            "score": score,
            "grade": self._score_to_grade(score["total"]),
            "archetypes": archetypes,
            "improvements": improvements,
            "essence_count": dup["total_essences"],
            "memory_count": len(target.get("memories", [])),
        }

    @staticmethod
    def _score_to_grade(score: int) -> str:
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 35:
            return "D"
        return "F"
