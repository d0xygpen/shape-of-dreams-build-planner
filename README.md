# Shape of Dreams - Build Planner

A desktop build planner for **Shape of Dreams**, an ARPG game. Browse 94 optimized builds across 9 characters, compare builds side-by-side, explore synergies, and create your own custom builds.

## Download

**[Download the latest release](https://github.com/d0xygpen/shape-of-dreams-build-planner/releases)** - no Python required, just extract and run.

1. Download the ZIP from Releases
2. Extract the folder
3. Run `SODBuildPlanner.exe`

## Features

- **94 Optimized Builds** across 9 characters with synergy scoring (0-100)
- **Build Creator** - design your own builds with live synergy preview and validation
- **Side-by-Side Comparison** - compare any two builds with diff highlighting
- **Synergy Calculator** - explore 36 known synergy pairs and test combinations
- **Essence & Memory Catalogs** - browse all 86 essences and 127 memories with filters
- **Meta Dashboard** - statistics, character comparison, usage analytics

## Screenshots

The app uses a dark theme with ARPG-standard rarity colors:
- Common (gray), Rare (blue), Epic (purple), Legendary (gold), Unique (green)

## Characters

| Character | Playstyle | Builds |
|-----------|-----------|--------|
| **Mist** | Agile melee assassin | 11 |
| **Yubar** | Elemental mage | 11 |
| **Vesper** | Tank with health-scaling | 11 |
| **Aurena** | Support/healer | 10 |
| **Bismuth** | Ranged elemental | 14 |
| **Nachia** | Summoner | 11 |
| **Shell** | Defensive guardian | 12 |
| **Lacerta** | Ranged sniper | 9 |
| **General** | Any character | 5 |

## Custom Builds

Click the **Create** tab to design your own builds:
- Select a character and name your build
- Add up to 4 memories with 3 essences each
- See live synergy score and validation as you build
- Save builds locally (stored in `custom_builds/` next to the exe)

Custom builds appear in all tabs with a [Custom] tag and are fully integrated with scoring, comparison, and analysis.

## CLI Tool

A command-line interface is also included for advanced users:

```bash
python view_builds.py list           # List all builds
python view_builds.py character mist # Show builds for Mist
python view_builds.py scorecard mist "Divine Shadow"
python view_builds.py recommend vesper --playstyle defensive
python view_builds.py stats          # Project statistics
python view_builds.py validate       # Validate all builds
```

Run `python view_builds.py --help` for all 16 commands.

## Building from Source

Requires Python 3.10+ and ttkbootstrap:

```bash
pip install ttkbootstrap
python app.py           # Run the GUI
python build_exe.py     # Build the standalone exe
```

Tests: `python -m unittest discover tests -v` (78 tests)

## Project Structure

```
analysis/          # Analysis engine (scoring, synergies, validation)
gui/               # Desktop GUI (ttkbootstrap)
  tabs/            # Tab implementations (builds, create, compare, etc.)
  widgets/         # Reusable widgets (score bar, search bar, memory slot)
data/              # Game data (essences, memories, characters)
builds/            # Optimized build configurations (JSON)
custom_builds/     # User-created builds (generated at runtime)
tests/             # Test suite (78 tests)
```

## Important Game Rule

**Each essence can only be used once per build.** This constraint is enforced in validation and the build creator.

## License

MIT
