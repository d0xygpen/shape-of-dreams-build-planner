"""
Synergy Analyzer for Shape of Dreams Builds

Analyzes synergies between Memories, Essences, and Character abilities
to identify optimal build combinations. Uses shared modules.
"""

from typing import List, Dict, Set, Optional

try:
    from analysis.data_loader import DataLoader, get_loader
    from analysis.validators import validate_no_duplicate_essences
    from analysis.synergies import (
        SYNERGY_CATEGORIES,
        ESSENCE_SYNERGIES,
        get_synergy_for_pair,
        find_all_synergies_in_set,
    )
except ImportError:
    from data_loader import DataLoader, get_loader
    from validators import validate_no_duplicate_essences
    from synergies import (
        SYNERGY_CATEGORIES,
        ESSENCE_SYNERGIES,
        get_synergy_for_pair,
        find_all_synergies_in_set,
    )


class SynergyAnalyzer:
    def __init__(self, loader: Optional[DataLoader] = None):
        self.loader = loader or get_loader()
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build lookup tables for synergy type matching."""
        self.essence_synergy_types: Dict[str, Set[str]] = {
            e["name"]: set(e.get("synergy_types", [])) for e in self.loader.essences
        }
        self.memory_keywords: Dict[str, Set[str]] = {
            m["name"]: set(m.get("synergy_keywords", [])) for m in self.loader.memories
        }

    def find_synergies(self, memory_name: str, essence_names: List[str]) -> Dict:
        """
        Analyze synergies between a Memory and its Essences.
        Returns synergy scores and detailed explanations.
        """
        memory = self.loader.memory_by_name.get(memory_name)
        if not memory:
            return {"error": f"Memory '{memory_name}' not found"}

        essences = [self.loader.essence_by_name.get(name) for name in essence_names]
        essences = [e for e in essences if e is not None]

        synergy_score = 0
        synergy_details = []
        essence_essence_synergies = []

        memory_kw = self.memory_keywords.get(memory_name, set())

        # Memory-Essence synergies
        for essence in essences:
            essence_types = self.essence_synergy_types.get(essence["name"], set())
            matches = memory_kw.intersection(essence_types)
            if matches:
                synergy_score += len(matches) * 10
                synergy_details.append({
                    "essence": essence["name"],
                    "matches": list(matches),
                    "synergy": "high",
                })
            else:
                synergy_details.append({
                    "essence": essence["name"],
                    "matches": [],
                    "synergy": "low",
                })

        # Essence-Essence synergies (check all pairs)
        for i, e1 in enumerate(essence_names):
            for e2 in essence_names[i + 1:]:
                info = get_synergy_for_pair(e1, e2)
                if info:
                    synergy_score += info["score"]
                    essence_essence_synergies.append({
                        "pair": [e1, e2],
                        "score": info["score"],
                        "description": info["description"],
                    })

        # Category overlap bonus
        essence_type_sets = [
            self.essence_synergy_types.get(name, set()) for name in essence_names
        ]
        for category, types in SYNERGY_CATEGORIES.items():
            types_set = set(types)
            count = sum(1 for ets in essence_type_sets if ets.intersection(types_set))
            if count >= 2:
                synergy_score += 5 * (count - 1)

        return {
            "memory": memory_name,
            "essences": essence_names,
            "synergy_score": synergy_score,
            "memory_essence_details": synergy_details,
            "essence_essence_synergies": essence_essence_synergies,
        }

    def analyze_cross_memory_synergies(self, memories: List[Dict]) -> Dict:
        """
        Analyze synergies between essences across different memories.
        Catches powerful combinations that span the entire build.
        """
        all_essences = self._collect_essences(memories)
        found = find_all_synergies_in_set(set(all_essences))
        total_score = sum(s["score"] for s in found)

        return {
            "cross_memory_synergies": found,
            "cross_memory_score": total_score,
        }

    def evaluate_build(
        self,
        character_name: str,
        memories: List[Dict],
        astrology_path: str,
    ) -> Dict:
        """
        Evaluate a complete build for a character.
        memories: List of dicts with "name" and "essences" keys.
        """
        character = self.loader.character_by_name.get(character_name)
        if not character:
            return {"error": f"Character '{character_name}' not found"}

        validation = validate_no_duplicate_essences({"memories": memories})

        total_synergy = 0
        analysis = {
            "character": character_name,
            "memories": [],
            "astrology_path": astrology_path,
            "overall_score": 0,
            "validation": validation,
            "strengths": [],
            "weaknesses": [],
            "cross_memory_synergies": [],
        }

        if not validation["valid"]:
            analysis["weaknesses"].append(
                f"INVALID: Duplicate essences: {', '.join(validation['duplicates'])}"
            )

        for mem_config in memories:
            memory_name = mem_config["name"]
            essences = mem_config.get("essences", [])
            synergy = self.find_synergies(memory_name, essences)
            mem_score = synergy.get("synergy_score", 0)
            total_synergy += mem_score

            analysis["memories"].append({
                "memory": memory_name,
                "essences": essences,
                "synergy_score": mem_score,
                "essence_synergies": synergy.get("essence_essence_synergies", []),
            })

        # Cross-memory synergies
        cross = self.analyze_cross_memory_synergies(memories)
        analysis["cross_memory_synergies"] = cross["cross_memory_synergies"]
        total_synergy += cross["cross_memory_score"]

        analysis["overall_score"] = total_synergy

        # Strengths / weaknesses based on score
        if total_synergy > 150:
            analysis["strengths"].append("Exceptional synergy between components")
        elif total_synergy > 100:
            analysis["strengths"].append("High synergy between components")
        elif total_synergy > 50:
            analysis["strengths"].append("Good synergy between components")

        if astrology_path.lower() in ["destruction", "life"]:
            analysis["strengths"].append(f"Focused {astrology_path} path")

        # Legendary count
        all_essences = self._collect_essences(memories)
        legendary = sum(
            1 for e in all_essences
            if self.loader.essence_rarity_map.get(e) == "Legendary"
        )
        if legendary >= 3:
            analysis["strengths"].append(
                f"High-power build with {legendary} Legendary essences"
            )
        elif legendary == 0:
            analysis["weaknesses"].append(
                "No Legendary essences - may lack late-game power"
            )

        return analysis

    def suggest_essence_upgrades(
        self, memory_name: str, current_essences: List[str]
    ) -> List[Dict]:
        """Suggest better essence combinations for a memory based on synergy potential."""
        memory = self.loader.memory_by_name.get(memory_name)
        if not memory:
            return []

        memory_kw = self.memory_keywords.get(memory_name, set())
        suggestions = []

        for essence in self.loader.essences:
            if essence["name"] in current_essences:
                continue

            essence_types = self.essence_synergy_types.get(essence["name"], set())
            matches = memory_kw.intersection(essence_types)

            if matches:
                synergy_with_current = 0
                for current in current_essences:
                    info = get_synergy_for_pair(essence["name"], current)
                    if info:
                        synergy_with_current += info["score"]

                suggestions.append({
                    "essence": essence["name"],
                    "rarity": essence["rarity"],
                    "matching_keywords": list(matches),
                    "synergy_with_current": synergy_with_current,
                    "total_score": len(matches) * 10 + synergy_with_current,
                })

        suggestions.sort(key=lambda x: x["total_score"], reverse=True)
        return suggestions[:5]

    def suggest_substitutes(self, essence_name: str) -> List[Dict]:
        """
        Suggest replacement essences that fill a similar role.
        Useful when a recommended essence isn't available.
        """
        original = self.loader.essence_by_name.get(essence_name)
        if not original:
            return []

        original_types = set(original.get("synergy_types", []))
        original_rarity = original.get("rarity", "Common")
        if not original_types:
            return []

        candidates = []
        for essence in self.loader.essences:
            if essence["name"] == essence_name:
                continue
            ess_types = set(essence.get("synergy_types", []))
            overlap = original_types.intersection(ess_types)
            if overlap:
                # Prefer same or adjacent rarity
                rarity_match = 1 if essence["rarity"] == original_rarity else 0
                candidates.append({
                    "essence": essence["name"],
                    "rarity": essence["rarity"],
                    "shared_types": list(overlap),
                    "overlap_score": len(overlap),
                    "rarity_match": rarity_match,
                    "total_score": len(overlap) * 10 + rarity_match * 5,
                })

        candidates.sort(key=lambda x: x["total_score"], reverse=True)
        return candidates[:5]

    @staticmethod
    def _collect_essences(memories: List[Dict]) -> List[str]:
        """Collect all essence names from a list of memory configs."""
        essences = []
        for memory in memories:
            essences.extend(memory.get("essences", []))
        return essences
