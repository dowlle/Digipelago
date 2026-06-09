from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, Toggle


class StartingCapacity(Range):
    """Initial DigiStorage capacity: the max number of Digimon you can have caught
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
    your sphere-0 guessable pool together with the precollected Rookie level. Only the
    four primary attributes can be a starter (Variable/Unknown are always unlocked
    mid-run via their Key). Defaults to random, so default-settings seeds vary instead
    of always opening on Vaccine; set vaccine/virus/data/free to pin it."""
    display_name = "Starting Attribute"
    option_vaccine = 0
    option_virus = 1
    option_data = 2
    option_free = 3
    default = "random"


class StartingMode(Choice):
    """Which input mode the client opens in. Input mode is client-side only and
    never affects what is beatable (mixed-mode multiworlds are fine). Defaults to
    silhouette: paired with the locked default (Allow Mode Switch off), this closes
    the see-silhouette-then-type exploit where a player could read the silhouette in
    one mode and type the answer in another.
    - free_text: type the Digimon's name (catch-anything).
    - free_text_hard: free-text with Wordle-style per-guess clues toward a hidden target.
    - silhouette: multiple-choice, name the silhouette (default).
    - mixed: each round randomly rolls type-the-silhouette OR multiple-choice
      (rolled per Digimon). Like silhouette mode, it needs the on-device image fetch.
      (`random` is a reserved Archipelago option name, hence `mixed`.)"""
    display_name = "Starting Mode"
    option_free_text = 0
    option_free_text_hard = 1
    option_silhouette = 2
    option_mixed = 3
    default = 2


class AllowModeSwitch(Toggle):
    """Whether the player may change input mode in the client. Off (default): the
    client is locked to Starting Mode (the mode, the hard-mode toggle, and the
    silhouette difficulty are all fixed); the player must opt in to switching. On:
    the client opens in Starting Mode but the player can switch freely."""
    display_name = "Allow Mode Switch"


class McDifficulty(Choice):
    """Silhouette mode only: how the wrong multiple-choice options (distractors) are
    chosen, which sets how hard the silhouette is to tell apart. Client-side only,
    never affects what is beatable.
    - easy: distractors drawn from anywhere in the pool (often a different level, so
      they are easy to rule out).
    - normal: distractors share the target's level (the previous default).
    - hard: distractors prefer same-base variants of the target (e.g. target Agumon ->
      Toy Agumon / Yuki Agumon / ...), the most confusable options the data allows."""
    display_name = "Silhouette Difficulty"
    option_easy = 0
    option_normal = 1
    option_hard = 2
    default = 1


class StartingStamina(Range):
    """Silhouette mode only: the starting size of your Stamina bar (how many wrong
    picks you can make before it is spent). Stamina self-regenerates over time and
    can be refilled instantly with food, so you can never get permanently stuck.
    Ignored by the free-text modes."""
    display_name = "Starting Stamina"
    range_start = 1
    range_end = 10
    default = 5


class StaminaUps(Range):
    """Silhouette mode only: how many 'Stamina Up' items to add to the pool. Each one
    the client receives permanently raises your maximum Stamina by one. Client-side
    only, never gates AP. 0 disables them."""
    display_name = "Stamina Ups"
    range_start = 0
    range_end = 20
    default = 0


class StaminaRegenSeconds(Range):
    """Silhouette mode only: how many seconds it takes to regenerate one spent Stamina
    point. Points regenerate one at a time, so a burst of wrong picks comes back over
    time rather than all at once. 0 means free guesses (Stamina never drains). The max
    is one day per point, for very slow long-async play (food then bridges the gaps)."""
    display_name = "Stamina Regen Seconds"
    range_start = 0
    range_end = 86400  # one day per point
    default = 30


class ProcessedMeatCount(Range):
    """Silhouette mode only: how many 'Processed Meat' food items to add to the pool.
    Each one the client receives can be eaten to refill 1 Stamina. Client-side only,
    never gates AP."""
    display_name = "Processed Meat Count"
    range_start = 0
    range_end = 300
    default = 8


class DigimeatCount(Range):
    """Silhouette mode only: how many 'Digimeat' food items to add to the pool. Each
    one refills 3 Stamina when eaten. Client-side only, never gates AP."""
    display_name = "Digimeat Count"
    range_start = 0
    range_end = 200
    default = 4


class DigiProteinCount(Range):
    """Silhouette mode only: how many 'DigiProtein' food items to add to the pool. Each
    one refills Stamina to full when eaten. Client-side only, never gates AP."""
    display_name = "DigiProtein Count"
    range_start = 0
    range_end = 100
    default = 1


class FoodFillerPercent(Range):
    """Silhouette mode only: what percent of the filler pool is replaced with weighted
    stamina-economy items (mostly Processed Meat, some Digimeat, the odd DigiProtein /
    Stamina Up) instead of do-nothing Digivice. This scales the feeding loop to the seed
    size rather than leaving food a rounding error in a ~900-slot pool. 0 = all Digivice
    (only the small baseline food applies). Ignored when silhouette is not reachable
    (food does nothing in the free-text modes). Client-side useful items, never gate AP."""
    display_name = "Food Filler Percent"
    range_start = 0
    range_end = 100
    default = 12


# Choice index -> dataset attribute string (must match data.ATTRIBUTES exactly).
STARTING_ATTRIBUTE_NAMES = {0: "Vaccine", 1: "Virus", 2: "Data", 3: "Free"}

# Choice index -> client input-mode string (must match the client's SlotData type).
STARTING_MODE_NAMES = {0: "free_text", 1: "free_text_hard", 2: "silhouette", 3: "mixed"}

# Choice index -> client silhouette-difficulty string (must match the client's SlotData type).
MC_DIFFICULTY_NAMES = {0: "easy", 1: "normal", 2: "hard"}

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
    starting_mode: StartingMode
    allow_mode_switch: AllowModeSwitch
    mc_difficulty: McDifficulty
    starting_stamina: StartingStamina
    stamina_ups: StaminaUps
    stamina_regen_seconds: StaminaRegenSeconds
    processed_meat: ProcessedMeatCount
    digimeat: DigimeatCount
    digiprotein: DigiProteinCount
    food_filler_percent: FoodFillerPercent
