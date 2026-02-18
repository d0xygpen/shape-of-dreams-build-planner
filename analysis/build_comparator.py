"""
Build Comparator for Shape of Dreams

Compares different builds and provides recommendations based on playstyle preferences.
Uses shared DataLoader, validators, and synergy definitions.
"""

from typing import List, Dict, Optional, Set

try:
    from analysis.data_loader import DataLoader, get_loader
    from analysis.validators import validate_no_duplicate_essences
    from analysis.synergies import (
        score_essence_set,
        find_all_synergies_in_set,
        _SYNERGY_PAIR_SCORES,
    )
except ImportError:
    from data_loader import DataLoader, get_loader
    from validators import validate_no_duplicate_essences
    from synergies import (
        score_essence_set,
        find_all_synergies_in_set,
        _SYNERGY_PAIR_SCORES,
    )

# Extended playstyle keywords for recommendation matching
PLAYSTYLE_KEYWORDS: Dict[str, List[str]] = {
    "aggressive": ["damage", "offensive", "burst", "execution", "assassin", "dps"],
    "defensive": ["tank", "shield", "defense", "survivability", "guardian", "protection"],
    "support": ["heal", "support", "ally", "buff", "healer"],
    "mobile": ["mobility", "movement", "speed", "dash", "agile"],
    "automated": ["automated", "paranoia", "auto", "passive", "retaliation"],
}


