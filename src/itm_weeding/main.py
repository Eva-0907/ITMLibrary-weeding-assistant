#!/usr/bin/env python3
"""
ITM Library Weeding Assistant — Main CLI Entry Point
Tropical Medicine & Global Health collection at ITG Antwerp

Usage:
    python -m itm_weeding.main <ris_file>
    python -m itm_weeding.main <ris_file> --students <csv> --staff <csv> --out <xlsx>
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from itm_weeding.core import (
    parse_ris,
    load_circulation,
    apply_rules,
    get_year,
    get_isbn,
    get_authors,
    barnard_label,
    base_barnard,
    gf,
)
from itm_weeding.report import export_xlsx
from itm_weeding.unicat import UniCatCache, UniCatLookup


def normalise_title(title, max_length=60):
    """Normalise title for edition grouping by removing edition markers."""
    import re
    t = title.lower()
    # Remove edition markers
    t = re.sub(
        r"[;,]\s*(\d+(st|nd|rd|th)?\.?\s*(ed|edition|éd|uitgave|druk|aufl).*)", "", t
    )
    t = re.sub(
        r"\s*(\d+(st|nd|rd|th)?\.?\s*(ed|edition|éd|uitgave|druk|aufl).*)", "", t
    )
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_length]


def get_edition_num(rec):
    """Extract edition number from record title."""
    import re
    title = gf(rec, "T1", "TI")
    m = re.search(r"(\d+)(st|nd|rd|th)?\s*(ed|edition|éd|uitgave|druk|aufl)", title, re.I)
    if m:
        return int(m.group(1))
    return 1


def normalise_volume_title(title, max_length=60):
    """Normalise title for volume grouping by removing volume markers."""
    import re
    t = title.lower()
    t = re.sub(
        r"[.,;]?\s*(volume|vol|deel|band|tome|part|partie|bd|fasc)\s*\.?\s*([ivxlcdm\d]+).*",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max_length]


def normalise_author(rec):
    """Normalise author for translation grouping."""
    import re
    a = gf(rec, "A1", "A2").lower()
    a = re.sub(r"[^a-z ]", "", a).strip()
    return " ".join(a.split()[:2])


def read_ris_file(path):
    """Read RIS file with auto-detected encoding."""
    for enc in ("utf-8-sig", "utf-8", "cp850", "windows-1252"):
        try:
            text = Path(path).read_text(encoding=enc)
            if "�" not in text:
                print(f"  Encoding detected: {enc}")
                return text
        except (UnicodeDecodeError, LookupError):
            continue
    text = Path(path).read_text(encoding="cp850", errors="replace")
    print("  Encoding detected: cp850 (fallback)")
    return text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ITM Library Weeding Agent — Tropical Medicine Collection"
    )
    parser.add_argument(
        "ris",
        help="Path to .ris file(s) — space-separated for multiple files",
        nargs="+",
    )
    parser.add_argument("--students", help="Student loans CSV (semicolon-delimited)")
    parser.add_argument("--staff", help="Staff loans CSV/TSV (tab-delimited)")
    parser.add_argument(
        "--out",
        default="data/output/weeding_report.xlsx",
        help="Output XLSX filename",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable UniCat cache (force re-lookup all ISBNs)",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Use concurrent SPARP batch lookups for UniCat (faster)",
    )
    args = parser.parse_args()

    # Initialize UniCat cache and lookup client
    unicat_cache = UniCatCache()
    unicat = UniCatLookup(concurrency=20)
    if args.no_cache:
        print("UniCat cache DISABLED — all ISBNs will be fetched from API")
    elif len(unicat_cache) > 0:
        print(f"UniCat cache loaded: {len(unicat_cache)} entries")

    # Load RIS
    all_records = []
    primary_count = 0
    for file_idx, ris_path in enumerate(args.ris):
        print(f"Reading {ris_path}...")
        ris_text = read_ris_file(ris_path)
        recs = parse_ris(ris_text)
        print(f"  Parsed {len(recs):,} records")
        all_records.extend(recs)
        if file_idx == 0:
            primary_count = len(recs)

    records = all_records
    if len(args.ris) > 1:
        print(f"  Total: {len(records):,} records across {len(args.ris)} file(s)")
        print(
            f"  Processing first file only ({primary_count:,} records); rest used for collection stats"
        )

    # Load circulation data
    borrowed = set()
    if args.students:
        print(f"Loading student loans: {args.students}")
        s = load_circulation(args.students, delimiter=";")
        borrowed |= s
        print(f"  {len(s):,} student loan records")
    if args.staff:
        print(f"Loading staff loans: {args.staff}")
        s = load_circulation(args.staff, delimiter="\t")
        borrowed |= s
        print(f"  {len(s):,} staff loan records")
    if borrowed:
        print(f"  {len(borrowed):,} unique circulated items total")

    # Pre-compute ISBN counts for duplicate detection
    isbn_counts = {}
    for rec in records:
        isbn = get_isbn(rec)
        if isbn:
            isbn_counts[isbn] = isbn_counts.get(isbn, 0) + 1

    # Pre-compute Barnard class counts for scarcity protection
    barnard_counts = {}
    for rec in records:
        bc = base_barnard(gf(rec, "U4"))
        if bc:
            barnard_counts[bc] = barnard_counts.get(bc, 0) + 1

    # Pre-compute edition groups
    edition_groups = defaultdict(list)
    for i, rec in enumerate(records):
        title = gf(rec, "T1", "TI")
        if not title:
            continue
        key = normalise_title(title)
        if key:
            edition_groups[key].append(i)

    older_edition_indices = set()
    for key, indices in edition_groups.items():
        if len(indices) < 2:
            continue
        def sort_key(i):
            ed = get_edition_num(records[i])
            yr = get_year(records[i]) or 0
            return (ed if ed > 1 else 0, yr)
        sorted_indices = sorted(indices, key=sort_key, reverse=True)
        newest = sorted_indices[0]
        for older in sorted_indices[1:]:
            older_edition_indices.add(older)

    # Pre-compute volume groups
    volume_groups = defaultdict(list)
    for i, rec in enumerate(records):
        title = gf(rec, "T1", "TI")
        if not title:
            continue
        key = normalise_volume_title(title)
        base = normalise_title(title)
        if key and key != base:
            volume_groups[key].append(i)

    volume_set_indices = {}
    for key, indices in volume_groups.items():
        if len(indices) > 1:
            for i in indices:
                volume_set_indices[i] = key

    # Pre-compute translation groups
    translation_groups = defaultdict(list)
    for i, rec in enumerate(records):
        author = normalise_author(rec)
        year = str(get_year(rec) or "")
        barnard = gf(rec, "U4").strip().upper()[:3]
        lang = gf(rec, "U3").strip().lower()
        if author and year and barnard:
            key = f"{author}|{year}|{barnard}"
            translation_groups[key].append((i, lang))

    ENGLISH_VARIANTS = {"english", "eng", "en", "anglais", "engels"}
    translation_weed_indices = set()
    for key, items in translation_groups.items():
        if len(items) < 2:
            continue
        langs = [lang for _, lang in items]
        has_english = any(l in ENGLISH_VARIANTS for l in langs)
        has_multiple_langs = len(set(langs)) > 1
        if has_english and has_multiple_langs:
            for i, lang in items:
                if lang not in ENGLISH_VARIANTS:
                    translation_weed_indices.add(i)

    # Process
    process_records = records[:primary_count]
    print(f"\nProcessing {len(process_records):,} records...")

    # ── Phase 1: collect UniCat data ────────────────────────────────────────
    # Gather all ISBNs that need a result.
    # If cache is enabled, use whatever is already stored; if not, always query the API.
    all_isbns = [get_isbn(rec) for rec in process_records]
    unique_isbns = {isbn for isbn in all_isbns if isbn}

    isbns_to_fetch = {
        isbn for isbn in unique_isbns
        if args.no_cache or not unicat_cache.get(isbn)
    }

    if isbns_to_fetch:
        print(f"Pre-fetching UniCat data for {len(isbns_to_fetch):,} ISBNs...")
        if args.concurrent:
            batch_results = unicat.batch_check_isbns(
                list(isbns_to_fetch),
                show_progress=True,
            )
        else:
            batch_results = {}
            for isbn in isbns_to_fetch:
                result, _ = unicat.check_isbn(isbn, retries=2)
                batch_results[isbn] = result

        fetched = sum(1 for v in batch_results.values() if v is not None)
        print(f"  Fetched {fetched:,} results — storing in cache")
        for isbn, result in batch_results.items():
            unicat_cache.set(isbn, result)
    else:
        print("Pre-fetching UniCat data...")
        print("  All ISBNs already cached")

    # ── Phase 2: process records — always read from in-memory cache ─────────
    
    t0 = datetime.now()
    output_rows = []
    counts = {"KEEP": 0, "WEED": 0, "REVIEW": 0, "SKIP": 0}

    for i, rec in enumerate(process_records):
        result = apply_rules(
            rec,
            records,
            borrowed,
            isbn_counts,
            older_edition=(i in older_edition_indices),
            translation_duplicate=(i in translation_weed_indices),
            barnard_counts=barnard_counts,
        )
        rec_val = result["recommendation"]
        counts[rec_val] = counts.get(rec_val, 0) + 1

        isbn = get_isbn(rec)

        # Phase 2: always read from cache (populated in phase 1)
        unicat_result = None
        if isbn:
            cached = unicat_cache.get(isbn)
            if cached:
                unicat_result = cached.get("result")
        
        output_rows.append(
            {
                "row_index": i,
                "rec": rec,
                "result": result,
                "title": gf(rec, "T1", "TI") or "Untitled",
                "author": get_authors(rec),
                "year": get_year(rec) or "",
                "rec_type": gf(rec, "TY").upper(),
                "isbn": isbn,
                "location": gf(rec, "U2").strip(),
                "unicat_result": unicat_result,
            }
        )

        if (i + 1) % 100 == 0 or (i + 1) == len(records):
            elapsed = (datetime.now() - t0).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(
                f"  {i+1:>6,} / {len(records):,}  "
                f"KEEP={counts['KEEP']}  WEED={counts['WEED']}  "
                f"REVIEW={counts['REVIEW']}  SKIP={counts['SKIP']}  "
                f"({rate:.0f}/s)"
            )

    # UniCat cache statistics
    unicat_held = sum(1 for row in output_rows if row.get("unicat_result") == "held")
    unicat_checked = sum(1 for row in output_rows if row.get("unicat_result") is not None)
    if unicat_checked:
        print(f"  UniCat: {unicat_held:,} items held in Belgian libraries ({unicat_checked:,} checked)")

    # ── Second pass: upgrade WEED volumes to KEEP if another volume is kept ──
    kept_volume_groups = set()
    for row in output_rows:
        i = row["row_index"]
        if row["result"]["recommendation"] == "KEEP" and i in volume_set_indices:
            kept_volume_groups.add(volume_set_indices[i])

    if kept_volume_groups:
        upgraded = 0
        for row in output_rows:
            i = row["row_index"]
            if (
                row["result"]["recommendation"] == "WEED"
                and i in volume_set_indices
                and volume_set_indices[i] in kept_volume_groups
            ):
                row["result"]["recommendation"] = "KEEP"
                row["result"]["reasoning"] += (
                    " | Kept: part of multi-volume set where another volume is kept."
                )
                row["result"]["flags"].append(
                    {
                        "criterion": "Volume set",
                        "detail": "Part of multi-volume set — another volume is kept",
                        "severity": "keep",
                    }
                )
                upgraded += 1
        if upgraded:
            print(f"  Volume sets: {upgraded} volumes upgraded from WEED to KEEP")

    # Report translation duplicates
    trans_weeded = sum(
        1
        for row in output_rows
        if any(f["criterion"] == "Translation" for f in row["result"]["flags"])
    )
    if trans_weeded:
        print(f"  Translations: {trans_weeded} non-English duplicates flagged")

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\nDone in {elapsed:.1f}s  ({len(process_records)/elapsed:.0f} records/sec)")
    print(f"  KEEP:   {counts['KEEP']:>6,}")
    print(f"  WEED:   {counts['WEED']:>6,}")
    print(f"  REVIEW: {counts['REVIEW']:>6,}")
    print(f"  SKIP:   {counts['SKIP']:>6,}")

    # Export
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting to {args.out}...")
    export_xlsx(output_rows, args.out)
    print(f"Done — {args.out}")


if __name__ == "__main__":
    main()
