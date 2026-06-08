"""Tests for the Digipelago APWorld.

Each WorldTestBase subclass auto-runs the inherited integration tests:
  - test_all_state_can_reach_everything  (all items -> all locations + victory)
  - test_empty_state_can_reach_something (sphere 0 is non-empty)
  - test_fill                            (distribute_items_restrictive succeeds)

`TestInvariants` adds the Digipelago-specific guarantees from ADR-0001 / the
Progression Logic note: non-empty + bounded sphere 0, capacity covers the whole
pool (no permanent lock), the tier ladder, and item/location balance.
"""
from BaseClasses import CollectionState
from test.bases import WorldTestBase

from worlds.digipelago import data as D


class _DigiBase(WorldTestBase):
    game = "Digipelago"


# ── option-combo coverage (each runs the 3 inherited tests) ──────────────────

class TestDefault(_DigiBase):
    pass


class TestStarterVirus(_DigiBase):
    options = {"starting_attribute": 1}


class TestStarterData(_DigiBase):
    options = {"starting_attribute": 2}


class TestStarterFree(_DigiBase):
    """Free starter = the tightest sphere 0 (Rookie|Free is the smallest cell)."""
    options = {"starting_attribute": 3}


class TestLowGoal(_DigiBase):
    options = {"goal_count": 5}


class TestHighGoal(_DigiBase):
    options = {"goal_count": 900}


class TestGoalLevelUltimate(_DigiBase):
    """Goal = catch 20 Ultimates."""
    options = {"goal": 1, "goal_level": 2, "goal_count": 20}


class TestGoalLevelMega(_DigiBase):
    """Goal = catch 50 Megas."""
    options = {"goal": 1, "goal_level": 3, "goal_count": 50}


class TestGoalLevelClamped(_DigiBase):
    """Rookie goal with a count above the Rookie pool — must clamp, stay beatable."""
    options = {"goal": 1, "goal_level": 0, "goal_count": 900}


class TestTightCapacity(_DigiBase):
    """Small start + small steps = many capacity upgrades in the pool."""
    options = {"starting_capacity": 10, "capacity_per_upgrade": 10}


class TestBigUpgrades(_DigiBase):
    options = {"starting_capacity": 10, "capacity_per_upgrade": 100}


# ── invariant tests ──────────────────────────────────────────────────────────

class TestInvariants(_DigiBase):
    def test_cell_counts_sum_equals_pool(self):
        self.assertEqual(sum(D.CELL_COUNTS.values()), D.POOL_SIZE,
                         "every pooled Digimon must sit in exactly one (level, attribute) cell")

    def test_sphere0_nonempty_and_bounded(self):
        rookie_vaccine = D.CELL_COUNTS[("Rookie", "Vaccine")]  # default starter = Vaccine
        state = CollectionState(self.multiworld)
        self.assertTrue(
            state.can_reach("Catch Slot #1", "Location", self.player),
            "sphere 0 must reach at least the first catch slot")
        self.assertTrue(
            state.can_reach(f"Catch Slot #{rookie_vaccine}", "Location", self.player),
            "sphere 0 should reach the entire starter (Rookie|Vaccine) cell")
        self.assertFalse(
            state.can_reach(f"Catch Slot #{rookie_vaccine + 1}", "Location", self.player),
            "sphere 0 must NOT reach beyond the starter pool (pool_size gate)")

    def test_capacity_covers_full_pool(self):
        allstate = self.multiworld.get_all_state()
        self.assertGreaterEqual(
            self.world._capacity(allstate), D.POOL_SIZE,
            "summed capacity must cover the whole pool — the no-permanent-lock invariant")
        self.assertEqual(
            self.world._pool_size(allstate), D.POOL_SIZE,
            "all attribute + level keys held => the entire pool is in logic")

    def test_all_slots_reachable_with_all_items(self):
        allstate = self.multiworld.get_all_state()
        self.assertTrue(
            allstate.can_reach(f"Catch Slot #{D.POOL_SIZE}", "Location", self.player))
        self.assertTrue(self.world._can_catch_n(allstate, D.POOL_SIZE))

    def test_victory_gated_by_goal(self):
        sphere0 = CollectionState(self.multiworld)
        self.assertFalse(
            sphere0.can_reach("Digipelago Victory", "Location", self.player),
            "victory must not be reachable from the starter kit (default goal 100 > starter pool)")
        allstate = self.multiworld.get_all_state()
        self.assertTrue(
            allstate.can_reach("Digipelago Victory", "Location", self.player))

    def test_tier_reached_mapping(self):
        state = CollectionState(self.multiworld)
        self.assertEqual(self.world._tier_reached(state), 2, "Rookie precollected => tier 2")
        state.collect(self.get_item_by_name("Digivolution"), True)
        self.assertEqual(self.world._tier_reached(state), 3, "one more Digivolution => Champion tier 3")

    def test_goal_count_clamped_to_level_pool(self):
        """A Rookie goal asking for 900 must clamp to the Rookie pool and stay winnable."""
        from worlds.digipelago import DigipelagoWorld  # noqa
        rookie_pool = sum(n for (lv, _a), n in D.CELL_COUNTS.items() if lv == "Rookie")
        # Build a fresh world with the level/Rookie/900 goal via a one-off generation.
        # (Simplest: assert the data fact the clamp relies on; full-gen clamp is covered
        # by TestGoalLevelClamped's inherited fill/reach tests.)
        self.assertLess(rookie_pool, 900, "test premise: Rookie pool is below the requested 900")

    def test_slot_data_shape(self):
        sd = self.world.fill_slot_data()
        for key in ("dataset_version", "starting_capacity", "capacity_per_upgrade",
                    "goal", "goal_level", "goal_count", "starting_attribute",
                    "starting_mode", "allow_mode_switch", "starting_stamina",
                    "stamina_regen_seconds",
                    "level_tier", "attributes", "cell_counts", "pool_size"):
            self.assertIn(key, sd, f"slot_data missing '{key}'")
        self.assertTrue(sd["dataset_version"], "dataset_version must be a non-empty hash")
        self.assertIn(sd["starting_mode"], ("free_text", "free_text_hard", "silhouette"))
        self.assertIsInstance(sd["allow_mode_switch"], bool)
        self.assertEqual(sd["pool_size"], D.POOL_SIZE)
        self.assertEqual(sum(sd["cell_counts"].values()), D.POOL_SIZE)
        # Lean: no heavy per-Digimon reference data dumped into slot_data.
        self.assertNotIn("meta", sd)
        self.assertNotIn("lines", sd)

    def test_itempool_matches_locations(self):
        n_loc = sum(1 for loc in self.multiworld.get_locations(self.player)
                    if loc.address is not None)
        n_items = len([i for i in self.multiworld.itempool if i.player == self.player])
        self.assertEqual(n_items, n_loc, "itempool must exactly fill addressable locations")
