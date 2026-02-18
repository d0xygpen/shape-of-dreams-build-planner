"""
Shared Build Validators for Shape of Dreams ARPG Builds

Centralized validation logic used across all modules.
"""

from typing import Dict, List, Set, Optional

# Try to import DataLoader for cross-reference validation
try:
    from analysis.data_loader import DataLoader
except ImportError:
    from data_loader import DataLoader


class ValidationResult:
    """Structured validation result."""

    def __init__(self):
        self.valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str):
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_no_duplicate_essences(build: Dict) -> Dict:
    """
    Check that no essence is used more than once in a build.
    Game rule: Each unique essence can only be used once per build.

    Returns dict with 'valid', 'duplicates', 'total_essences', 'unique_essences'.
    """
    all_essences: List[str] = []
    for memory in build.get("memories", []):
        all_essences.extend(memory.get("essences", []))

    # Also check passive essences
    for passive in build.get("passive_essences", []):
        name = passive.get("name", "") if isinstance(passive, dict) else passive
        if name:
            all_essences.append(name)

    seen: Set[str] = set()
    duplicates: List[str] = []
    for essence in all_essences:
        if essence in seen:
            duplicates.append(essence)
        seen.add(essence)

    return {
        "valid": len(duplicates) == 0,
        "duplicates": duplicates,
        "total_essences": len(all_essences),
        "unique_essences": len(seen),
    }


def validate_build_references(build: Dict, loader: DataLoader) -> ValidationResult:
    """
    Validate that all essences and memories referenced in a build
    actually exist in the game data files.
    """
    result = ValidationResult()

    # Check memories exist
    for memory in build.get("memories", []):
        memory_name = memory.get("name", "")
        if memory_name and memory_name not in loader.memory_by_name:
            result.add_warning(f"Memory '{memory_name}' not found in memories.json")

        # Check essences exist
        for essence_name in memory.get("essences", []):
            if essence_name not in loader.essence_by_name:
                result.add_warning(f"Essence '{essence_name}' not found in essences.json")

    # Check passive essences
    for passive in build.get("passive_essences", []):
        name = passive.get("name", "") if isinstance(passive, dict) else passive
        if name and name not in loader.essence_by_name:
            result.add_warning(f"Passive essence '{name}' not found in essences.json")

    return result


def validate_build_schema(build: Dict) -> ValidationResult:
    """
    Validate that a build has all required fields and proper structure.
    """
    result = ValidationResult()
    required_fields = ["name", "concept", "playstyle", "memories"]

    for field in required_fields:
        if field not in build:
            result.add_error(f"Missing required field: '{field}'")

    # Validate memories structure
    memories = build.get("memories", [])
    if not isinstance(memories, list):
        result.add_error("'memories' must be a list")
    else:
        for i, memory in enumerate(memories):
            if not isinstance(memory, dict):
                result.add_error(f"Memory #{i+1} must be a dict")
                continue
            if "name" not in memory:
                result.add_error(f"Memory #{i+1} missing 'name'")
            if "essences" not in memory:
                result.add_warning(f"Memory #{i+1} '{memory.get('name', '?')}' has no essences")
            elif not isinstance(memory.get("essences"), list):
                result.add_error(f"Memory #{i+1} 'essences' must be a list")

    # Check for tree field (either naming convention)
    has_tree = build.get("astrology_tree") or build.get("constellation_tree")
    if not has_tree:
        result.add_warning("Build has no astrology/constellation tree defined")

    # Validate strengths/weaknesses
    if "strengths" not in build:
        result.add_warning("Build has no strengths listed")
    if "weaknesses" not in build:
        result.add_warning("Build has no weaknesses listed")

    return result


def validate_full_build(build: Dict, loader: Optional[DataLoader] = None) -> ValidationResult:
    """
    Run all validators on a build and combine results.
    """
    result = ValidationResult()

    # Schema validation
    schema_result = validate_build_schema(build)
    result.errors.extend(schema_result.errors)
    result.warnings.extend(schema_result.warnings)
    if not schema_result.valid:
        result.valid = False

    # Duplicate essence check
    dup_check = validate_no_duplicate_essences(build)
    if not dup_check["valid"]:
        result.add_error(
            f"Duplicate essences: {', '.join(dup_check['duplicates'])} "
            "(game rule: each essence can only be used once per build)"
        )

    # Cross-reference validation (if loader provided)
    if loader is not None:
        ref_result = validate_build_references(build, loader)
        result.warnings.extend(ref_result.warnings)
        if not ref_result.valid:
            result.errors.extend(ref_result.errors)
            result.valid = False

    return result
