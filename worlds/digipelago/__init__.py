"""Digipelago — a Digimon guessing-game randomizer for Archipelago.

Vertical slice (Phase 1): the AP progression model only. Unlock Digimon via
multiworld items — DigiStorage capacity + progressive Digivolution level keys +
Attribute keys — and catch them via abstract `Catch Slot #k` locations. AP logic
gates only on capacity + pool_size; it is graph- and identity-independent. The
digivolution web and the guessing UI live in the (future) client.
"""
from __future__ import annotations

import math
from typing import Any

from BaseClasses import CollectionState, ItemClassification, Region
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import set_rule

from . import data as D
from .Items import DigipelagoItem, item_data_table, item_table
from .Locations import CATCH_SLOT_PREFIX, MAX_SLOTS, DigipelagoLocation, location_table
from .Options import (
    GOAL_LEVEL_NAMES,
    STARTING_ATTRIBUTE_NAMES,
    STARTING_MODE_NAMES,
    DigipelagoOptions,
)


class DigipelagoWeb(WebWorld):
    tutorials = []


class DigipelagoWorld(World):
    """Catch Digimon by guessing their names. Capacity, Digivolution level keys, and
    Attribute keys are the multiworld progression; catches are abstract slots."""

    game = "Digipelago"
    options_dataclass = DigipelagoOptions
    options: DigipelagoOptions
    topology_present = False
    web = DigipelagoWeb()

    item_name_to_id = item_table
    location_name_to_id = location_table

    # ── pipeline ─────────────────────────────────────────────────────────────

    def generate_early(self) -> None:
        self.starter_attr: str = STARTING_ATTRIBUTE_NAMES[self.options.starting_attribute.value]

        # Resolve the goal and clamp its count to the relevant pool.
        if self.options.goal.value == self.options.goal.option_level:
            self.goal_kind = "level"
            self.goal_level: str = GOAL_LEVEL_NAMES[self.options.goal_level.value]
            level_pool = sum(n for (lv, _at), n in D.CELL_COUNTS.items() if lv == self.goal_level)
            self.goal_count: int = min(self.options.goal_count.value, level_pool)
        else:
            self.goal_kind = "total"
            self.goal_level = None
            self.goal_count = min(self.options.goal_count.value, D.POOL_SIZE)

    # ── logic helpers (the entire rule set) ──────────────────────────────────

    def _capacity(self, state: CollectionState) -> int:
        return (self.options.starting_capacity.value
                + state.count("DigiStorage Upgrade", self.player) * self.options.capacity_per_upgrade.value)

    def _tier_reached(self, state: CollectionState) -> int:
        # Rookie (tier 2) is precollected -> count >= 1; each extra step raises the tier.
        return 1 + state.count("Digivolution", self.player)

    def _pool_size(self, state: CollectionState) -> int:
        tier = self._tier_reached(state)
        held = {a for a in D.ATTRIBUTES if state.has(f"{a} Key", self.player)}
        total = 0
        for (lv, at), n in D.CELL_COUNTS.items():
            if at in held and D.LEVEL_TIER[lv] <= tier:
                total += n
        return total

    def _pool_size_of_level(self, state: CollectionState, level: str) -> int:
        if self._tier_reached(state) < D.LEVEL_TIER[level]:
            return 0
        held = {a for a in D.ATTRIBUTES if state.has(f"{a} Key", self.player)}
        return sum(n for (lv, at), n in D.CELL_COUNTS.items() if lv == level and at in held)

    def _can_catch_n(self, state: CollectionState, k: int) -> bool:
        return self._capacity(state) >= k and self._pool_size(state) >= k

    def _can_catch_n_of_level(self, state: CollectionState, level: str, k: int) -> bool:
        return self._capacity(state) >= k and self._pool_size_of_level(state, level) >= k

    def _goal_reached(self, state: CollectionState) -> bool:
        if self.goal_kind == "level":
            return self._can_catch_n_of_level(state, self.goal_level, self.goal_count)
        return self._can_catch_n(state, self.goal_count)

    # ── items ─────────────────────────────────────────────────────────────────

    def create_item(self, name: str) -> DigipelagoItem:
        item_id, classification = item_data_table[name]
        return DigipelagoItem(name, classification, item_id, self.player)

    def create_event(self, name: str) -> DigipelagoItem:
        return DigipelagoItem(name, ItemClassification.progression, None, self.player)

    def get_filler_item_name(self) -> str:
        return "Digivice"

    def create_items(self) -> None:
        o = self.options
        pool: list[DigipelagoItem] = []

        # Capacity upgrades: enough that the summed capacity >= POOL_SIZE so every slot is reachable.
        need = max(0, D.POOL_SIZE - o.starting_capacity.value)
        n_upgrades = math.ceil(need / o.capacity_per_upgrade.value) if o.capacity_per_upgrade.value else 0
        pool += [self.create_item("DigiStorage Upgrade") for _ in range(n_upgrades)]

        # Digivolution: precollect the Rookie step, place the remaining tiers.
        self.multiworld.push_precollected(self.create_item("Digivolution"))
        pool += [self.create_item("Digivolution") for _ in range(D.NUM_DIGIVOLUTION_STEPS - 1)]

        # Attribute keys: precollect the starter's, place the rest as progression.
        self.multiworld.push_precollected(self.create_item(f"{self.starter_attr} Key"))
        pool += [self.create_item(f"{a} Key") for a in D.ATTRIBUTES if a != self.starter_attr]

        # Stamina Ups + food: useful (never progression), client-side meter boosts.
        pool += [self.create_item("Stamina Up") for _ in range(o.stamina_ups.value)]
        pool += [self.create_item("Processed Meat") for _ in range(o.processed_meat.value)]
        pool += [self.create_item("Digimeat") for _ in range(o.digimeat.value)]
        pool += [self.create_item("DigiProtein") for _ in range(o.digiprotein.value)]

        # Fill remaining locations with filler.
        total_locations = sum(1 for loc in self.multiworld.get_locations(self.player)
                              if loc.address is not None)
        pool += [self.create_item(self.get_filler_item_name())
                 for _ in range(total_locations - len(pool))]

        self.multiworld.itempool += pool

    # ── regions / rules ─────────────────────────────────────────────────────────

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        for name, loc_id in location_table.items():
            menu.locations.append(DigipelagoLocation(self.player, name, loc_id, menu))
        # Victory event location (no address).
        menu.locations.append(DigipelagoLocation(self.player, "Digipelago Victory", None, menu))

    def set_rules(self) -> None:
        p = self.player
        for k in range(1, MAX_SLOTS + 1):
            loc = self.multiworld.get_location(f"{CATCH_SLOT_PREFIX}{k}", p)
            set_rule(loc, lambda state, k=k: self._can_catch_n(state, k))

        victory = self.multiworld.get_location("Digipelago Victory", p)
        set_rule(victory, lambda state: self._goal_reached(state))
        victory.place_locked_item(self.create_event("Victory"))
        self.multiworld.completion_condition[p] = lambda state: state.has("Victory", p)

    # ── slot data ───────────────────────────────────────────────────────────────

    def fill_slot_data(self) -> dict[str, Any]:
        """Lean + authoritative. We send the per-seed config and the gate-logic
        primitives (cell_counts / level_tier / attributes), plus a dataset_version
        hash. The heavy static reference data (per-Digimon names, sprites, lines,
        roots) ships WITH the client, keyed by dataset_version — so slot_data stays
        small and the reference data can't silently drift from the seed."""
        o = self.options
        return {
            "dataset_version": D.DATASET_VERSION,
            "starting_capacity": o.starting_capacity.value,
            "capacity_per_upgrade": o.capacity_per_upgrade.value,
            "goal": self.goal_kind,
            "goal_level": self.goal_level,
            "goal_count": self.goal_count,
            "starting_attribute": self.starter_attr,
            # Client input-mode lock (client-side only, never gates AP).
            "starting_mode": STARTING_MODE_NAMES[o.starting_mode.value],
            "allow_mode_switch": bool(o.allow_mode_switch.value),
            "starting_stamina": o.starting_stamina.value,
            "stamina_regen_seconds": o.stamina_regen_seconds.value,
            "level_tier": D.LEVEL_TIER,
            "attributes": D.ATTRIBUTES,
            "cell_counts": {f"{lv}|{at}": n for (lv, at), n in D.CELL_COUNTS.items()},
            "pool_size": D.POOL_SIZE,
        }
