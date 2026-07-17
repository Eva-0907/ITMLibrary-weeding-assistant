"""UniCat holdings data loading and lookup."""

from itm_weeding.core import get_isbn
from itm_weeding.unicat import UniCatCache, UniCatLookupConcurrent, UniCatLookupSequential


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

    def __init__(self, unicat_cache: UniCatCache, concurrent: bool = False, no_cache: bool = False):
        self._cache = unicat_cache
        self._no_cache = no_cache
        self._lookup = (
            UniCatLookupConcurrent(concurrency=10) if concurrent
            else UniCatLookupSequential()
        )
        if no_cache:
            print("UniCat cache DISABLED — all ISBNs will be fetched from API")
        elif len(unicat_cache) > 0:
            print(f"UniCat cache loaded: {len(unicat_cache)} entries")

    def load(self, process_records) -> UnicatData:
        """Fetch missing ISBNs, populate cache, return a UnicatData lookup."""
        unique_isbns = {
            isbn
            for rec in process_records
            if (isbn := get_isbn(rec))
        }
        isbns_to_fetch = {
            isbn for isbn in unique_isbns
            if self._no_cache or not self._cache.get(isbn)
        }

        if not isbns_to_fetch:
            print("Pre-fetching UniCat data...")
            print("  All ISBNs already cached")
        else:
            print(f"Pre-fetching UniCat data for {len(isbns_to_fetch):,} ISBNs...")
            batch_results = self._lookup.batch_check_isbns(
                list(isbns_to_fetch),
                show_progress=True,
            )
            fetched = sum(1 for v in batch_results.values() if v is not None)
            print(f"  Fetched {fetched:,} results — storing in cache")
            for isbn, result in batch_results.items():
                self._cache.set(isbn, result)

        results = {}
        for isbn in unique_isbns:
            cached = self._cache.get(isbn)
            if cached:
                results[isbn] = cached.get("result")

        return UnicatData(results)
