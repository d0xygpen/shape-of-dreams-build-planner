"""
Shared Data Loader for Shape of Dreams ARPG Builds

Centralized data loading with caching, error handling, and configurable paths.
Used by view_builds.py, build_comparator.py, and synergy_analyzer.py.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from analysis.paths import get_base_dir, get_custom_builds_dir


class DataLoadError(Exception):
    """Raised when game data files cannot be loaded."""
    pass


class DataLoader:
    """
    Centralized loader for all game data and build files.
    Caches everything after first load for performance.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = get_base_dir()
        self.base_dir = base_dir
        self.builds_dir = base_dir / "builds"
        self.data_dir = base_dir / "data"
        self.custom_builds_dir = get_custom_builds_dir()

        # Caches (None = not yet loaded)
        self._builds: Optional[Dict[str, List[Dict]]] = None
        self._custom_builds: Optional[Dict[str, List[Dict]]] = None
        self._essences: Optional[List[Dict]] = None
        self._memories: Optional[List[Dict]] = None
        self._characters: Optional[List[Dict]] = None
        self._astrology_tree: Optional[Dict] = None
        self._constellation_powers: Optional[Any] = None

        # Lookup tables (built on first access)
        self._essence_by_name: Optional[Dict[str, Dict]] = None
        self._essence_rarity_map: Optional[Dict[str, str]] = None
        self._memory_by_name: Optional[Dict[str, Dict]] = None
        self._character_by_name: Optional[Dict[str, Dict]] = None

    def _load_json(self, path: Path) -> Any:
        """Load a JSON file with proper error handling."""
        if not path.exists():
            raise DataLoadError(f"File not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in {path}: {e}")
        except IOError as e:
            raise DataLoadError(f"Cannot read {path}: {e}")

    # ── Raw data loaders (cached) ──────────────────────────────────────

    @property
    def builds(self) -> Dict[str, List[Dict]]:
        """All builds keyed by character name (lowercase)."""
        if self._builds is None:
            self._builds = {}
            if not self.builds_dir.exists():
                return self._builds
            for build_file in self.builds_dir.glob("*_builds.json"):
                char_name = build_file.stem.replace("_builds", "").lower()
                try:
                    data = self._load_json(build_file)
                    self._builds[char_name] = data.get("builds", [])
                except DataLoadError as e:
                    print(f"Warning: {e}")
        return self._builds

    def builds_for(self, character: str) -> List[Dict]:
        """Get builds for a specific character (case-insensitive)."""
        return self.builds.get(character.lower(), [])

    # ── Custom builds (user-created, writable) ───────────────────────

    @property
    def custom_builds(self) -> Dict[str, List[Dict]]:
        """User-created builds keyed by character name (lowercase)."""
        if self._custom_builds is None:
            self._custom_builds = {}
            if not self.custom_builds_dir.exists():
                return self._custom_builds
            for build_file in self.custom_builds_dir.glob("*_builds.json"):
                char_name = build_file.stem.replace("_builds", "").lower()
                try:
                    data = self._load_json(build_file)
                    self._custom_builds[char_name] = data.get("builds", [])
                except DataLoadError as e:
                    print(f"Warning: {e}")
        return self._custom_builds

    @property
    def all_builds(self) -> Dict[str, List[Dict]]:
        """Merged view: bundled builds + custom builds."""
        merged = {}
        for char, builds in self.builds.items():
            merged[char] = list(builds)
        for char, builds in self.custom_builds.items():
            merged.setdefault(char, []).extend(builds)
        return merged

    @property
    def all_character_names(self) -> List[str]:
        """Character names from both bundled and custom builds."""
        names = set(self.builds.keys()) | set(self.custom_builds.keys())
        return sorted(names)

    def is_custom_build(self, character: str, build_name: str) -> bool:
        """Check if a build is user-created (lives in custom_builds/)."""
        char_lower = character.lower()
        for b in self.custom_builds.get(char_lower, []):
            if b.get("name") == build_name:
                return True
        return False

    def save_custom_build(self, character: str, build: dict) -> Path:
        """Save a user-created build to custom_builds/ directory.

        If a build with the same name already exists, it is replaced.
        Returns the path to the saved file.
        """
        self.custom_builds_dir.mkdir(parents=True, exist_ok=True)
        char_lower = character.lower()
        file_path = self.custom_builds_dir / f"{char_lower}_builds.json"

        # Load existing file or start fresh
        if file_path.exists():
            try:
                data = self._load_json(file_path)
            except DataLoadError:
                data = {"character": character.capitalize(), "builds": []}
        else:
            data = {"character": character.capitalize(), "builds": []}

        # Replace existing build with same name, or append
        builds_list = data.get("builds", [])
        replaced = False
        for i, b in enumerate(builds_list):
            if b.get("name") == build["name"]:
                builds_list[i] = build
                replaced = True
                break
        if not replaced:
            builds_list.append(build)

        data["builds"] = builds_list

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Invalidate custom cache so next access reloads
        self._custom_builds = None
        return file_path

    def delete_custom_build(self, character: str, build_name: str) -> bool:
        """Delete a user-created build by name. Returns True if found."""
        char_lower = character.lower()
        file_path = self.custom_builds_dir / f"{char_lower}_builds.json"
        if not file_path.exists():
            return False

        try:
            data = self._load_json(file_path)
        except DataLoadError:
            return False

        builds_list = data.get("builds", [])
        original_count = len(builds_list)
        builds_list = [b for b in builds_list if b.get("name") != build_name]

        if len(builds_list) == original_count:
            return False

        data["builds"] = builds_list
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._custom_builds = None
        return True

    @property
    def essences(self) -> List[Dict]:
        """All essence definitions."""
        if self._essences is None:
            data = self._load_json(self.data_dir / "essences.json")
            self._essences = data.get("essences", [])
        return self._essences

    @property
    def memories(self) -> List[Dict]:
        """All memory definitions."""
        if self._memories is None:
            data = self._load_json(self.data_dir / "memories.json")
            self._memories = data.get("memories", [])
        return self._memories

    @property
    def characters(self) -> List[Dict]:
        """All character definitions."""
        if self._characters is None:
            data = self._load_json(self.data_dir / "characters.json")
            self._characters = data.get("characters", [])
        return self._characters

    @property
    def astrology_tree(self) -> Dict:
        """Astrology/constellation tree data."""
        if self._astrology_tree is None:
            data = self._load_json(self.data_dir / "astrology_tree.json")
            self._astrology_tree = data.get("astrology_tree", {})
        return self._astrology_tree

    @property
    def constellation_powers(self) -> Any:
        """Constellation powers data."""
        if self._constellation_powers is None:
            self._constellation_powers = self._load_json(
                self.data_dir / "constellation_powers.json"
            )
        return self._constellation_powers

    # ── Lookup tables (built on first access) ──────────────────────────

    @property
    def essence_by_name(self) -> Dict[str, Dict]:
        """Essence lookup by name."""
        if self._essence_by_name is None:
            self._essence_by_name = {e["name"]: e for e in self.essences}
        return self._essence_by_name

    @property
    def essence_rarity_map(self) -> Dict[str, str]:
        """Essence name -> rarity string."""
        if self._essence_rarity_map is None:
            self._essence_rarity_map = {e["name"]: e["rarity"] for e in self.essences}
        return self._essence_rarity_map

    @property
    def memory_by_name(self) -> Dict[str, Dict]:
        """Memory lookup by name."""
        if self._memory_by_name is None:
            self._memory_by_name = {m["name"]: m for m in self.memories}
        return self._memory_by_name

    @property
    def character_by_name(self) -> Dict[str, Dict]:
        """Character lookup by name."""
        if self._character_by_name is None:
            self._character_by_name = {c["name"]: c for c in self.characters}
        return self._character_by_name

    @property
    def character_names(self) -> List[str]:
        """List of all character names from build files."""
        return sorted(self.builds.keys())

    # ── Utility ────────────────────────────────────────────────────────

    def get_rarity_symbol(self, essence_name: str) -> str:
        """Get display symbol for an essence's rarity."""
        rarity = self.essence_rarity_map.get(essence_name, "Unknown")
        return {
            "Legendary": "[L]",
            "Epic": "[E]",
            "Rare": "[R]",
            "Common": "[C]",
            "Unique": "[U]",
        }.get(rarity, "[?]")

    def get_all_essences_in_build(self, build: Dict) -> List[str]:
        """Get flat list of all essence names used in a build."""
        essences = []
        for memory in build.get("memories", []):
            essences.extend(memory.get("essences", []))
        for passive in build.get("passive_essences", []):
            name = passive.get("name", "") if isinstance(passive, dict) else passive
            if name:
                essences.append(name)
        return essences

    def count_rarity(self, build: Dict) -> Dict[str, int]:
        """Count essences by rarity tier in a build."""
        counts = {"Legendary": 0, "Epic": 0, "Rare": 0, "Common": 0, "Unique": 0}
        for essence_name in self.get_all_essences_in_build(build):
            rarity = self.essence_rarity_map.get(essence_name, "Unknown")
            if rarity in counts:
                counts[rarity] += 1
        return counts

    def invalidate_cache(self):
        """Clear all caches. Useful if data files have changed."""
        self._builds = None
        self._custom_builds = None
        self._essences = None
        self._memories = None
        self._characters = None
        self._astrology_tree = None
        self._constellation_powers = None
        self._essence_by_name = None
        self._essence_rarity_map = None
        self._memory_by_name = None
        self._character_by_name = None


# Module-level singleton for convenience
_default_loader: Optional[DataLoader] = None


def get_loader(base_dir: Optional[Path] = None) -> DataLoader:
    """Get or create the default DataLoader singleton."""
    global _default_loader
    if _default_loader is None or (base_dir is not None and _default_loader.base_dir != base_dir):
        _default_loader = DataLoader(base_dir)
    return _default_loader
