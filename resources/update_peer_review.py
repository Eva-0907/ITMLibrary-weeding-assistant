print("Script started")
import argparse; print("argparse OK")
import csv; print("csv OK")
import getpass; print("getpass OK")
import sys; print("sys OK")
import time; print("time OK")
import requests; print("requests OK")
print("All imports OK")
"""
Pure API – Bulk update peerReview to false
==========================================
Usage:
    python update_peer_review.py --csv path/to/report.csv

Requirements:
    pip install requests

The script prompts for your API key at runtime; it is never stored.

CSV requirements:
    The file must contain a column named 'UUID' (case-insensitive).
    It can contain any other columns – they are ignored.
"""

import argparse
import csv
import getpass
import sys
import time

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_URL = "https://pure.itg.be/ws/api"
ENDPOINT = "/research-outputs/{uuid}"

# How many seconds to wait between requests (be kind to the server)
REQUEST_DELAY = 0.25
# ──────────────────────────────────────────────────────────────────────────────


def load_uuids(csv_path: str) -> list[str]:
    """Read UUIDs from the CSV exported from Pure."""
    uuids = []
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        # Normalise header names to upper-case for robustness
        headers = {h.strip().upper(): h for h in reader.fieldnames or []}
        if "UUID" not in headers:
            sys.exit(
                f"ERROR: No 'UUID' column found in {csv_path}.\n"
                f"       Columns detected: {list(reader.fieldnames)}"
            )
        uuid_col = headers["UUID"]
        for row in reader:
            val = row[uuid_col].strip()
            if val:
                uuids.append(val)
    return uuids


def update_record(session: requests.Session, uuid: str) -> tuple[bool, str]:
    """
    Send a PUT request to set peerReview=false for one research output.
    Returns (success: bool, message: str).
    """
    url = BASE_URL + ENDPOINT.format(uuid=uuid)
    payload = {"peerReview": False}

    try:
        response = session.put(url, json=payload, timeout=30)
        if response.status_code in (200, 204):
            return True, f"OK ({response.status_code})"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except requests.RequestException as exc:
        return False, f"Request error: {exc}"


def main():
    parser = argparse.ArgumentParser(
        description="Bulk-set peerReview=false on Pure research outputs."
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="FILE",
        help="Path to the CSV file exported from Pure (must contain a UUID column).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be updated without making any API calls.",
    )
    args = parser.parse_args()

    # Prompt for API key (hidden input where supported, visible fallback otherwise)
    api_key = input("Enter your PURE API key:")
    if not api_key.strip():
        sys.exit("ERROR: API key cannot be empty.")

    # Load UUIDs
    uuids = load_uuids(args.csv)
    if not uuids:
        sys.exit("ERROR: No UUIDs found in the CSV file.")

    print(f"\nRecords to update: {len(uuids)}")
    if args.dry_run:
        print("DRY RUN – no changes will be made.\n")
        for uuid in uuids:
            print(f"  Would update: {uuid}")
        return

    # Set up session with auth header
    session = requests.Session()
    session.headers.update(
        {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    # Process records
    success_count = 0
    failure_count = 0
    failures = []

    print("\nStarting updates…\n")
    for i, uuid in enumerate(uuids, start=1):
        ok, msg = update_record(session, uuid)
        status = "✓" if ok else "✗"
        print(f"  [{i:>4}/{len(uuids)}] {status}  {uuid}  {msg}")
        if ok:
            success_count += 1
        else:
            failure_count += 1
            failures.append((uuid, msg))
        time.sleep(REQUEST_DELAY)

    # Summary
    print(f"\n{'─'*60}")
    print(f"Done.  Updated: {success_count}  |  Failed: {failure_count}")
    if failures:
        print("\nFailed records:")
        for uuid, msg in failures:
            print(f"  {uuid}: {msg}")
if __name__ == "__main__":
    main()
