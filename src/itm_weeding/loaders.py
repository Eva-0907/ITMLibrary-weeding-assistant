"""Loading of RIS records and circulation data."""

from itm_weeding.core import parse_ris, load_circulation
from itm_weeding.text_utils import TextUtils


class DataLoader:
    """Loads bibliographic records and circulation (loan) data."""

    @staticmethod
    def load_records(ris_paths):
        """Read and parse all RIS files. Returns (all_records, primary_count)."""
        all_records = []
        primary_count = 0
        for file_idx, ris_path in enumerate(ris_paths):
            print(f"Reading {ris_path}...")
            ris_text = TextUtils.read_ris_file(ris_path)
            recs = parse_ris(ris_text)
            print(f"  Parsed {len(recs):,} records")
            all_records.extend(recs)
            if file_idx == 0:
                primary_count = len(recs)

        if len(ris_paths) > 1:
            print(
                f"  Total: {len(all_records):,} records across "
                f"{len(ris_paths)} file(s)"
            )
            print(
                f"  Processing first file only ({primary_count:,} records); "
                f"rest used for collection stats"
            )
        return all_records, primary_count

    @staticmethod
    def load_borrowed(students_path, staff_path):
        """Load circulation data from student and staff loan files."""
        borrowed = set()
        if students_path:
            print(f"Loading student loans: {students_path}")
            s = load_circulation(students_path, delimiter=";")
            borrowed |= s
            print(f"  {len(s):,} student loan records")
        if staff_path:
            print(f"Loading staff loans: {staff_path}")
            s = load_circulation(staff_path, delimiter="\t")
            borrowed |= s
            print(f"  {len(s):,} staff loan records")
        if borrowed:
            print(f"  {len(borrowed):,} unique circulated items total")
        return borrowed
