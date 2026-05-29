from BaseClasses import Location

from . import data as D

# Shifted away from item IDs to prevent collisions.
LOCATION_ID_OFFSET = 8590000

CATCH_SLOT_PREFIX = "Catch Slot #"
# One abstract catch slot per catchable Digimon. Slot #k = "your kth catch".
# Identity (which Digimon) is decided client-side; the slot is graph-independent.
MAX_SLOTS = D.POOL_SIZE

location_table: dict[str, int] = {
    f"{CATCH_SLOT_PREFIX}{k}": LOCATION_ID_OFFSET + k
    for k in range(1, MAX_SLOTS + 1)
}


class DigipelagoLocation(Location):
    game: str = "Digipelago"
