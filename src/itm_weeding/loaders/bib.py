"""Bibliographic record loading from RIS files."""

from itm_weeding.core import parse_ris
from itm_weeding.grouping import GroupIndexer
from itm_weeding.text_utils import TextUtils


class BibDataLoader:
    """Reads and parses RIS files into record dicts."""

    @staticmethod
    def load(ris_paths):
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


class BibData:
    """Bibliographic records loaded from RIS files, with grouping indices.

    ``process_records`` returns only the primary file's records (to be
    weeded); ``records`` covers all files for collection-wide statistics.
    """

    def __init__(self, ris_paths):
        self.records, self.primary_count = BibDataLoader.load(ris_paths)
        self.indexer = GroupIndexer(self.records)

    @property
    def process_records(self):
        """Records from the primary (first) RIS file — the ones to be weeded."""
        return self.records[: self.primary_count]
