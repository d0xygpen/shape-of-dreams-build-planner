"""
Unified Synergy Definitions for Shape of Dreams ARPG Builds

Single source of truth for all synergy pairs, categories, and scoring.
Used by both build_comparator.py and synergy_analyzer.py.
"""

from typing import Dict, FrozenSet, List, Set, Tuple


# ── Synergy Categories ─────────────────────────────────────────────────
# Maps high-level synergy categories to the synergy_type tags used in essences.json

SYNERGY_CATEGORIES: Dict[str, List[str]] = {
    "damage_conversion": ["fire_damage", "cold_damage", "light_damage", "dark_damage", "damage_conversion"],
    "healing": ["healing", "defense"],
    "cooldown": ["cooldown_reduction"],
    "critical": ["critical_strike"],
    "scaling": ["scaling"],
    "automation": ["automation"],
    "mobility": ["mobility", "attack_speed"],
    "summon": ["summon"],
    "projectile": ["projectile"],
}


# ── Known Powerful Synergy Pairs ───────────────────────────────────────
# Each entry: (essence_a, essence_b) -> { score, description }
# Order within tuple doesn't matter - lookups check both orderings.

ESSENCE_SYNERGIES: Dict[Tuple[str, str], Dict] = {
    # ── Original 10 Pairs ─────────────────────────────────────────────
    ("Glacial Core", "Essence of Clemency"): {
        "score": 25,
        "description": "Healing-to-damage conversion loop: Clemency heals from damage, Glacial Core converts healing to cold damage",
    },
    ("Divine Faith", "Essence of Domination"): {
        "score": 22,
        "description": "Dual infinite scaling: Faith scales with kills, Domination scales with crits",
    },
    ("Essence of Paranoia", "Essence of Momentum"): {
        "score": 20,
        "description": "Auto-cast on damage + cooldown reduction per attack = near-permanent uptime",
    },
    ("Essence of Twilight", "Essence of the Abyss"): {
        "score": 20,
        "description": "Dark stack synergy: Abyss converts to dark, Twilight consumes stacks for massive damage",
    },
    ("Eternal Flame", "Eye of the Sun"): {
        "score": 20,
        "description": "Fire synergy: Eternal Flame applies burn stacks, Eye of the Sun enhances burning enemies",
    },
    ("Essence of Domination", "Essence of Fangs"): {
        "score": 18,
        "description": "Crit scaling: Fangs guarantees crits, Domination scales crit damage infinitely",
    },
    ("Essence of Insight", "Essence of Flow"): {
        "score": 18,
        "description": "Light damage cooldown loop: Both reduce cooldowns when dealing light damage",
    },
    ("Perfection", "Divine Faith"): {
        "score": 18,
        "description": "Universal scaling: Perfection provides base stats, Faith scales everything with kills",
    },
    ("Essence of Fever", "Essence of Sulfur"): {
        "score": 15,
        "description": "Fire DoT amplification: Sulfur converts to fire and boosts DoT, Fever creates scaling explosions",
    },
    ("Essence of Momentum", "Essence of Efficiency"): {
        "score": 15,
        "description": "Cooldown stacking: Attack-based reduction + flat haste for minimal downtime",
    },
    # ── Newly Discovered Fire Pairs ───────────────────────────────────
    ("Eternal Flame", "Essence of Fever"): {
        "score": 22,
        "description": "Chain explosion loop: Eternal Flame stacks burns, Fever detonates fire enemies with scaling AoE, explosions re-trigger burns",
    },
    ("Eternal Flame", "Essence of Sulfur"): {
        "score": 20,
        "description": "Full fire conversion: Sulfur converts all damage to Fire + 50% DoT boost, every hit triggers Eternal Flame burn stacking",
    },
    ("Embertail", "Eye of the Sun"): {
        "score": 20,
        "description": "Fire spread + mass detonation: Embertail ricochets fire to all enemies, Eye of the Sun detonates all burning targets for 360% damage",
    },
    ("Embertail", "Eternal Flame"): {
        "score": 20,
        "description": "Ricochet burn spread: Embertail ricochets fire hits, each triggering Eternal Flame burn stacks across the battlefield",
    },
    ("Eternal Flame", "Essence of Charcoal"): {
        "score": 18,
        "description": "Guaranteed burn bonus: Eternal Flame ensures targets are burning, Charcoal deals 100% Fire damage to burning targets (vs 60%)",
    },
    ("Embertail", "Essence of Fever"): {
        "score": 15,
        "description": "Fire spread + chain explosion: Embertail spreads fire everywhere, Fever detonates all burning enemies in chain explosions",
    },
    # ── Newly Discovered Dark Pairs ───────────────────────────────────
    ("Essence of Twilight", "Essence of Obsidian"): {
        "score": 16,
        "description": "Dark burst combo: Obsidian empowers next attack for 250% Dark damage + 1s CDR, Twilight stacks and consumes darkness",
    },
    ("Essence of Twilight", "Essence of Dusk"): {
        "score": 16,
        "description": "Dark stack amplification: Dusk fires 2 dark shards per attack, rapidly building stacks for Twilight's burst consumption",
    },
    ("Essence of Twilight", "Essence of the Starry Sky"): {
        "score": 16,
        "description": "Dark attack speed loop: Twilight converts attacks to Dark, Starry Sky grants up to 40% attack speed on Dark damage",
    },
    # ── Newly Discovered Crit Pairs ───────────────────────────────────
    ("Essence of Crimson", "Essence of Fangs"): {
        "score": 18,
        "description": "Aligned 4th-attack procs: Both trigger every 4th attack, Fangs guarantees crits that enlarge Crimson explosions",
    },
    ("Essence of Crimson", "Essence of Domination"): {
        "score": 18,
        "description": "Crit scaling + AoE: Domination's +20% Crit enlarges Crimson explosions, Crimson's procs feed Domination's infinite crit stacking",
    },
    ("Essence of Domination", "Essence of Composure"): {
        "score": 15,
        "description": "Crit chance stacking: Composure gives +30% Crit on cast + Domination's +20% = 50%+ Crit feeding infinite scaling",
    },
    ("Essence of Domination", "Essence of Umbra"): {
        "score": 15,
        "description": "Crit-scaling damage: Umbra scales by 42% of Crit Chance, Domination provides +20% Crit and infinite Crit Damage",
    },
    ("Perfection", "Essence of Fangs"): {
        "score": 14,
        "description": "Stat synergy: Perfection's +6% Crit + 10% AS + 10 Haste enhances Fangs' crit proc rate and cooldown reduction",
    },
    # ── Newly Discovered Cold/Healing Pairs ───────────────────────────
    ("Glacial Core", "Essence of Frost"): {
        "score": 18,
        "description": "Infinite HP scaling: Frost permanently gains Max HP, increasing its cold damage, which feeds Glacial Core's healing-to-damage loop",
    },
    ("Glacial Core", "Essence of Freezing"): {
        "score": 14,
        "description": "Cold feedback loop: Freezing's cold damage triggers Glacial Core's boosted 7.2% healing, converting back to cold shards",
    },
    ("Glacial Core", "Essence of Bleakness"): {
        "score": 14,
        "description": "Cold damage amplification: Glacial Core's ice shards apply Cold status, Bleakness deals 50% more damage to Cold-affected enemies",
    },
    # ── Newly Discovered Light Pairs ──────────────────────────────────
    ("Essence of Thunder", "Essence of Flow"): {
        "score": 16,
        "description": "Light damage CDR: Thunder's Light damage per stack triggers Flow's 6% cooldown reduction per Light hit",
    },
    ("Essence of Thunder", "Essence of Insight"): {
        "score": 16,
        "description": "Light burst + haste: Thunder consumes stacks for Light damage, Insight adds 200% bonus Light damage + 20 Memory Haste",
    },
    ("Pure White", "Essence of Shock"): {
        "score": 16,
        "description": "Light stacking: Pure White fires more projectiles per Light stack, Shock bounces Lightning adding Light stacks to multiple enemies",
    },
    ("Pure White", "Essence of Flow"): {
        "score": 15,
        "description": "Light projectile CDR: Pure White's multiple Light projectiles each trigger Flow's 6% cooldown reduction",
    },
    # ── Newly Discovered Automation/Retaliation Pairs ─────────────────
    ("Essence of Paranoia", "Essence of Vengeance"): {
        "score": 18,
        "description": "Damage-reactive retaliation: Both trigger on taking damage, Vengeance adds +34% damage buff amplifying Paranoia's auto-casts",
    },
    ("Essence of Paranoia", "Essence of Panic"): {
        "score": 15,
        "description": "Damage-reactive haste: Both trigger on hit, Panic grants 30 Haste + 20% movement speed stacking with Paranoia's auto-cast",
    },
    # ── Newly Discovered Scaling/Utility Pairs ────────────────────────
    ("Essence of Direness", "Essence of Overload"): {
        "score": 16,
        "description": "Low-HP symbiosis: Overload sacrifices 20% HP to gain 45% damage, pushing into Direness' below-30% threshold for 55% CDR",
    },
    ("Essence of the Giant", "Essence of Frost"): {
        "score": 15,
        "description": "HP scaling synergy: Giant gives +260 HP and 1% damage per 50 HP, Frost permanently gains HP making Giant scale higher",
    },
    ("Essence of Finality", "Essence of Inversion"): {
        "score": 13,
        "description": "Extended cooldown payoff: Inversion's +15% cooldown means more Finality stacks (5% damage each) plus Inversion's own +20% damage",
    },
}

