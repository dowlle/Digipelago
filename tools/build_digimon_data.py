#!/usr/bin/env python3
"""Phase 0 spike: pull the Digi-API catalogue, dedupe to a candidate guessing
pool, and analyse it for the curation work Digipelago needs.

Outputs (written next to ../data/):
  digimon_raw.json   full detail dump, cached so reruns don't re-hit the API
  analysis.json      computed distributions + curation findings

Stdlib only (no pip — supply-chain hygiene). Digi-API is a fan service; we hit
it once to snapshot, never at generation time. Non-commercial fan project.

Usage:
  python build_digimon_data.py            # use cache if present
  python build_digimon_data.py --refresh  # force re-fetch from the API
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "https://digi-api.com/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (Digipelago-spike; non-commercial fan project)"}
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW = DATA_DIR / "digimon_raw.json"
ANALYSIS = DATA_DIR / "analysis.json"
MVP = DATA_DIR / "digimon_mvp.json"
CURATION = DATA_DIR / "curation_report.json"

# MVP ladder: Rookie-and-up, four combat tiers only. Babies (Fresh/In-Training)
# and off-ladder Armor/Hybrid/Unknown are excluded pending their own design pass.
MVP_TIERS = {"Rookie": 2, "Champion": 3, "Ultimate": 4, "Mega": 5}

# Digi-API uses Japanese-canon level names. Map to English-dub ladder + tier.
# There is no "Ultra" level in Digi-API. Armor/Hybrid sit outside the linear ladder.
JP_TO_EN = {
    "Baby I": ("Fresh", 0),
    "Baby II": ("In-Training", 1),
    "Child": ("Rookie", 2),
    "Adult": ("Champion", 3),
    "Perfect": ("Ultimate", 4),
    "Ultimate": ("Mega", 5),
    "Armor": ("Armor", -1),
    "Hybrid": ("Hybrid", -1),
    "Unknown": ("Unknown", -2),
}


def get(url, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 - spike: retry on anything transient
            if i == retries - 1:
                raise
            time.sleep(1.0 * (i + 1))


def list_all_ids():
    ids, page = [], 0
    total = None
    while True:
        data = get(f"{BASE}/digimon?page={page}&pageSize=100")
        ids.extend(c["id"] for c in data.get("content", []))
        pageable = data.get("pageable", {})
        total = pageable.get("totalElements", total)
        if not data.get("content") or (total and len(ids) >= total):
            break
        page += 1
    return ids, total


def fetch_all(ids):
    out = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(get, f"{BASE}/digimon/{i}"): i for i in ids}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                out[i] = fut.result()
            except Exception as e:  # noqa: BLE001
                out[i] = {"id": i, "_error": f"{type(e).__name__}: {e}"}
            done += 1
            if done % 100 == 0:
                print(f"  fetched {done}/{len(ids)}", file=sys.stderr)
    return out


def load_raw(refresh: bool):
    if RAW.exists() and not refresh:
        print(f"Using cached {RAW.name}", file=sys.stderr)
        return json.loads(RAW.read_text(encoding="utf-8"))
    print("Listing IDs...", file=sys.stderr)
    ids, total = list_all_ids()
    print(f"  {len(ids)} ids (totalElements={total}). Fetching details...", file=sys.stderr)
    raw = fetch_all(ids)
    RAW.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {RAW}", file=sys.stderr)
    return raw


# ---------- normalisation ----------

def primary_level(levels):
    """Highest tier among a Digimon's levels (Game Design: gate on highest)."""
    best = None
    for lv in levels:
        en = JP_TO_EN.get(lv.get("level"))
        if not en:
            continue
        if best is None or en[1] > best[1]:
            best = en
    return best  # (en_name, tier) or None


def is_variant(d):
    """Heuristic alt-form filter for a fair guessing pool. Conservative — listed
    transparently so curation can re-include false positives."""
    name = d.get("name", "")
    if d.get("xAntibody"):
        return "x-antibody"
    if "(" in name:  # "(X-Antibody)", "(2010 Anime Version)", "(Blue)", "(C'mon ... Version)"
        return "parenthetical"
    return None


