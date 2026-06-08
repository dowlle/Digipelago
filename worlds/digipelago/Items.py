from BaseClasses import Item, ItemClassification

from . import data as D

# High base to avoid overlap with other games' ID spaces (cosmetic — IDs are per-game).
ITEM_ID_OFFSET = 8600000

# Single source of truth: item name -> (id, classification).
item_data_table: dict[str, tuple[int, ItemClassification]] = {
    # Bulk progression + pacing throttle: raises the DigiStorage capacity cap.
    "DigiStorage Upgrade": (ITEM_ID_OFFSET + 1, ItemClassification.progression),
    # Progressive level key: Rookie -> Champion -> Ultimate -> Mega.
    "Digivolution": (ITEM_ID_OFFSET + 2, ItemClassification.progression),
    # Cosmetic filler.
    "Digivice": (ITEM_ID_OFFSET + 100, ItemClassification.filler),
    # Useful, never progression: raises the silhouette-mode Stamina bar's max by one
    # on the client. Stamina self-regenerates, so it never gates AP.
    "Stamina Up": (ITEM_ID_OFFSET + 101, ItemClassification.useful),
    # Food (Digimon Story in-game names): eaten on the client to refill Stamina
    # (Processed Meat +1, Digimeat +3, DigiProtein = full). Useful, never
    # progression; client-side only, never gates AP.
    "Processed Meat": (ITEM_ID_OFFSET + 110, ItemClassification.useful),
    "Digimeat": (ITEM_ID_OFFSET + 111, ItemClassification.useful),
    "DigiProtein": (ITEM_ID_OFFSET + 112, ItemClassification.useful),
}

# Attribute gate keys (one per attribute in the dataset).
for _i, _attr in enumerate(D.ATTRIBUTES):
    item_data_table[f"{_attr} Key"] = (ITEM_ID_OFFSET + 10 + _i, ItemClassification.progression)

item_table: dict[str, int] = {name: data[0] for name, data in item_data_table.items()}


class DigipelagoItem(Item):
    game: str = "Digipelago"
