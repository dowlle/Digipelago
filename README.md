# Digipelago APWorld

The Archipelago world for **Digipelago**, a Digimon guessing game for the
[Archipelago Multiworld Randomizer](https://archipelago.gg) (the Digimon counterpart
to Pokepelago). Unofficial, non-commercial fan project.

You play it in your browser at **https://digipelago.ap-pie.com**, nothing to install
on the playing side. This repository provides the world file that Archipelago needs to
generate a multiworld containing a Digipelago slot. The web client lives at
[dowlle/DigipelagoClient](https://github.com/dowlle/DigipelagoClient).

## How it plays

Items from the multiworld widen what you can guess: DigiStorage Upgrades raise how
many Digimon you can have caught, progressive Digivolution keys unlock levels (Rookie
up to Mega), and Attribute Keys unlock attributes (Vaccine, Virus, Data, Free,
Variable, Unknown). Each correct guess catches that Digimon and completes a check,
sending an item to someone in the multiworld. Catch enough Digimon (your YAML's goal)
and you win. The full guide is on the site under "How to play".

## Setup

1. Install [Archipelago](https://archipelago.gg) **0.6.7 or newer**.
2. Download `digipelago.apworld` from the
   [releases page](https://github.com/dowlle/Digipelago/releases) and double-click it
   to install it (or place it in Archipelago's `custom_worlds` folder).
3. In the Archipelago Launcher, pick **Generate Template Options** to get a
   `Digipelago.yaml` template, then edit your player name and options.
4. Put every player's YAML in the `Players` folder and run **Generate**. Host the
   resulting zip at [archipelago.gg](https://archipelago.gg) under **Host Game**, or
   run the Archipelago server locally.
5. Open https://digipelago.ap-pie.com, enter the server address, port, and your slot
   name, and start guessing.

Note: the archipelago.gg website can only generate games for worlds it ships with.
Digipelago seeds must be generated locally with the apworld installed; hosting the
generated game on archipelago.gg works fine.

## Options highlights

- `goal` / `goal_count` / `goal_level`: what winning means; catch a total number of
  Digimon, or a number of one level (for example 20 Ultimates).
- `starting_mode`: the input mode the client opens in; `silhouette` (default,
  multiple choice), `free_text`, `free_text_hard` (hidden target with clues), or
  `mixed` (each round rolls typing or multiple choice).
- `allow_mode_switch`: off by default, locking the seed to the starting mode.
- `mc_difficulty`: how confusable the wrong silhouette options are (`hard` picks
  lookalike variants of the same Digimon family).
- `starting_capacity` / `capacity_per_upgrade`: the DigiStorage capacity curve.
- Stamina and food pacing for silhouette mode (`starting_stamina`,
  `stamina_regen_seconds`, food counts, `food_filler_percent`); the defaults are
  sensible for a first game.

Every option is documented in the generated YAML template.

## World design (for the curious)

Progression is DigiStorage capacity + progressive Digivolution level keys + Attribute
Keys over abstract `Catch Slot #k` locations. Archipelago logic gates only on capacity
and the unlocked pool size, never on specific Digimon identities, so the multiworld can
never strand you. Digivolution-line ordering (guess an evolved form only after catching
a curated prior form) is enforced client-side and cannot affect beatability. The world
package is self-contained: the curated dataset (`worlds/digipelago/data/digimon_mvp.json`,
about 900 Digimon) ships inside it, and a `dataset_version` handshake keeps the client
and world in sync.

## Repository contents

- `worlds/digipelago/`: the Archipelago world, including its dataset and unit tests.
- `tools/build_digimon_data.py`: rebuilds the curated dataset from the
  [Digi-API](https://digi-api.com/) catalogue (dedup, curation analysis, level and
  attribute gate grid). Stdlib only; needs a browser User-Agent (Digi-API 403s default
  urllib). Run: `python tools/build_digimon_data.py [--refresh]`.
- `data/`: the raw cached Digi-API dump and curation analysis the build tool consumes.

### Running the tests

The world tests run inside an Archipelago source checkout (0.6.7): copy
`worlds/digipelago` into the checkout's `worlds/` folder and run pytest on
`worlds/digipelago/test`.

## License

This project's own source code is licensed under the **MIT License** (see `LICENSE`).

## Fan project disclaimer

Digipelago is an unofficial, non-commercial fan project. Digimon and all related names,
characters, and media are trademarks and copyright of Bandai, Toei Animation, and their
respective owners. This project is not affiliated with, endorsed by, or sponsored by any
of them. Digimon data is sourced from [Digi-API](https://digi-api.com/) (which draws on
Wikimon); no copyrighted Digimon artwork is hosted or distributed by this project. The
MIT license covers this repository's own code only, not any Digimon names, data, or media,
which remain the property of their respective owners.