class BuildComparator:
    def __init__(self, loader: Optional[DataLoader] = None):
        self.loader = loader or get_loader()

    def compare_builds(self, character: str) -> Dict:
        """Compare all builds for a character."""
        builds = self.loader.builds_for(character)
        if not builds:
            return {
                "error": f"Character '{character}' not found. Available: {self.loader.character_names}"
            }

        comparison = {
            "character": character.lower(),
            "builds": [],
        }

        for build in builds:
            validation = validate_no_duplicate_essences(build)
            build_info = {
                "name": build["name"],
                "playstyle": build.get("playstyle", "N/A"),
                "complexity": self._calculate_complexity(build),
                "synergy_score": self._count_synergies(build),
                "synergy_details": self._get_synergy_details(build),
                "essence_rarity": self.loader.count_rarity(build),
                "validation": validation,
                "strengths": build.get("strengths", []),
                "weaknesses": build.get("weaknesses", []),
            }
            comparison["builds"].append(build_info)

        comparison["builds"].sort(key=lambda x: x["synergy_score"], reverse=True)
        return comparison

    def _calculate_complexity(self, build: Dict) -> str:
        """Calculate build complexity based on number of systems used."""
        memory_count = len(build.get("memories", []))
        total_essences = sum(
            len(m.get("essences", [])) for m in build.get("memories", [])
        )
        has_passive = len(build.get("passive_essences", [])) > 0
        has_constellation = (
            build.get("constellation_tree") is not None
            or build.get("astrology_tree") is not None
        )

        score = memory_count + (total_essences // 3)
        if has_passive:
            score += 1
        if has_constellation:
            score += 1

        if score >= 8:
            return "High"
        elif score >= 5:
            return "Medium"
        return "Low"

    def _count_synergies(self, build: Dict) -> int:
        """Calculate weighted synergy score for a build."""
        all_essences: Set[str] = set()
        for memory in build.get("memories", []):
            all_essences.update(memory.get("essences", []))

        score = score_essence_set(all_essences)

        # Half score for passive essence synergies
        passive_essences = {
            e.get("name", "") for e in build.get("passive_essences", [])
        }
        for passive in passive_essences:
            for active in all_essences:
                key = frozenset([passive, active])
                if key in _SYNERGY_PAIR_SCORES:
                    score += _SYNERGY_PAIR_SCORES[key] // 2

        return score

    def _get_synergy_details(self, build: Dict) -> List[Dict]:
        """Get detailed synergy breakdown for a build."""
        all_essences: Set[str] = set()
        for memory in build.get("memories", []):
            all_essences.update(memory.get("essences", []))
        return find_all_synergies_in_set(all_essences)

    def recommend_build(self, character: str, preferences: Dict) -> Dict:
        """
        Recommend a build based on preferences.

        preferences: {
            "playstyle": "aggressive" | "defensive" | "support" | "mobile" | "automated",
            "complexity": "low" | "medium" | "high" | "any",
            "focus": "damage" | "survivability" | "utility" | "scaling"
        }
        """
        builds = self.loader.builds_for(character)
        if not builds:
            return {
                "error": f"Character '{character}' not found. Available: {self.loader.character_names}"
            }

        scores = []

        for build in builds:
            score = 0

            # Playstyle matching
            playstyle = preferences.get("playstyle", "").lower()
            if playstyle in PLAYSTYLE_KEYWORDS:
                search_text = (
                    f"{build.get('playstyle', '')} {build.get('concept', '')} "
                    f"{build.get('name', '')}"
                ).lower()
                for keyword in PLAYSTYLE_KEYWORDS[playstyle]:
                    if keyword in search_text:
                        score += 10

            # Complexity matching
            complexity = self._calculate_complexity(build)
            preferred = preferences.get("complexity", "").lower()
            if complexity.lower() == preferred:
                score += 5
            elif preferred == "any":
                score += 2

            # Focus matching
            focus = preferences.get("focus", "").lower()
            focus_text = (
                f"{build.get('concept', '')} {build.get('strategy', '')}"
            ).lower()

            focus_keywords = {
                "damage": ["damage", "dps", "burst", "execution"],
                "survivability": ["tank", "defense", "health", "healing", "sustain"],
                "utility": ["support", "summon", "buff", "utility"],
                "scaling": ["scaling", "infinite", "faith", "domination", "stacks"],
            }
            if focus in focus_keywords:
                for kw in focus_keywords[focus]:
                    if kw in focus_text:
                        score += 10

            # Synergy bonus
            synergy_score = self._count_synergies(build)
            score += synergy_score // 5

            # Legendary bonus
            rarity = self.loader.count_rarity(build)
            score += rarity.get("Legendary", 0) * 3

            scores.append({
                "build": build["name"],
                "score": score,
                "synergy_score": synergy_score,
                "complexity": complexity,
                "essence_rarity": rarity,
                "build_data": build,
            })

        scores.sort(key=lambda x: x["score"], reverse=True)

        return {
            "character": character.lower(),
            "preferences": preferences,
            "recommendations": scores,
            "top_recommendation": scores[0] if scores else None,
        }

    def get_all_builds_summary(self) -> Dict:
        """Get a summary of all builds across all characters."""
        summary = {
            "total_builds": 0,
            "characters": {},
            "top_synergy_builds": [],
        }

        all_scored = []
        for character, builds in self.loader.builds.items():
            summary["characters"][character] = {
                "build_count": len(builds),
                "builds": [b["name"] for b in builds],
            }
            summary["total_builds"] += len(builds)

            for build in builds:
                synergy_score = self._count_synergies(build)
                all_scored.append({
                    "character": character,
                    "build": build["name"],
                    "synergy_score": synergy_score,
                    "complexity": self._calculate_complexity(build),
                })

        all_scored.sort(key=lambda x: x["synergy_score"], reverse=True)
        summary["top_synergy_builds"] = all_scored[:5]
        return summary

    def find_builds_with_essence(self, essence_name: str) -> List[Dict]:
        """Find all builds that use a specific essence."""
        results = []
        for character, builds in self.loader.builds.items():
            for build in builds:
                for memory in build.get("memories", []):
                    if essence_name in memory.get("essences", []):
                        results.append({
                            "character": character,
                            "build": build["name"],
                            "memory": memory["name"],
                            "other_essences": [
                                e for e in memory.get("essences", []) if e != essence_name
                            ],
                        })
                        break
        return results
