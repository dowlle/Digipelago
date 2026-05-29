# Digipelago — code

Spike + future code home for **Digipelago**, a Digimon guessing-game randomizer for
Archipelago (the Digimon counterpart to Pokepelago). Non-commercial fan project.

**Design & decisions live in the vault:** `F:\Vaults\stefappelhof\11-Dev\Digipelago\`
(start at `Digipelago.md` / `Digipelago Agent Briefing.md`).

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

Phase 1 continues with goal variety, full slot_data, apworld tests, then the client fork
of `D:\pythonProjects\PokepelagoClient\`.
