"""
Duplicate Checker for LLM-Generated JSON Files
================================================
Checks for duplicates in JSON files with the structure:
  [{ "pos_id", "neg_id", "tipe_1": [...], "tipe_2": [...] }, ...]

Usage:
  python check_duplicates.py <path_to_json_file>
  python check_duplicates.py synthetic_query.json
  python check_duplicates.py synthetic_query.json --output report.txt
  python check_duplicates.py synthetic_query.json --fix --output cleaned.json
"""

import json
import argparse
from collections import defaultdict, Counter
from pathlib import Path


# ──────────────────────────────────────────────
# CORE DUPLICATE DETECTION
# ──────────────────────────────────────────────

def check_duplicates(data: list[dict]) -> dict:
    """
    Run all duplicate checks and return a structured report dict.
    """
    results = {}

    # 1. Fully duplicate records
    results["full_record_duplicates"] = _find_full_record_duplicates(data)

    # 2. Duplicate scalar fields (pos_id, neg_id)
    for field in ("pos_id", "neg_id"):
        results[f"duplicate_{field}"] = _find_scalar_field_duplicates(data, field)

    # 3. Duplicate items inside list fields (tipe_1, tipe_2)
    for field in ("tipe_1", "tipe_2"):
        results[f"duplicate_{field}_items"] = _find_list_field_duplicates(data, field)

    return results


def _find_full_record_duplicates(data: list[dict]) -> list[dict]:
    seen = {}
    duplicates = []
    for i, record in enumerate(data):
        key = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if key in seen:
            duplicates.append({
                "indices": [seen[key], i],
                "record": record,
            })
        else:
            seen[key] = i
    return duplicates


def _find_scalar_field_duplicates(data: list[dict], field: str) -> list[dict]:
    value_map = defaultdict(list)
    for i, record in enumerate(data):
        val = record.get(field)
        if val is not None:
            value_map[val].append(i)

    return [
        {"value": val, "indices": indices, "records": [data[i] for i in indices]}
        for val, indices in value_map.items()
        if len(indices) > 1
    ]


def _find_list_field_duplicates(data: list[dict], field: str) -> list[dict]:
    value_map = defaultdict(list)
    for i, record in enumerate(data):
        for item in record.get(field, []):
            value_map[item].append(i)

    return [
        {"value": val, "indices": list(dict.fromkeys(indices)),  # preserve order, dedupe
         "records": [data[i] for i in dict.fromkeys(indices)]}
        for val, indices in value_map.items()
        if len(indices) > 1
    ]


# ──────────────────────────────────────────────
# REPORT FORMATTING
# ──────────────────────────────────────────────

def format_report(data: list[dict], results: dict, filepath: str) -> str:
    lines = []
    lines.append("=" * 65)
    lines.append("  DUPLICATE CHECK REPORT")
    lines.append(f"  File   : {filepath}")
    lines.append(f"  Records: {len(data)}")
    lines.append("=" * 65)

    total_issues = 0

    # ── Full record duplicates ──
    full_dups = results["full_record_duplicates"]
    total_issues += len(full_dups)
    lines.append(f"\n[1] FULLY DUPLICATE RECORDS  →  {len(full_dups)} found")
    if full_dups:
        for dup in full_dups:
            lines.append(f"    Indices {dup['indices']}  |  pos_id: {dup['record'].get('pos_id')}")
    else:
        lines.append("    ✓ None")

    # ── Scalar field duplicates ──
    for field in ("pos_id", "neg_id"):
        key = f"duplicate_{field}"
        dups = results[key]
        total_issues += len(dups)
        lines.append(f"\n[{'2' if field == 'pos_id' else '3'}] DUPLICATE {field.upper()}  →  {len(dups)} found")
        if dups:
            for dup in dups:
                lines.append(f"    \"{dup['value']}\"  →  indices {dup['indices']}")
                for rec in dup["records"]:
                    lines.append(f"      Record idx {dup['indices'][dup['records'].index(rec)]}: "
                                 f"pos_id={rec.get('pos_id')}, neg_id={rec.get('neg_id')}")
        else:
            lines.append("    ✓ None")

    # ── List field duplicates ──
    section_num = 4
    for field in ("tipe_1", "tipe_2"):
        key = f"duplicate_{field}_items"
        dups = results[key]
        total_issues += len(dups)
        lines.append(f"\n[{section_num}] DUPLICATE {field.upper()} ITEMS  →  {len(dups)} found")
        section_num += 1
        if dups:
            for dup in dups:
                lines.append(f"    \"{dup['value']}\"")
                lines.append(f"    Appears in record indices: {dup['indices']}")
                for idx, rec in zip(dup["indices"], dup["records"]):
                    lines.append(f"      Record {idx}: pos_id={rec.get('pos_id')}, neg_id={rec.get('neg_id')}")
        else:
            lines.append("    ✓ None")

    # ── Summary ──
    lines.append("\n" + "=" * 65)
    status = "⚠  DUPLICATES FOUND" if total_issues > 0 else "✓  NO DUPLICATES — file is clean"
    lines.append(f"  RESULT : {status}")
    if total_issues > 0:
        lines.append(f"  Total duplicate groups : {total_issues}")
    lines.append("=" * 65)

    return "\n".join(lines)


# ──────────────────────────────────────────────
# AUTO-FIX  (optional)
# ──────────────────────────────────────────────

def fix_duplicates(data: list[dict]) -> tuple[list[dict], int]:
    """
    Remove fully duplicate records (keep first occurrence).
    Returns (cleaned_data, num_removed).
    """
    seen = set()
    cleaned = []
    removed = 0
    for record in data:
        key = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            cleaned.append(record)
        else:
            removed += 1
    return cleaned, removed


# ──────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check LLM-generated JSON files for duplicate passages or records."
    )
    parser.add_argument("filepath", help="Path to the JSON file to check")
    parser.add_argument(
        "--output", "-o",
        help="Save report (txt) or cleaned data (json) to this path",
        default=None,
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Remove fully duplicate records and save cleaned JSON to --output path",
    )
    args = parser.parse_args()

    # Load
    path = Path(args.filepath)
    if not path.exists():
        print(f"Error: file not found → {path}")
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: expected a JSON array at the top level.")
        return

    # Check
    results = check_duplicates(data)
    report = format_report(data, results, str(path))
    print(report)

    # Save report or cleaned file
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