# Single-essence synergies (essences that are powerful on their own)
SOLO_ESSENCE_SCORES: Dict[str, int] = {
    "Essence of Paranoia": 15,  # Provides automation + retaliation
    "Essence of Pain": 12,      # 40% AoE splash on ALL damage, universal value
    "Perfection": 12,           # +7 AD/AP, +35 HP, +10% AS, +6% Crit, +10 Haste - universal stat stick
}

# Pre-computed frozenset lookup for O(1) pair checking
_SYNERGY_FROZENSET_MAP: Dict[FrozenSet[str], Dict] = {
    frozenset(pair): info for pair, info in ESSENCE_SYNERGIES.items()
}

# Pre-computed frozenset scores (compatible with old BuildComparator format)
_SYNERGY_PAIR_SCORES: Dict[FrozenSet[str], int] = {
    frozenset(pair): info["score"] for pair, info in ESSENCE_SYNERGIES.items()
}
# Add solo essences
for name, score in SOLO_ESSENCE_SCORES.items():
    _SYNERGY_PAIR_SCORES[frozenset([name])] = score


def get_synergy_for_pair(essence_a: str, essence_b: str) -> Dict:
    """Look up synergy info for a pair of essences (order-independent)."""
    key = frozenset([essence_a, essence_b])
    return _SYNERGY_FROZENSET_MAP.get(key, {})


