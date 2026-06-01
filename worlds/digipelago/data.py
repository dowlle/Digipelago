"""Loads the pinned, curated Digimon dataset and derives the values the world
logic needs. Single source of truth: data/digimon_mvp.json (built by
tools/build_digimon_data.py from a Digi-API snapshot — non-commercial fan project).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PATH = Path(__file__).parent / "data" / "digimon_mvp.json"
_RAW_BYTES = _PATH.read_bytes()
_DATA = json.loads(_RAW_BYTES.decode("utf-8"))

# Content version of the pinned dataset. Embedded by tools/build_digimon_data.py
# (hash of the version-less payload) and READ here — never recomputed — so the
# apworld and client share one token and can't drift. Sent in slot_data so the
# client can verify its bundled copy matches the seed's. Falls back to a byte
# hash for any pre-embed dataset.
DATASET_VERSION: str = _DATA.get("version") or hashlib.sha256(_RAW_BYTES).hexdigest()[:12]

LEVEL_TIER: dict[str, int] = _DATA["level_tier"]      # {"Rookie": 2, ... "Mega": 5}
ATTRIBUTES: list[str] = _DATA["attributes"]           # ["Data","Free","Unknown","Vaccine","Variable","Virus"]
META: dict[str, dict] = _DATA["meta"]                 # {id: {name, level, attribute, ...}}
ROOTS: list[int] = _DATA["roots"]
LINES: dict[str, list[int]] = _DATA["lines"]

# (level, attribute) -> count, parsed from "Level|Attribute" keys
CELL_COUNTS: dict[tuple[str, str], int] = {}
for _k, _n in _DATA["cell_counts"].items():
    _lv, _at = _k.split("|", 1)
    CELL_COUNTS[(_lv, _at)] = _n

POOL_SIZE: int = len(META)

# Progressive "Digivolution" level key: one step per distinct tier (Rookie..Mega).
# Tier reached = 1 + count("Digivolution"); the Rookie step is precollected.
TIER_LADDER: list[int] = sorted(set(LEVEL_TIER.values()))
NUM_DIGIVOLUTION_STEPS: int = len(TIER_LADDER)
