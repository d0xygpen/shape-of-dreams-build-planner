#!/usr/bin/env python3
"""
Shape of Dreams - ARPG Build Viewer & Analyzer

CLI tool for viewing, searching, comparing, and analyzing character builds.

Commands:
  list                           List all builds overview
  character <name>               Show all builds for a character
  build <char> <name>            Show detailed build info
  search <query>                 Search builds by keyword
  synergy <essence>              Find builds using a specific essence
  compare <char>                 Compare all builds for a character
  validate                       Validate all builds for duplicate essences
  recommend <char> [options]     Get build recommendations
  stats                          Show project-wide statistics
  essences [--rarity R]          Browse essences catalog
  memories [--character C]       Browse memories catalog
  substitute <essence>           Find replacement essences
  gaps <char>                    Archetype gap analysis for a character
  scorecard <char> <build>       Detailed build scorecard with grade
  meta                           Essence meta-game report
  reindex                        Regenerate the build index
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Ensure analysis package is importable
sys.path.insert(0, str(Path(__file__).parent))

from analysis.data_loader import DataLoader, get_loader
from analysis.validators import validate_no_duplicate_essences, validate_full_build
from analysis.synergies import find_all_synergies_in_set, score_essence_set
from analysis.build_comparator import BuildComparator
from analysis.synergy_analyzer import SynergyAnalyzer
from analysis.build_analyzer import BuildAnalyzer


# -- Output Formatting --------------------------------------------------

class OutputFormatter:
    """Handles output in table, json, or csv format."""

    def __init__(self, fmt: str = "table"):
        self.fmt = fmt
        self._buffer: List[Dict] = []

    def print_header(self, text: str, width: int = 80):
        if self.fmt == "table":
            print(f"\n{'=' * width}")
            print(text)
            print(f"{'=' * width}")

    def print_separator(self, char: str = "-", width: int = 80):
        if self.fmt == "table":
            print(char * width)

    def print_line(self, text: str):
        if self.fmt == "table":
            print(text)

    def collect(self, record: Dict):
        """Collect a record for batch output (json/csv modes)."""
        self._buffer.append(record)

    def flush(self):
        """Output all collected records in the chosen format."""
        if self.fmt == "json":
            print(json.dumps(self._buffer, indent=2))
        elif self.fmt == "csv" and self._buffer:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=self._buffer[0].keys())
            writer.writeheader()
            writer.writerows(self._buffer)
            print(output.getvalue())
        self._buffer.clear()


# -- Build Display ------------------------------------------------------

def print_build_summary(
    build: Dict, char_name: str, loader: DataLoader, out: OutputFormatter
):
    """Print a concise summary of a build."""
    if out.fmt != "table":
        out.collect({
            "character": char_name,
            "name": build.get("name", "Unknown"),
            "concept": build.get("concept", ""),
            "playstyle": build.get("playstyle", ""),
            "memories": [
                {
                    "name": m.get("name", ""),
                    "essences": [
                        {"name": e, "rarity": loader.essence_rarity_map.get(e, "?")}
                        for e in m.get("essences", [])
                    ],
                }
                for m in build.get("memories", [])
            ],
            "strengths": build.get("strengths", []),
            "weaknesses": build.get("weaknesses", []),
        })
        return

    out.print_header(
        f"Character: {char_name.upper()}\nBuild: {build.get('name', 'Unknown')}"
    )

    # Validation
    dup_check = validate_no_duplicate_essences(build)
    if not dup_check["valid"]:
        print(f"(!)  VALIDATION ERROR: Duplicate essences: {', '.join(dup_check['duplicates'])}")
        print(f"     (Game rule: Each essence can only be used once per build)")
        print()

    print(f"Concept: {build.get('concept', 'N/A')}")
    print(f"Playstyle: {build.get('playstyle', 'N/A')}")

    # Rarity summary
    rarity = loader.count_rarity(build)
    rarity_str = ", ".join(f"{v} {k}" for k, v in rarity.items() if v > 0)
    if rarity_str:
        print(f"Essence Rarity: {rarity_str}")

    # Synergy score
    all_ess = set()
    for m in build.get("memories", []):
        all_ess.update(m.get("essences", []))
    syn_score = score_essence_set(all_ess)
    if syn_score > 0:
        print(f"Synergy Score: {syn_score}")

    # Memories
    memories = build.get("memories", [])
    print(f"\nMemories ({len(memories)} active):")
    for i, memory in enumerate(memories, 1):
        print(f"  {i}. {memory.get('name', 'Unknown')}")
        for ess in memory.get("essences", []):
            symbol = loader.get_rarity_symbol(ess)
            print(f"     {symbol} {ess}")

    # Passive essences
    if build.get("passive_essences"):
        print(f"\nPassive Essences:")
        for ess in build["passive_essences"]:
            ess_name = ess.get("name", "Unknown") if isinstance(ess, dict) else ess
            symbol = loader.get_rarity_symbol(ess_name)
            print(f"  {symbol} {ess_name}")

    # Tree (supports both naming conventions)
    tree = build.get("constellation_tree") or build.get("astrology_tree")
    if isinstance(tree, dict) and tree.get("primary"):
        print(f"\nConstellation Tree: {tree.get('primary', 'N/A')} (primary) / {tree.get('secondary', 'N/A')} (secondary)")
        if tree.get("focus"):
            print(f"  Focus: {', '.join(str(f) for f in tree['focus'][:4])}")
    elif isinstance(tree, dict):
        print(f"\nConstellation Tree:")
        for category, powers in tree.items():
            if isinstance(powers, list) and powers:
                display = ", ".join(str(p)[:30] for p in powers[:3])
                print(f"  {category.capitalize()}: {display}...")

    # Strengths / weaknesses
    print(f"\nKey Strengths:")
    for s in build.get("strengths", [])[:5]:
        print(f"  [OK] {s}")
    print(f"\nKey Weaknesses:")
    for w in build.get("weaknesses", [])[:3]:
        print(f"  [-] {w}")


# -- CLI Commands -------------------------------------------------------

def cmd_list(loader: DataLoader, out: OutputFormatter, **_):
    """List all builds with overview."""
    out.print_header("ALL CHARACTER BUILDS OVERVIEW")

    total = 0
    invalid = 0

    for char_name, builds in sorted(loader.builds.items()):
        out.print_line(f"\n{char_name.upper()}: {len(builds)} builds")
        total += len(builds)

        for i, build in enumerate(builds, 1):
            tags = []
            name = build.get("name", "")

            if "Basic Attack" in name:
                tags.append("BASIC ATK")
            if "Maximum Damage" in name or "Max Damage" in name:
                tags.append("MAX DMG")
            if "Automated" in name or "Paranoia" in name:
                tags.append("AUTO")
            if "Divine" in name or "Faith" in name:
                tags.append("SCALING")

            # Legendary count
            rarity = loader.count_rarity(build)
            leg = rarity.get("Legendary", 0)
            if leg >= 3:
                tags.append(f"{leg}L")

            # Synergy score
            all_ess = set()
            for m in build.get("memories", []):
                all_ess.update(m.get("essences", []))
            syn = score_essence_set(all_ess)
            if syn > 0:
                tags.append(f"S:{syn}")

            # Validation
            dup = validate_no_duplicate_essences(build)
            if not dup["valid"]:
                tags.append("!INVALID")
                invalid += 1

            tags_str = f" [{', '.join(tags)}]" if tags else ""
            out.print_line(f"  {i}. {name}{tags_str}")

            if out.fmt != "table":
                out.collect({
                    "character": char_name,
                    "build": name,
                    "tags": tags,
                    "synergy_score": syn,
                    "legendary_count": leg,
                    "valid": dup["valid"],
                })

    out.print_separator("=")
    out.print_line(f"Total: {total} builds across {len(loader.builds)} characters")
    if invalid > 0:
        out.print_line(f"(!)  {invalid} builds have validation errors")

    if out.fmt != "table":
        out.flush()


def cmd_character(loader: DataLoader, out: OutputFormatter, character: str, **_):
    """Show all builds for a character."""
    builds = loader.builds_for(character)
    if not builds:
        print(f"\nNo builds found for character: {character}")
        print(f"\nAvailable characters:")
        for name in loader.character_names:
            print(f"  - {name}")
        return

    char_key = character.lower()
    out.print_header(f"{char_key.upper()} - {len(builds)} BUILDS")

    for i, build in enumerate(builds, 1):
        print_build_summary(build, char_key, loader, out)
        if i < len(builds) and out.fmt == "table":
            out.print_separator()

    if out.fmt != "table":
        out.flush()


def cmd_build(loader: DataLoader, out: OutputFormatter, character: str, name: str, **_):
    """Show detailed info about a specific build."""
    builds = loader.builds_for(character)
    if not builds:
        print(f"No builds found for character: {character}")
        return

    for build in builds:
        if name.lower() in build.get("name", "").lower():
            print_build_summary(build, character.lower(), loader, out)

            if out.fmt == "table":
                out.print_separator()
                print("STRATEGY:")
                out.print_separator()
                strategy = build.get("strategy", "N/A")
                words = strategy.split()
                line = ""
                for word in words:
                    if len(line) + len(word) + 1 > 78:
                        print(f"  {line}")
                        line = word
                    else:
                        line = f"{line} {word}".strip()
                if line:
                    print(f"  {line}")

                # Show synergy details
                all_ess = set()
                for m in build.get("memories", []):
                    all_ess.update(m.get("essences", []))
                synergies = find_all_synergies_in_set(all_ess)
                if synergies:
                    print(f"\nActive Synergies:")
                    for s in synergies:
                        pair_str = " + ".join(s["pair"])
                        print(f"  [{s['score']}pts] {pair_str}")
                        print(f"         {s['description']}")

            if out.fmt != "table":
                out.flush()
            return

    print(f"Build '{name}' not found for {character}")
    print(f"\nAvailable builds:")
    for b in builds:
        print(f"  - {b.get('name', 'Unknown')}")


def cmd_search(loader: DataLoader, out: OutputFormatter, query: str, **_):
    """Search for builds matching a query."""
    query_lower = query.lower()
    results = []

    for char_name, builds in loader.builds.items():
        for build in builds:
            text_parts = [
                build.get("name", ""),
                build.get("concept", ""),
                build.get("playstyle", ""),
                build.get("strategy", ""),
            ]
            for memory in build.get("memories", []):
                text_parts.extend(memory.get("essences", []))
            search_text = " ".join(text_parts).lower()

            if query_lower in search_text:
                results.append((char_name, build))

    if results:
        out.print_header(f"Found {len(results)} build(s) matching '{query}'")
        for char_name, build in results:
            print_build_summary(build, char_name, loader, out)
        if out.fmt != "table":
            out.flush()
    else:
        print(f"\nNo builds found matching '{query}'")


def cmd_synergy(loader: DataLoader, out: OutputFormatter, essence: str, **_):
    """Find builds using a specific essence."""
    out.print_header(f"BUILDS USING: {essence}")

    found = False
    search_term = essence.lower()

    for char_name, builds in sorted(loader.builds.items()):
        for build in builds:
            for memory in build.get("memories", []):
                matching = [
                    e for e in memory.get("essences", [])
                    if search_term in e.lower()
                ]
                if matching:
                    if out.fmt == "table":
                        print(f"\n{char_name.upper()} - {build.get('name', 'Unknown')}")
                        print(f"  Memory: {memory.get('name', 'Unknown')}")
                        print(f"  Matched: {', '.join(matching)}")
                        others = [e for e in memory.get("essences", []) if search_term not in e.lower()]
                        if others:
                            print(f"  Paired with: {', '.join(others)}")
                    else:
                        out.collect({
                            "character": char_name,
                            "build": build.get("name"),
                            "memory": memory.get("name"),
                            "matched_essences": matching,
                        })
                    found = True
                    break

    if not found:
        print(f"\nNo builds found using '{essence}'")
        print("\nSample essences:")
        for name in list(loader.essence_by_name.keys())[:10]:
            print(f"  - {name}")
    elif out.fmt != "table":
        out.flush()


def cmd_validate(loader: DataLoader, out: OutputFormatter, **_):
    """Validate all builds for issues."""
    out.print_header("BUILD VALIDATION REPORT")

    valid_count = 0
    invalid_count = 0
    warning_count = 0

    for char_name, builds in sorted(loader.builds.items()):
        for build in builds:
            result = validate_full_build(build, loader)
            if result.valid and not result.warnings:
                valid_count += 1
            elif result.valid:
                valid_count += 1
                warning_count += len(result.warnings)
                if out.fmt == "table":
                    print(f"\n[~] {char_name.upper()} - {build.get('name', 'Unknown')}")
                    for w in result.warnings:
                        print(f"    Warning: {w}")
            else:
                invalid_count += 1
                if out.fmt == "table":
                    print(f"\n[X] {char_name.upper()} - {build.get('name', 'Unknown')}")
                    for e in result.errors:
                        print(f"    Error: {e}")
                    for w in result.warnings:
                        print(f"    Warning: {w}")

            if out.fmt != "table":
                out.collect({
                    "character": char_name,
                    "build": build.get("name", "Unknown"),
                    "valid": result.valid,
                    "errors": result.errors,
                    "warnings": result.warnings,
                })

    out.print_separator("=")
    out.print_line(f"Results: {valid_count} valid, {invalid_count} invalid, {warning_count} warnings")
    if invalid_count == 0:
        out.print_line("[OK] All builds pass validation!")

    if out.fmt != "table":
        out.flush()


def cmd_compare(loader: DataLoader, out: OutputFormatter, character: str, **_):
    """Compare all builds for a character using analysis engine."""
    comparator = BuildComparator(loader)
    comparison = comparator.compare_builds(character)

    if "error" in comparison:
        print(f"Error: {comparison['error']}")
        return

    out.print_header(f"BUILD COMPARISON: {comparison['character'].upper()}")

    for build in comparison["builds"]:
        icon = "[OK]" if build["validation"]["valid"] else "(!)"
        if out.fmt == "table":
            print(f"\n{icon} {build['name']}")
            print(f"  Playstyle: {build['playstyle']}")
            print(f"  Synergy Score: {build['synergy_score']}")
            print(f"  Complexity: {build['complexity']}")
            r = build["essence_rarity"]
            print(f"  Essences: {r.get('Legendary', 0)}L / {r.get('Epic', 0)}E / {r.get('Rare', 0)}R / {r.get('Common', 0)}C / {r.get('Unique', 0)}U")
            if build["synergy_details"]:
                print(f"  Synergies:")
                for s in build["synergy_details"]:
                    print(f"    [{s['score']}pts] {' + '.join(s['pair'])}")
            if not build["validation"]["valid"]:
                print(f"  (!) Duplicates: {', '.join(build['validation']['duplicates'])}")
        else:
            out.collect({
                "name": build["name"],
                "synergy_score": build["synergy_score"],
                "complexity": build["complexity"],
                "essence_rarity": build["essence_rarity"],
                "valid": build["validation"]["valid"],
            })

    if out.fmt != "table":
        out.flush()


def cmd_recommend(
    loader: DataLoader,
    out: OutputFormatter,
    character: str,
    playstyle: str = "aggressive",
    focus: str = "damage",
    complexity: str = "any",
    **_,
):
    """Get build recommendations for a character."""
    comparator = BuildComparator(loader)
    result = comparator.recommend_build(character, {
        "playstyle": playstyle,
        "focus": focus,
        "complexity": complexity,
    })

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    out.print_header(
        f"BUILD RECOMMENDATIONS FOR: {character.upper()}\n"
        f"Preferences: playstyle={playstyle}, focus={focus}, complexity={complexity}"
    )

    print("\nTop recommendations (sorted by score):\n")
    for i, rec in enumerate(result["recommendations"][:5], 1):
        r = rec["essence_rarity"]
        if out.fmt == "table":
            print(f"{i}. {rec['build']}")
            print(f"   Score: {rec['score']}  |  Synergy: {rec['synergy_score']}  |  Complexity: {rec['complexity']}")
            print(f"   Essences: {r.get('Legendary', 0)}L / {r.get('Epic', 0)}E / {r.get('Rare', 0)}R")
        else:
            out.collect({
                "rank": i,
                "build": rec["build"],
                "score": rec["score"],
                "synergy_score": rec["synergy_score"],
                "complexity": rec["complexity"],
            })

    if out.fmt != "table":
        out.flush()


def cmd_stats(loader: DataLoader, out: OutputFormatter, **_):
    """Show project-wide statistics."""
    comparator = BuildComparator(loader)
    summary = comparator.get_all_builds_summary()

    out.print_header("PROJECT STATISTICS")

    total_essences = len(loader.essences)
    total_memories = len(loader.memories)
    total_characters = len(loader.builds)
    total_builds = summary["total_builds"]

    # Rarity distribution
    rarity_dist: Dict[str, int] = {}
    for e in loader.essences:
        r = e.get("rarity", "Unknown")
        rarity_dist[r] = rarity_dist.get(r, 0) + 1

    if out.fmt == "table":
        print(f"\nCharacters: {total_characters}")
        print(f"Total Builds: {total_builds}")
        print(f"Total Essences: {total_essences}")
        print(f"Total Memories: {total_memories}")

        print(f"\nEssence Rarity Distribution:")
        for r, count in sorted(rarity_dist.items()):
            print(f"  {r}: {count}")

        print(f"\nBuilds per Character:")
        for char, info in sorted(summary["characters"].items()):
            print(f"  {char.capitalize()}: {info['build_count']} builds")

        print(f"\nTop Synergy Builds:")
        for b in summary["top_synergy_builds"]:
            print(f"  {b['character'].capitalize()} - {b['build']} (Synergy: {b['synergy_score']}, {b['complexity']})")

        # Essence usage stats
        essence_usage: Dict[str, int] = {}
        for builds in loader.builds.values():
            for build in builds:
                for m in build.get("memories", []):
                    for e in m.get("essences", []):
                        essence_usage[e] = essence_usage.get(e, 0) + 1

        if essence_usage:
            sorted_usage = sorted(essence_usage.items(), key=lambda x: x[1], reverse=True)
            print(f"\nMost Used Essences:")
            for name, count in sorted_usage[:10]:
                print(f"  {name}: used in {count} builds")

            unused = [e["name"] for e in loader.essences if e["name"] not in essence_usage]
            if unused:
                print(f"\nUnused Essences ({len(unused)}):")
                for name in unused[:10]:
                    print(f"  - {name}")
                if len(unused) > 10:
                    print(f"  ... and {len(unused) - 10} more")
    else:
        out.collect({
            "characters": total_characters,
            "total_builds": total_builds,
            "total_essences": total_essences,
            "total_memories": total_memories,
            "rarity_distribution": rarity_dist,
            "builds_per_character": {
                k: v["build_count"] for k, v in summary["characters"].items()
            },
            "top_synergy_builds": summary["top_synergy_builds"],
        })
        out.flush()


def cmd_essences(loader: DataLoader, out: OutputFormatter, rarity: Optional[str] = None, **_):
    """Browse the essences catalog."""
    out.print_header("ESSENCES CATALOG")

    essences = loader.essences
    if rarity:
        essences = [e for e in essences if e.get("rarity", "").lower() == rarity.lower()]
        if not essences:
            print(f"No essences found with rarity '{rarity}'")
            print(f"Available rarities: Legendary, Epic, Rare, Common, Unique")
            return

    # Group by rarity
    by_rarity: Dict[str, List[Dict]] = {}
    for e in essences:
        r = e.get("rarity", "Unknown")
        by_rarity.setdefault(r, []).append(e)

    for r in ["Legendary", "Unique", "Epic", "Rare", "Common"]:
        group = by_rarity.get(r, [])
        if not group:
            continue
        if out.fmt == "table":
            print(f"\n{r} ({len(group)}):")
            for e in sorted(group, key=lambda x: x["name"]):
                types = ", ".join(e.get("synergy_types", []))
                print(f"  {e['name']}")
                print(f"    Effect: {e.get('effect', 'N/A')[:100]}...")
                if types:
                    print(f"    Types: {types}")
        else:
            for e in group:
                out.collect({
                    "name": e["name"],
                    "rarity": r,
                    "effect": e.get("effect", ""),
                    "synergy_types": e.get("synergy_types", []),
                })

    if out.fmt != "table":
        out.flush()


def cmd_memories(
    loader: DataLoader, out: OutputFormatter, character: Optional[str] = None, **_
):
    """Browse the memories catalog."""
    out.print_header("MEMORIES CATALOG")

    memories = loader.memories

    # Filter by character if specified (show memories used in that character's builds)
    if character:
        used_memories = set()
        for build in loader.builds_for(character):
            for m in build.get("memories", []):
                used_memories.add(m.get("name", ""))
        if used_memories:
            print(f"\nMemories used in {character.capitalize()} builds:")
            for mem in sorted(memories, key=lambda x: x["name"]):
                if mem["name"] in used_memories:
                    if out.fmt == "table":
                        kw = ", ".join(mem.get("synergy_keywords", []))
                        print(f"  [{mem.get('rarity', '?')[0]}] {mem['name']} ({mem.get('type', 'Unknown')})")
                        if kw:
                            print(f"      Keywords: {kw}")
                    else:
                        out.collect({
                            "name": mem["name"],
                            "rarity": mem.get("rarity", "?"),
                            "type": mem.get("type", "Unknown"),
                            "synergy_keywords": mem.get("synergy_keywords", []),
                        })
        else:
            print(f"No builds found for character: {character}")
        if out.fmt != "table":
            out.flush()
        return

    # Group by type
    by_type: Dict[str, List[Dict]] = {}
    for m in memories:
        t = m.get("type", "Unknown")
        by_type.setdefault(t, []).append(m)

    for mem_type in sorted(by_type.keys()):
        group = by_type[mem_type]
        if out.fmt == "table":
            print(f"\n{mem_type} ({len(group)}):")
            for m in sorted(group, key=lambda x: x["name"]):
                kw = ", ".join(m.get("synergy_keywords", []))
                rarity_char = m.get("rarity", "?")[0]
                print(f"  [{rarity_char}] {m['name']}")
                if kw:
                    print(f"      Keywords: {kw}")
        else:
            for m in group:
                out.collect({
                    "name": m["name"],
                    "rarity": m.get("rarity", "?"),
                    "type": mem_type,
                    "synergy_keywords": m.get("synergy_keywords", []),
                })

    if out.fmt != "table":
        out.flush()


def cmd_substitute(loader: DataLoader, out: OutputFormatter, essence: str, **_):
    """Find replacement essences for a given essence."""
    analyzer = SynergyAnalyzer(loader)
    substitutes = analyzer.suggest_substitutes(essence)

    if not substitutes:
        # Try partial match
        matches = [e for e in loader.essence_by_name if essence.lower() in e.lower()]
        if matches:
            print(f"Essence '{essence}' not found exactly. Did you mean:")
            for m in matches:
                print(f"  - {m}")
        else:
            print(f"Essence '{essence}' not found.")
        return

    out.print_header(f"SUBSTITUTES FOR: {essence}")

    original = loader.essence_by_name.get(essence, {})
    if out.fmt == "table":
        print(f"Original: {essence} ({original.get('rarity', '?')})")
        print(f"Types: {', '.join(original.get('synergy_types', []))}")
        print()

    for i, sub in enumerate(substitutes, 1):
        if out.fmt == "table":
            print(f"  {i}. {sub['essence']} ({sub['rarity']})")
            print(f"     Shared types: {', '.join(sub['shared_types'])}")
            print(f"     Match score: {sub['total_score']}")
        else:
            out.collect(sub)

    if out.fmt != "table":
        out.flush()


def cmd_reindex(loader: DataLoader, out: OutputFormatter, **_):
    """Regenerate the build index file."""
    index = {
        "essence_usage": {},
        "memory_usage": {},
        "characters": {},
    }

    for char_name, builds in loader.builds.items():
        index["characters"][char_name] = [b.get("name", "") for b in builds]
        for build in builds:
            build_ref = f"{char_name}/{build.get('name', '')}"
            for memory in build.get("memories", []):
                mem_name = memory.get("name", "")
                if mem_name:
                    index["memory_usage"].setdefault(mem_name, []).append(build_ref)
                for ess in memory.get("essences", []):
                    index["essence_usage"].setdefault(ess, []).append(build_ref)

    index_path = loader.builds_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Build index written to {index_path}")
    print(f"  Essences tracked: {len(index['essence_usage'])}")
    print(f"  Memories tracked: {len(index['memory_usage'])}")
    print(f"  Characters: {len(index['characters'])}")


def cmd_gaps(loader: DataLoader, out: OutputFormatter, character: str, **_):
    """Archetype gap analysis for a character."""
    analyzer = BuildAnalyzer(loader)
    result = analyzer.gap_analysis(character)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    out.print_header(
        f"ARCHETYPE GAP ANALYSIS: {character.upper()}\n"
        f"Coverage: {result['coverage_pct']:.0f}% ({len(result['covered_archetypes'])}/{len(result['covered_archetypes']) + len(result['uncovered_archetypes'])} archetypes)"
    )

    if out.fmt == "table":
        print(f"\nCovered Archetypes:")
        for arch_name, arch_info in sorted(result["covered_archetypes"].items()):
            builds_str = ", ".join(arch_info["builds"])
            print(f"  [OK] {arch_name}: {arch_info['description']}")
            print(f"       Builds: {builds_str}")

        if result["uncovered_archetypes"]:
            print(f"\nMissing Archetypes:")
            for arch in result["uncovered_archetypes"]:
                print(f"  [ ] {arch['archetype']}: {arch['description']}")
                print(f"       Keywords: {', '.join(arch['keywords'][:5])}")
        else:
            print(f"\n[OK] All archetypes covered!")
    else:
        out.collect(result)
        out.flush()


def cmd_scorecard(
    loader: DataLoader, out: OutputFormatter, character: str, name: str, **_
):
    """Detailed build scorecard with grade."""
    analyzer = BuildAnalyzer(loader)
    card = analyzer.build_scorecard(character, name)

    if not card:
        print(f"Build '{name}' not found for {character}")
        builds = loader.builds_for(character)
        if builds:
            print(f"\nAvailable builds:")
            for b in builds:
                print(f"  - {b.get('name', 'Unknown')}")
        return

    if out.fmt == "table":
        score = card["score"]
        out.print_header(
            f"BUILD SCORECARD: {card['build']}\n"
            f"Character: {character.upper()}  |  Grade: {card['grade']}  |  Score: {score['total']}/100"
        )

        print(f"\nScore Breakdown:")
        print(f"  Synergy:      {score['synergy']:>2}/40  (raw: {score['raw_synergy_score']})")
        print(f"  Rarity:       {score['rarity']:>2}/20")
        print(f"  Validity:     {score['validity']:>2}/20")
        print(f"  Completeness: {score['completeness']:>2}/20")
        print(f"  {'-' * 25}")
        print(f"  Total:        {score['total']:>2}/100")

        if card["archetypes"]:
            print(f"\nArchetypes: {', '.join(card['archetypes'])}")

        print(f"\nBuild Stats:")
        print(f"  Memories: {card['memory_count']}")
        print(f"  Total Essences: {card['essence_count']}")

        if score["synergy_details"]:
            print(f"\nActive Synergies:")
            for s in score["synergy_details"]:
                print(f"  [{s['score']}pts] {' + '.join(s['pair'])}")

        if card["improvements"]:
            print(f"\nSuggested Improvements:")
            for imp in card["improvements"]:
                print(f"  -> {imp}")
    else:
        out.collect(card)
        out.flush()


def cmd_meta(loader: DataLoader, out: OutputFormatter, **_):
    """Essence meta-game report."""
    analyzer = BuildAnalyzer(loader)
    report = analyzer.essence_meta_report()

    out.print_header("ESSENCE META-GAME REPORT")

    if out.fmt == "table":
        print(f"\nOverview:")
        print(f"  Total builds: {report['total_builds']}")
        print(f"  Total essences: {report['total_essences']}")
        print(f"  Used in builds: {report['used_essences']}")
        print(f"  Unused: {len(report['unused_essences'])}")

        print(f"\nUsage by Rarity:")
        for rarity, info in sorted(report["usage_by_rarity"].items()):
            print(f"  {rarity}: {info['used']} essences, {info['total_uses']} total uses")

        print(f"\nMost Popular Essences:")
        for name, count in report["most_used"][:10]:
            pct = count / report["total_builds"] * 100
            bar = "#" * int(pct / 5)
            print(f"  {name:<35} {count:>3} builds ({pct:.0f}%) {bar}")

        if report["least_used"]:
            print(f"\nRarely Used (1-2 builds):")
            for name, count in report["least_used"][:10]:
                print(f"  {name}: {count}")

        if report["unused_essences"]:
            print(f"\nCompletely Unused Essences:")
            for name in report["unused_essences"]:
                rarity = loader.essence_rarity_map.get(name, "?")
                print(f"  [{rarity[0]}] {name}")

        print(f"\nMost Common Essence Pairs:")
        for item in report["most_common_pairs"]:
            print(f"  {item['pair'][0]} + {item['pair'][1]}: {item['count']} builds")

        # Cross-character comparison
        comparison = analyzer.cross_character_comparison()
        print(f"\nCharacter Comparison:")
        print(f"  {'Character':<12} {'Builds':>6} {'Avg':>5} {'Max':>4} {'Coverage':>9}")
        print(f"  {'-' * 42}")
        for char, info in sorted(comparison.items(), key=lambda x: x[1]["avg_score"], reverse=True):
            print(
                f"  {char.capitalize():<12} {info['build_count']:>6} "
                f"{info['avg_score']:>5.0f} {info['max_score']:>4} "
                f"{info['archetype_coverage']:>7.0f}%"
            )
    else:
        out.collect(report)
        out.flush()


# -- Argument Parser ----------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="view_builds",
        description="Shape of Dreams - ARPG Build Viewer & Analyzer",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    sub.add_parser("list", help="List all builds overview")

    # character
    p = sub.add_parser("character", help="Show all builds for a character")
    p.add_argument("character", help="Character name")

    # build
    p = sub.add_parser("build", help="Show detailed build info")
    p.add_argument("character", help="Character name")
    p.add_argument("name", nargs="+", help="Build name (partial match)")

    # search
    p = sub.add_parser("search", help="Search builds by keyword")
    p.add_argument("query", nargs="+", help="Search query")

    # synergy
    p = sub.add_parser("synergy", help="Find builds using a specific essence")
    p.add_argument("essence", nargs="+", help="Essence name (partial match)")

    # validate
    sub.add_parser("validate", help="Validate all builds")

    # compare
    p = sub.add_parser("compare", help="Compare builds for a character")
    p.add_argument("character", help="Character name")

    # recommend
    p = sub.add_parser("recommend", help="Get build recommendations")
    p.add_argument("character", help="Character name")
    p.add_argument("--playstyle", "-p", default="aggressive",
                   choices=["aggressive", "defensive", "support", "mobile", "automated"],
                   help="Preferred playstyle")
    p.add_argument("--focus", default="damage",
                   choices=["damage", "survivability", "utility", "scaling"],
                   help="Build focus")
    p.add_argument("--complexity", "-c", default="any",
                   choices=["low", "medium", "high", "any"],
                   help="Preferred complexity")

    # stats
    sub.add_parser("stats", help="Show project statistics")

    # essences
    p = sub.add_parser("essences", help="Browse essences catalog")
    p.add_argument("--rarity", "-r", help="Filter by rarity")

    # memories
    p = sub.add_parser("memories", help="Browse memories catalog")
    p.add_argument("--character", "-c", help="Filter by character builds")

    # substitute
    p = sub.add_parser("substitute", help="Find essence replacements")
    p.add_argument("essence", nargs="+", help="Essence name")

    # gaps
    p = sub.add_parser("gaps", help="Archetype gap analysis for a character")
    p.add_argument("character", help="Character name")

    # scorecard
    p = sub.add_parser("scorecard", help="Detailed build scorecard with grade")
    p.add_argument("character", help="Character name")
    p.add_argument("name", nargs="+", help="Build name (partial match)")

    # meta
    sub.add_parser("meta", help="Essence meta-game report")

    # reindex
    sub.add_parser("reindex", help="Regenerate the build index")

    return parser


# -- Main ---------------------------------------------------------------

COMMANDS = {
    "list": cmd_list,
    "character": cmd_character,
    "build": cmd_build,
    "search": cmd_search,
    "synergy": cmd_synergy,
    "validate": cmd_validate,
    "compare": cmd_compare,
    "recommend": cmd_recommend,
    "stats": cmd_stats,
    "essences": cmd_essences,
    "memories": cmd_memories,
    "substitute": cmd_substitute,
    "gaps": cmd_gaps,
    "scorecard": cmd_scorecard,
    "meta": cmd_meta,
    "reindex": cmd_reindex,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    loader = get_loader()
    out = OutputFormatter(args.format)

    # Convert args to dict for command dispatch
    kwargs = vars(args)
    command = kwargs.pop("command")
    kwargs.pop("format")

    # Join multi-word arguments
    if "name" in kwargs and isinstance(kwargs["name"], list):
        kwargs["name"] = " ".join(kwargs["name"])
    if "query" in kwargs and isinstance(kwargs["query"], list):
        kwargs["query"] = " ".join(kwargs["query"])
    if "essence" in kwargs and isinstance(kwargs["essence"], list):
        kwargs["essence"] = " ".join(kwargs["essence"])

    cmd_fn = COMMANDS.get(command)
    if cmd_fn:
        cmd_fn(loader=loader, out=out, **kwargs)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
