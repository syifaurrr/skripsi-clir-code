"""
Duplicate Checker for LLM-Generated JSON Files
================================================
Checks for duplicates in JSON files with the structure:
  [{ "pos_id", "neg_id", "tipe_1": [...], "tipe_2": [...] }, ...]

Duplicate types checked:
  1.  Fully duplicate records
  2.  Duplicate pos_id (within field)
  3.  Duplicate neg_id (within field)
  4.  Duplicate tipe_1 items (within field)
  5.  Duplicate tipe_2 items (within field)
  6.  [INTER] pos_id == neg_id in same record
  7.  [INTER] pos_id of one record appears as neg_id in another
  8.  [INTER] tipe_1 item of one record appears in tipe_2 of another

Usage:
  python check_duplicates.py <path_to_json_file>
  python check_duplicates.py synthetic_query.json
  python check_duplicates.py synthetic_query.json --output report.txt
  python check_duplicates.py synthetic_query.json --fix --output cleaned.json
"""

import json
import argparse
from collections import defaultdict
from pathlib import Path


# ──────────────────────────────────────────────
# CORE DUPLICATE DETECTION
# ──────────────────────────────────────────────

def check_duplicates(data: list[dict]) -> dict:
    results = {}

    # ── Within-field duplicates ──
    results["full_record_duplicates"]   = _find_full_record_duplicates(data)
    results["duplicate_pos_id"]         = _find_scalar_field_duplicates(data, "pos_id")
    results["duplicate_neg_id"]         = _find_scalar_field_duplicates(data, "neg_id")
    results["duplicate_tipe_1_items"]   = _find_list_field_duplicates(data, "tipe_1")
    results["duplicate_tipe_2_items"]   = _find_list_field_duplicates(data, "tipe_2")

    # ── Intercategorical duplicates ──
    results["inter_pos_eq_neg"]         = _find_same_record_pos_neg_equal(data)
    results["inter_pos_id_in_neg_id"]   = _find_cross_id_duplicates(data)
    results["inter_tipe1_in_tipe2"]     = _find_cross_list_duplicates(data, "tipe_1", "tipe_2")

    return results


# ── Within-field helpers ──

def _find_full_record_duplicates(data):
    seen = {}
    duplicates = []
    for i, record in enumerate(data):
        key = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if key in seen:
            duplicates.append({"indices": [seen[key], i], "record": record})
        else:
            seen[key] = i
    return duplicates


def _find_scalar_field_duplicates(data, field):
    value_map = defaultdict(list)
    for i, record in enumerate(data):
        val = record.get(field)
        if val is not None:
            value_map[val].append(i)
    return [
        {"value": val, "indices": indices, "records": [data[i] for i in indices]}
        for val, indices in value_map.items() if len(indices) > 1
    ]


def _find_list_field_duplicates(data, field):
    value_map = defaultdict(list)
    for i, record in enumerate(data):
        for item in record.get(field, []):
            value_map[item].append(i)
    return [
        {
            "value": val,
            "indices": list(dict.fromkeys(indices)),
            "records": [data[i] for i in dict.fromkeys(indices)],
        }
        for val, indices in value_map.items() if len(indices) > 1
    ]


# ── Intercategorical helpers ──

def _find_same_record_pos_neg_equal(data):
    """pos_id == neg_id within the same record."""
    return [
        {"index": i, "value": d["pos_id"], "record": d}
        for i, d in enumerate(data)
        if d.get("pos_id") and d.get("pos_id") == d.get("neg_id")
    ]


def _find_cross_id_duplicates(data):
    """
    A page ID that appears as pos_id in one record AND as neg_id in another.
    This means the same passage is used as both a positive and a negative example.
    """
    pos_map = {d["pos_id"]: i for i, d in enumerate(data) if d.get("pos_id")}
    neg_map = {d["neg_id"]: i for i, d in enumerate(data) if d.get("neg_id")}

    conflicts = []
    seen = set()
    for val in pos_map:
        if val in neg_map and val not in seen:
            seen.add(val)
            i_pos = pos_map[val]
            i_neg = neg_map[val]
            conflicts.append({
                "value": val,
                "as_pos_in_index": i_pos,
                "as_neg_in_index": i_neg,
                "pos_record": data[i_pos],
                "neg_record": data[i_neg],
            })
    return conflicts


def _find_cross_list_duplicates(data, field_a, field_b):
    """
    Items that appear in field_a of one record AND field_b of another record.
    e.g. a tipe_1 keyword that also shows up inside a tipe_2 question.
    """
    map_a = defaultdict(list)
    map_b = defaultdict(list)

    for i, record in enumerate(data):
        for item in record.get(field_a, []):
            map_a[item].append(i)
        for item in record.get(field_b, []):
            map_b[item].append(i)

    conflicts = []
    for val in map_a:
        if val in map_b:
            indices_a = list(dict.fromkeys(map_a[val]))
            indices_b = list(dict.fromkeys(map_b[val]))
            conflicts.append({
                "value": val,
                f"in_{field_a}_records": indices_a,
                f"in_{field_b}_records": indices_b,
            })
    return conflicts


# ──────────────────────────────────────────────
# REPORT FORMATTING
# ──────────────────────────────────────────────

