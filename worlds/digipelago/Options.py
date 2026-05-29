from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range


class StartingCapacity(Range):
    """Initial DigiStorage capacity — the max number of Digimon you can have caught
    before the multiworld grants more capacity."""
    display_name = "Starting Capacity"
    range_start = 10
    range_end = 200
    default = 50


class CapacityPerUpgrade(Range):
    """How much each DigiStorage Upgrade item raises the capacity cap."""
    display_name = "Capacity Per Upgrade"
    range_start = 10
    range_end = 100
    default = 50


class Goal(Choice):
    """What winning means.
    - total: catch `goal_count` Digimon of any level.
    - level: catch `goal_count` Digimon of the chosen `goal_level` (e.g. 20 Ultimates)."""
    display_name = "Goal"
    option_total = 0
    option_level = 1
    default = 0


class GoalLevel(Choice):
    """Which level the `level` goal targets (ignored when goal = total)."""
    display_name = "Goal Level"
    option_rookie = 0
    option_champion = 1
    option_ultimate = 2
    option_mega = 3
    default = 2  # Ultimate — the thematic default


class GoalCount(Range):
    """How many Digimon you must catch (correctly guess) to win. Clamped to the size
    of the relevant pool (the whole pool for `total`, or the chosen level's pool)."""
    display_name = "Goal Count"
    range_start = 5
    range_end = 900
    default = 100


class StartingAttribute(Choice):
    """Which attribute you start with unlocked (its key is precollected). Determines
    your sphere-0 guessable pool together with the precollected Rookie level."""
    display_name = "Starting Attribute"
    option_vaccine = 0
    option_virus = 1
    option_data = 2
    option_free = 3
    default = 0


# Choice index -> dataset attribute string (must match data.ATTRIBUTES exactly).
STARTING_ATTRIBUTE_NAMES = {0: "Vaccine", 1: "Virus", 2: "Data", 3: "Free"}

# Choice index -> dataset level string (must match data.LEVEL_TIER keys exactly).
GOAL_LEVEL_NAMES = {0: "Rookie", 1: "Champion", 2: "Ultimate", 3: "Mega"}


@dataclass
class DigipelagoOptions(PerGameCommonOptions):
    starting_capacity: StartingCapacity
    capacity_per_upgrade: CapacityPerUpgrade
    goal: Goal
    goal_level: GoalLevel
    goal_count: GoalCount
    starting_attribute: StartingAttribute
