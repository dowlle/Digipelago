# Digipelago — APWorld

The Archipelago world for **Digipelago**, a Digimon guessing-game randomizer for
Archipelago (the Digimon counterpart to Pokepelago). Unofficial, non-commercial fan
project. The game client lives in a separate repository.

## Current contents (Phase 0)

- `tools/build_digimon_data.py` — pulls the [Digi-API](https://digi-api.com/) catalogue,
  dedupes to a candidate guessing pool, and analyses the evolution graph for curation
  (level×attribute cell counts, forced roots, cross-attribute edges, attribute orphans).
  Stdlib only; needs a browser User-Agent (Digi-API 403s default urllib).
  Run: `python tools/build_digimon_data.py [--refresh]`.
- `data/digimon_raw.json` — cached full detail dump (1,488 entries).
- `data/analysis.json` — computed distributions + curation findings.

## APWorld (Phase 1, vertical slice)

- `worlds/digipelago/` — the Archipelago world. Progression = DigiStorage capacity +
  progressive Digivolution level keys + Attribute keys, over abstract `Catch Slot #k`
  locations. AP logic gates only on `capacity` + `pool_size` (graph/identity-independent).
  Consumes `worlds/digipelago/data/digimon_mvp.json`.

### Test-generate a seed

The world isn't a standalone install yet; test it inside an existing AP 0.6.7 install:

```
# copy the world + a YAML into an AP install, then generate
cp -r worlds/digipelago <AP_INSTALL>/worlds/digipelago
#  <AP_INSTALL>/Players_digi/digi.yaml :  name + "game: Digipelago" + a Digipelago: block
<AP_INSTALL>/.venv/Scripts/python.exe Generate.py --player_files_path Players_digi --seed 12345 --outputpath output_digi
```

Validated 2026-05-30: beatable 922-location seed, 0.12s. See the vault note
`Development/2026-05-30 — Phase 1 — APWorld Vertical Slice`.

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