def format_report(data, results, filepath) -> str:
    lines = []
    W = 65

    def header(title):
        lines.append("\n" + "─" * W)
        lines.append(f"  {title}")
        lines.append("─" * W)

    lines.append("=" * W)
    lines.append("  DUPLICATE CHECK REPORT")
    lines.append(f"  File   : {filepath}")
    lines.append(f"  Records: {len(data)}")
    lines.append("=" * W)

    total_issues = 0

    # ── 1. Full record duplicates ──
    dups = results["full_record_duplicates"]
    total_issues += len(dups)
    header(f"[1] FULLY DUPLICATE RECORDS  →  {len(dups)} found")
    if dups:
        for d in dups:
            lines.append(f"    Indices {d['indices']}  |  pos_id: {d['record'].get('pos_id')}")
    else:
        lines.append("    ✓ None")

    # ── 2–3. Scalar field duplicates ──
    for n, field in enumerate(("pos_id", "neg_id"), start=2):
        dups = results[f"duplicate_{field}"]
        total_issues += len(dups)
        header(f"[{n}] DUPLICATE {field.upper()} (WITHIN FIELD)  →  {len(dups)} found")
        if dups:
            for d in dups:
                lines.append(f"    \"{d['value']}\"  →  indices {d['indices']}")
                for rec in d["records"]:
                    idx = d["indices"][d["records"].index(rec)]
                    lines.append(f"      Record {idx}: pos_id={rec.get('pos_id')}, neg_id={rec.get('neg_id')}")
        else:
            lines.append("    ✓ None")

    # ── 4–5. List field duplicates ──
    for n, field in enumerate(("tipe_1", "tipe_2"), start=4):
        dups = results[f"duplicate_{field}_items"]
        total_issues += len(dups)
        header(f"[{n}] DUPLICATE {field.upper()} ITEMS (WITHIN FIELD)  →  {len(dups)} found")
        if dups:
            for d in dups:
                lines.append(f"    \"{d['value']}\"")
                lines.append(f"    Appears in record indices: {d['indices']}")
                for idx, rec in zip(d["indices"], d["records"]):
                    lines.append(f"      Record {idx}: pos_id={rec.get('pos_id')}, neg_id={rec.get('neg_id')}")
        else:
            lines.append("    ✓ None")

    # ── 6. pos_id == neg_id in same record ──
    dups = results["inter_pos_eq_neg"]
    total_issues += len(dups)
    header(f"[6] [INTER] pos_id == neg_id IN SAME RECORD  →  {len(dups)} found")
    if dups:
        for d in dups:
            lines.append(f"    Record {d['index']}: pos_id = neg_id = \"{d['value']}\"")
    else:
        lines.append("    ✓ None")

    # ── 7. pos_id of one record appears as neg_id in another ──
    dups = results["inter_pos_id_in_neg_id"]
    total_issues += len(dups)
    header(f"[7] [INTER] pos_id APPEARS AS neg_id ACROSS RECORDS  →  {len(dups)} found")
    if dups:
        for d in dups:
            lines.append(f"    Page ID \"{d['value']}\"")
            lines.append(f"      As pos_id → Record {d['as_pos_in_index']}: "
                         f"pos_id={d['pos_record'].get('pos_id')}, neg_id={d['pos_record'].get('neg_id')}")
            lines.append(f"      As neg_id → Record {d['as_neg_in_index']}: "
                         f"pos_id={d['neg_record'].get('pos_id')}, neg_id={d['neg_record'].get('neg_id')}")
    else:
        lines.append("    ✓ None")

    # ── 8. tipe_1 item appears in tipe_2 of another record ──
    dups = results["inter_tipe1_in_tipe2"]
    total_issues += len(dups)
    header(f"[8] [INTER] tipe_1 ITEM APPEARS IN tipe_2 ACROSS RECORDS  →  {len(dups)} found")
    if dups:
        for d in dups:
            lines.append(f"    \"{d['value']}\"")
            lines.append(f"      In tipe_1 of records : {d['in_tipe_1_records']}")
            lines.append(f"      In tipe_2 of records : {d['in_tipe_2_records']}")
    else:
        lines.append("    ✓ None")

    # ── Summary ──
    lines.append("\n" + "=" * W)
    status = "⚠  DUPLICATES FOUND" if total_issues > 0 else "✓  NO DUPLICATES — file is clean"
    lines.append(f"  RESULT : {status}")
    if total_issues > 0:
        lines.append(f"  Total duplicate groups : {total_issues}")
    lines.append("=" * W)

    return "\n".join(lines)


# ──────────────────────────────────────────────
# AUTO-FIX  (removes fully duplicate records)
# ──────────────────────────────────────────────

def fix_duplicates(data):
    seen = set()
    cleaned, removed = [], 0
    for record in data:
        key = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            cleaned.append(record)
        else:
            removed += 1
    return cleaned, removed


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check LLM-generated JSON files for duplicate passages or records."
    )
    parser.add_argument("filepath", help="Path to the JSON file to check")
    parser.add_argument("--output", "-o", default=None,
                        help="Save report (.txt) or cleaned data (.json) to this path")
    parser.add_argument("--fix", action="store_true",
                        help="Remove fully duplicate records and save cleaned JSON to --output")
    args = parser.parse_args()

    path = Path(args.filepath)
    if not path.exists():
        print(f"Error: file not found → {path}")
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: expected a JSON array at the top level.")
        return

    results = check_duplicates(data)
    report  = format_report(data, results, str(path))
    print(report)

    if args.output:
        out_path = Path(args.output)
        if args.fix:
            cleaned, removed = fix_duplicates(data)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, ensure_ascii=False, indent=2)
            print(f"\n  Cleaned file saved → {out_path}  ({removed} full-duplicate records removed)")
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n  Report saved → {out_path}")


if __name__ == "__main__":
    main()