def analyse(raw):
    digi = {}
    for i, d in raw.items():
        if d.get("_error"):
            continue
        attrs = [a.get("attribute") for a in d.get("attributes", []) if a.get("attribute")]
        levels = d.get("levels", [])
        pl = primary_level(levels)
        digi[int(i)] = {
            "id": int(i),
            "name": d.get("name"),
            "levels_jp": [lv.get("level") for lv in levels],
            "primary_level": pl[0] if pl else None,
            "tier": pl[1] if pl else None,
            "attributes": attrs,
            "primary_attribute": attrs[0] if attrs else None,
            "xAntibody": bool(d.get("xAntibody")),
            "variant": is_variant(d),
            "year": (d.get("releaseDate") or None),
            "priors": [p.get("id") for p in d.get("priorEvolutions", []) if p.get("id")],
            "nexts": [n.get("id") for n in d.get("nextEvolutions", []) if n.get("id")],
        }

    total = len(raw)
    errors = sum(1 for d in raw.values() if d.get("_error"))

    # distributions
    from collections import Counter
    by_jp = Counter()
    for x in digi.values():
        for j in x["levels_jp"]:
            by_jp[j] += 1
    by_en_tier = Counter(x["primary_level"] for x in digi.values())
    by_attr = Counter(x["primary_attribute"] for x in digi.values())
    multi_level = sum(1 for x in digi.values() if len(x["levels_jp"]) > 1)
    multi_attr = sum(1 for x in digi.values() if len(x["attributes"]) > 1)
    missing_level = sum(1 for x in digi.values() if x["primary_level"] is None)
    missing_attr = sum(1 for x in digi.values() if x["primary_attribute"] is None)

    # dedup -> candidate pool
    variant_breakdown = Counter(x["variant"] for x in digi.values() if x["variant"])
    pool = {
        i: x for i, x in digi.items()
        if not x["variant"] and x["primary_level"] is not None and x["primary_attribute"] is not None
    }
    pool_ids = set(pool)

    # (level x attribute) cell counts on the pool
    cells = Counter()
    for x in pool.values():
        cells[(x["primary_level"], x["primary_attribute"])] += 1

    # evolution graph within the pool
    forced_roots = []          # non-base node with no in-pool prior (breaks the climb)
    cross_attr_edges = 0
    attr_orphans = []          # node whose in-pool priors ALL cross attribute (connectivity risk)
    for i, x in pool.items():
        in_pool_priors = [p for p in x["priors"] if p in pool_ids]
        if not in_pool_priors and (x["tier"] is not None and x["tier"] >= 3):  # Champion+
            forced_roots.append((i, x["name"], x["primary_level"]))
        if in_pool_priors:
            same_attr = [p for p in in_pool_priors if pool[p]["primary_attribute"] == x["primary_attribute"]]
            for p in in_pool_priors:
                if pool[p]["primary_attribute"] != x["primary_attribute"]:
                    cross_attr_edges += 1
            if not same_attr:  # no attribute-consistent prior available in pool
                attr_orphans.append((i, x["name"], x["primary_attribute"]))

    roots = [i for i, x in pool.items()
             if not [p for p in x["priors"] if p in pool_ids]]

    # Refined model (the design's real rule): the line-climb starts at ROOKIE.
    # Rookie-and-below (tier <= 2) are roots, so the Free-attribute baby tiers
    # never act as required priors. Attribute consistency is checked on the full
    # attribute SETS (286 Digimon are multi-attribute), not just the primary.
    CLIMB_MIN = 3  # Champion and above must climb from a prior
    def aset(i):
        return set(pool[i]["attributes"])
    cp_no_prior, cp_attr_orphan = [], []
    cp_cross_edges = cp_total_edges = 0
    for i, x in pool.items():
        if x["tier"] is None or x["tier"] < CLIMB_MIN:
            continue
        in_pool = [p for p in x["priors"] if p in pool_ids]
        if not in_pool:
            cp_no_prior.append((i, x["name"], x["primary_level"]))
            continue
        tset = aset(i)
        consistent = [p for p in in_pool if aset(p) & tset]
        for p in in_pool:
            cp_total_edges += 1
            if not (aset(p) & tset):
                cp_cross_edges += 1
        if not consistent:
            cp_attr_orphan.append((i, x["name"], x["primary_attribute"]))

    result = {
        "totals": {
            "raw_entries": total,
            "fetch_errors": errors,
            "usable": len(digi),
            "candidate_pool": len(pool),
            "variants_excluded": dict(variant_breakdown),
            "excluded_missing_level": missing_level,
            "excluded_missing_attr": missing_attr,
            "multi_level_count": multi_level,
            "multi_attribute_count": multi_attr,
        },
        "distribution_by_jp_level": dict(by_jp.most_common()),
        "distribution_by_en_tier": dict(by_en_tier.most_common()),
        "distribution_by_attribute": dict(by_attr.most_common()),
        "cell_counts_level_x_attribute": {f"{lv} | {at}": n for (lv, at), n in sorted(cells.items(), key=lambda kv: -kv[1])},
        "graph": {
            "pool_roots": len(roots),
            "forced_roots_champion_plus": len(forced_roots),
            "forced_roots_sample": forced_roots[:25],
            "cross_attribute_edges": cross_attr_edges,
            "attribute_orphans": len(attr_orphans),
            "attribute_orphans_sample": attr_orphans[:25],
        },
        "refined_climb_from_rookie": {
            "_note": "Rookie-and-below are roots; only Champion+ must climb. "
                     "Attribute consistency checked on full attribute sets.",
            "champion_plus_in_pool": sum(1 for x in pool.values() if x["tier"] and x["tier"] >= 3),
            "forced_roots_no_prior": len(cp_no_prior),
            "forced_roots_sample": cp_no_prior[:25],
            "cross_attribute_edges": cp_cross_edges,
            "total_climb_edges": cp_total_edges,
            "attribute_orphans_unfixable": len(cp_attr_orphan),
            "attribute_orphans_sample": cp_attr_orphan[:25],
        },
    }
    return result


