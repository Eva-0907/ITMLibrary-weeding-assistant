"""UniCat SRU API lookup for Belgian library availability."""

import time
import random
import urllib.parse
import xml.etree.ElementTree as ET

import requests
import aiohttp
from sparp import SPARP, ResponseState

_SRU_BASE = "http://www.unicat.be/sru"
_SRU_NS = "http://www.loc.gov/zing/srw/"


def _progress_bar(current: int, total: int, width: int = 20) -> str:
    """Render a simple text progress bar."""
    if total <= 0:
        return f"[{'-' * width}] 0/{total} (0%)"
    filled = max(0, min(width, int(round(current / total * width))))
    bar = "#" * filled + "-" * (width - filled)
    percent = int(round(current / total * 100))
    return f"[{bar}] {current}/{total} ({percent}%)"


class UniCatLookupBase:
    """Shared helpers for UniCat SRU lookups.

    Subclasses implement :meth:`batch_check_isbns` with either a sequential or
    a concurrent strategy. The single-ISBN :meth:`check_isbn` is shared.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_url(self, isbn: str) -> str:
        """Build the SRU request URL for a single ISBN."""
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": f"isbn={isbn}",
            "maximumRecords": "1",
        }
        return f"{_SRU_BASE}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _parse_count(xml_text: str):
        """Extract the numberOfRecords value from an SRU XML response."""
        try:
            root = ET.fromstring(xml_text)
            el = root.find(f"{{{_SRU_NS}}}numberOfRecords")
            if el is not None and el.text is not None:
                return int(el.text)
        except (ET.ParseError, ValueError):
            pass
        return None

    @staticmethod
    def _isbn_from_url(url: str) -> str:
        """Extract the ISBN from a request URL query string."""
        raw_query = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query
        ).get("query", [""])[0]
        return raw_query.removeprefix("isbn=")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_isbn(self, isbn: str, retries: int = 3, debug: bool = False):
        """Check whether a single ISBN is held by any Belgian library.

        The method performs a direct request to UniCat, retries transient
        failures, and returns a simple held/not-held result or an error string.
        """
        url = self._build_url(isbn)

        for attempt in range(retries):
            try:
                resp = self._session.get(url, timeout=self.timeout)
                resp.raise_for_status()

                count = self._parse_count(resp.text)
                if count is None:
                    return (None, "Failed to parse SRU response")

                result = "held" if count > 0 else "not_held"
                if debug:
                    print(f"  ISBN {isbn}: {result.upper()} (numberOfRecords={count})")
                return (result, None)

            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    wait = random.uniform(2, 5)
                    if debug:
                        print(f"  ISBN {isbn}: Retry {attempt + 1}/{retries} after {wait:.1f}s ({e})")
                    time.sleep(wait)
                else:
                    return (None, str(e))

        return (None, "Max retries exceeded")

    def batch_check_isbns(self, isbns: list, show_progress: bool = False) -> dict:
        """Check many ISBNs. Returns dict ISBN -> "held" | "not_held" | None."""
        raise NotImplementedError


class UniCatLookupSequential(UniCatLookupBase):
    """Checks ISBNs one at a time (no concurrency)."""

    def batch_check_isbns(self, isbns: list, show_progress: bool = False) -> dict:
        """Check ISBNs sequentially, one request at a time.

        Returns:
            Dict mapping ISBN -> "held" | "not_held" | None
        """
        if not isbns:
            return {}

        results = {}
        total = len(isbns)
        for index, isbn in enumerate(isbns, start=1):
            result, _ = self.check_isbn(isbn, retries=2)
            results[isbn] = result
            if show_progress:
                print(f"\r  {_progress_bar(index, total)}", end="", flush=True)
        if show_progress:
            print()

        return results


class UniCatLookupConcurrent(UniCatLookupBase):
    """Checks ISBNs concurrently via SPARP."""

    def __init__(self, concurrency: int = 20, timeout: float = 10.0):
        super().__init__(timeout=timeout)
        self.concurrency = concurrency

    @staticmethod
    def _inspect_response(response: aiohttp.ClientResponse) -> ResponseState:
        if response.status == 200:
            return ResponseState.SUCCESS
        if response.status in (429, 502, 503):
            return ResponseState.SOFT_FAIL
        return ResponseState.HARD_FAIL

    async def _parse_response(self, req_config: dict, response: aiohttp.ClientResponse) -> dict:
        text = await response.text()
        count = self._parse_count(text)
        isbn = self._isbn_from_url(req_config["url"])
        return {
            "isbn": isbn,
            "result": ("held" if count > 0 else "not_held") if count is not None else None,
        }

    def batch_check_isbns(self, isbns: list, show_progress: bool = False) -> dict:
        """Batch-check ISBNs concurrently via SPARP.

        This uses the SPARP library to issue requests concurrently, which is much
        faster for large batches but more complex than the single-ISBN flow.
        """
        if not isbns:
            return {}

        requests_config = [
            {"method": "GET", "url": self._build_url(isbn)}
            for isbn in isbns
        ]

        result = SPARP(
            inspect_response=self._inspect_response,
            parse_response_fn=self._parse_response,
            concurrency=self.concurrency,
            max_retries_when_soft_fail=3,
            max_retries_on_timeout=3,
            show_progress_bar=show_progress,
            timeout_s=self.timeout,
        ).run(
            requests_config,
            estimated_input_collection_size=len(isbns),
        )

        results = {item["isbn"]: item["result"] for item in result.success}

        for item in result.failed:
            isbn = item.get("isbn")
            if isbn:
                results[isbn] = None

        for req in (*result.max_retries_soft_fail_reached, *result.max_retries_timeout_reached):
            isbn = self._isbn_from_url(req.get("url", ""))
            if isbn:
                results[isbn] = None

        return results
