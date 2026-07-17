"""Loading of RIS records and circulation data."""

from itm_weeding.core import parse_ris, load_circulation, get_isbn
from itm_weeding.grouping import GroupIndexer
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


class BibData:
    """Bibliographic records loaded from RIS files, with grouping indices.

    ``process_records`` returns only the primary file's records (to be
    weeded); ``records`` covers all files for collection-wide statistics.
    """

    def __init__(self, ris_paths):
        self.records, self.primary_count = DataLoader.load_records(ris_paths)
        self.indexer = GroupIndexer(self.records)

    @property
    def process_records(self):
        """Records from the primary (first) RIS file — the ones to be weeded."""
        return self.records[: self.primary_count]


class UnicatData:
    """UniCat holdings results for a set of records, keyed by ISBN.

    Stores the final result string (``"held"``, ``"not_held"``, or ``None``)
    for each ISBN encountered in the primary records.
    """

    def __init__(self, results: dict):
        self._results = results  # isbn -> "held" | "not_held" | None

    def get(self, isbn: str):
        """Return the UniCat result for an ISBN, or None if unknown."""
        return self._results.get(isbn)


class UnicatDataLoader:
    """Fetches UniCat holdings data and builds a UnicatData lookup."""

    @staticmethod
    def load(process_records, unicat_lookup, unicat_cache, no_cache=False) -> "UnicatData":
        """Fetch missing ISBNs, populate cache, return a UnicatData lookup."""
        unique_isbns = {
            isbn
            for rec in process_records
            if (isbn := get_isbn(rec))
        }
        isbns_to_fetch = {
            isbn for isbn in unique_isbns
            if no_cache or not unicat_cache.get(isbn)
        }

        if not isbns_to_fetch:
            print("Pre-fetching UniCat data...")
            print("  All ISBNs already cached")
        else:
            print(f"Pre-fetching UniCat data for {len(isbns_to_fetch):,} ISBNs...")
            batch_results = unicat_lookup.batch_check_isbns(
                list(isbns_to_fetch),
                show_progress=True,
            )
            fetched = sum(1 for v in batch_results.values() if v is not None)
            print(f"  Fetched {fetched:,} results — storing in cache")
            for isbn, result in batch_results.items():
                unicat_cache.set(isbn, result)

        results = {}
        for isbn in unique_isbns:
            cached = unicat_cache.get(isbn)
            if cached:
                results[isbn] = cached.get("result")

        return UnicatData(results)


class CirculationData:
    """Loan records loaded from student and staff circulation files."""

    def __init__(self, borrowed: set):
        self.borrowed = borrowed


class CirculationDataLoader:
    """Loads circulation (loan) data from CSV files."""

    @staticmethod
    def load(students_path, staff_path) -> "CirculationData":
        """Load student and staff loan files into a CirculationData object."""
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
        return CirculationData(borrowed)
