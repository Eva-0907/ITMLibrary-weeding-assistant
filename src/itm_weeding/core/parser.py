"""RIS file parsing and circulation data loading."""

import re
import sys
from pathlib import Path

from .helpers import make_circ_key


def parse_ris(text):
    """Parse raw RIS text into a list of dictionary-based bibliographic records.

    The function splits the input into logical record blocks, reads each field
    line, and normalizes repeated tags into lists when needed. Records that
    contain a title-like field are retained for downstream processing.
    """
    records = []
    for block in re.split(r"\nER\s*-", text):
        rec = {}
        for line in block.strip().splitlines():
            m = re.match(r"^([A-Z][A-Z0-9])\s*-\s*(.*)$", line)
            if not m:
                continue
            tag, val = m.group(1), m.group(2).strip()
            if tag in rec:
                if isinstance(rec[tag], list):
                    rec[tag].append(val)
                else:
                    rec[tag] = [rec[tag], val]
            else:
                rec[tag] = val
        if rec.get("T1") or rec.get("TI"):
            records.append(rec)
    return records


def load_circulation(path, delimiter, b_col=1, c_col=2, y_col=3):
    """Load circulation history data from a CSV or TSV file.

    Each row is converted into a normalized circulation key of the form
    barnard|call_number|year, which can be matched against bibliographic
    records. Rows missing the required columns or call-number values are
    ignored.
    """
    borrowed = set()
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                cols = line.rstrip("\n").split(delimiter)
                if len(cols) <= max(b_col, c_col, y_col):
                    continue
                barnard = cols[b_col].strip()
                call_num = cols[c_col].strip()
                year = cols[y_col].strip()
                if barnard and call_num and re.search(r"\d", call_num):
                    borrowed.add(make_circ_key(barnard, call_num, year))
    except FileNotFoundError:
        print(f"  Warning: file not found: {path}", file=sys.stderr)
    return borrowed