def build_curated(raw):
    """Emit the pinned MVP dataset the apworld + client consume.

    Curation rules (locked decisions, see vault Game Design / Progression Logic):
      - Pool = Rookie..Mega, deduped, has level + attribute. Babies & off-ladder excluded.
      - Gating attribute = primary attribute; the climb keeps ONLY same-primary-attribute
        prior edges so a single attribute key threads a full root->target path.
      - Roots = all Rookies + any Champion+ left with no consistent prior (forced roots,
        attribute orphans) + any cycle-locked node. Roots are directly catchable once
        their level + attribute keys are held.
      - Full reachability is then guaranteed by construction (verified below).
    """
    # normalise (mirror analyse, plus client-facing fields)
    digi = {}
    for i, d in raw.items():
        if d.get("_error"):
            continue
        attrs = [a.get("attribute") for a in d.get("attributes", []) if a.get("attribute")]
        pl = primary_level(d.get("levels", []))
        imgs = d.get("images", []) or [{}]
        digi[int(i)] = {
            "id": int(i),
            "name": d.get("name"),
            "level": pl[0] if pl else None,
            "tier": pl[1] if pl else None,
            "attributes": attrs,
            "attribute": attrs[0] if attrs else None,
            "types": [t.get("type") for t in d.get("types", []) if t.get("type")],
            "fields": [f.get("field") for f in d.get("fields", []) if f.get("field")],
            "year": d.get("releaseDate") or None,
            "sprite": imgs[0].get("href"),
            "xAntibody": bool(d.get("xAntibody")),
            "variant": is_variant(d),
            "priors": [p.get("id") for p in d.get("priorEvolutions", []) if p.get("id")],
        }

    pool = {
        i: x for i, x in digi.items()
        if not x["variant"] and x["attribute"] and x["level"] in MVP_TIERS
    }
    pool_ids = set(pool)

    lines, roots = {}, set()
    forced, orphan = [], []
    for i, x in pool.items():
        if x["level"] == "Rookie":
            roots.add(i)
            continue
        same = sorted(p for p in x["priors"]
                      if p in pool_ids and pool[p]["attribute"] == x["attribute"])
        if same:
            lines[i] = same
        else:
            roots.add(i)
            in_pool_any = [p for p in x["priors"] if p in pool_ids]
            (orphan if in_pool_any else forced).append([i, x["name"], x["level"], x["attribute"]])

    # Reachability fixpoint; auto-promote any cycle-locked node to a root.
    cycle_promoted = []
    while True:
        reachable = set(roots)
        changed = True
        while changed:
            changed = False
            for t, ps in lines.items():
                if t not in reachable and any(p in reachable for p in ps):
                    reachable.add(t)
                    changed = True
        stuck = [t for t in lines if t not in reachable]
        if not stuck:
            break
        for t in stuck:
            roots.add(t)
            cycle_promoted.append([t, pool[t]["name"], pool[t]["level"], pool[t]["attribute"]])
            del lines[t]

    assert set(pool_ids) == (set(roots) | set(lines)), "every pool node is a root or has lines"
    unreachable = pool_ids - (set(roots) | {t for t in lines})  # sanity, should be empty

    from collections import Counter
    cells = Counter((x["level"], x["attribute"]) for x in pool.values())
    pool_by_tier = Counter(x["level"] for x in pool.values())

    dataset = {
        "_meta": {
            "generated_from": "Digi-API (https://digi-api.com)",
            "note": "Non-commercial fan project. Pinned snapshot; do not fetch live at gen time.",
            "pool": "rookie-and-up, deduped",
            "gating": "primary_attribute; same-primary-attribute climb edges; HasAny not used",
            "excluded": "X-Antibody, parenthetical variants, missing level/attr, babies, Armor/Hybrid/Unknown tiers",
        },
        "level_tier": MVP_TIERS,
        "attributes": sorted({x["attribute"] for x in pool.values()}),
        "cell_counts": {f"{lv}|{at}": n for (lv, at), n in sorted(cells.items(), key=lambda kv: -kv[1])},
        "roots": sorted(roots),
        "lines": {str(t): ps for t, ps in sorted(lines.items())},
        "meta": {
            str(i): {k: x[k] for k in
                     ("name", "level", "tier", "attributes", "attribute", "types",
                      "fields", "year", "sprite", "xAntibody")}
            for i, x in sorted(pool.items())
        },
    }
    MVP.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "pool_size": len(pool),
        "pool_by_tier": dict(pool_by_tier.most_common()),
        "roots_total": len(roots),
        "rookies_as_roots": sum(1 for i in roots if pool[i]["level"] == "Rookie"),
        "climb_nodes": len(lines),
        "climb_edges": sum(len(v) for v in lines.values()),
        "forced_roots_no_prior": len(forced),
        "forced_roots": forced,
        "attribute_orphans_promoted": len(orphan),
        "attribute_orphans": orphan,
        "cycle_locked_promoted": len(cycle_promoted),
        "cycle_locked": cycle_promoted,
        "unreachable_after_build": len(unreachable),
    }
    CURATION.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {k: report[k] for k in
               ("pool_size", "pool_by_tier", "roots_total", "rookies_as_roots",
                "climb_nodes", "climb_edges", "forced_roots_no_prior",
                "attribute_orphans_promoted", "cycle_locked_promoted",
                "unreachable_after_build")}
    print("=== CURATED MVP DATASET ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote {MVP.name} ({len(pool)} Digimon) and {CURATION.name}", file=sys.stderr)


def main():
    refresh = "--refresh" in sys.argv
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw(refresh)
    res = analyse(raw)
    ANALYSIS.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {ANALYSIS}", file=sys.stderr)
    build_curated(raw)


if __name__ == "__main__":
    main()