def get_pair_score(essence_a: str, essence_b: str) -> int:
    """Get the synergy score for a pair of essences."""
    info = get_synergy_for_pair(essence_a, essence_b)
    return info.get("score", 0)


def score_essence_set(essences: Set[str]) -> int:
    """
    Calculate total synergy score for a set of essences.
    Checks all known synergy pairs (including solo essences).
    """
    total = 0
    for synergy_set, score in _SYNERGY_PAIR_SCORES.items():
        if synergy_set.issubset(essences):
            total += score
    return total


def find_all_synergies_in_set(essences: Set[str]) -> List[Dict]:
    """
    Find all synergy pairs present in a set of essences.
    Returns list of {pair, score, description} dicts.
    """
    found = []
    for (e1, e2), info in ESSENCE_SYNERGIES.items():
        if e1 in essences and e2 in essences:
            found.append({
                "pair": [e1, e2],
                "score": info["score"],
                "description": info["description"],
            })
    # Solo synergies
    for name, score in SOLO_ESSENCE_SCORES.items():
        if name in essences:
            found.append({
                "pair": [name],
                "score": score,
                "description": f"{name} provides standalone value",
            })
    return found


def get_category_for_types(synergy_types: Set[str]) -> List[str]:
    """Given a set of synergy_types from an essence, return matching categories."""
    matched = []
    for category, types in SYNERGY_CATEGORIES.items():
        if synergy_types.intersection(types):
            matched.append(category)
    return matched
