"""UniCat web scraping for Belgian library availability."""

import time
import random
import urllib.parse
import urllib3

import requests
from bs4 import BeautifulSoup
import aiohttp
from sparp.sparp import SPARP, ResponseState

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
})


def check_unicat_isbn(isbn, retries=3, debug=False):
    """Search UniCat by ISBN and check if any library holds it.
    
    Args:
        isbn: ISBN to search
        retries: Number of retry attempts on failure
        debug: Print debug information
    
    Returns:
        Tuple: ("held", None) if available, ("not_held", None) if sole/no holder,
               (None, error_msg) if request failed
    """
    url = f"https://www.unicat.be/uniCat?func=search&query={urllib.parse.quote(isbn)}"

    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=10, verify=False)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Check for checkAvailability link (indicates other libraries hold it)
            if soup.find("a", {"data-action": "checkAvailability"}):
                if debug:
                    print(f"  ISBN {isbn}: HELD (checkAvailability link found)")
                return ("held", None)

            # No availability link found
            if debug:
                print(f"  ISBN {isbn}: NOT_HELD (no checkAvailability link)")
            return ("not_held", None)

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait = random.uniform(2, 5)
                if debug:
                    print(f"  ISBN {isbn}: Retry {attempt + 1}/{retries} after {wait:.1f}s ({e})")
                time.sleep(wait)
            else:
                return (None, str(e))

    return (None, "Max retries exceeded")


def batch_check_unicat_isbns(isbns, concurrency=20, show_progress=False):
    """Batch check ISBNs using concurrent requests with SPARP.
    
    Args:
        isbns: List of ISBNs to check
        concurrency: Maximum concurrent requests
        show_progress: Show progress bar
    
    Returns:
        Dict mapping ISBN -> ("held" | "not_held" | None)
    """
    if not isbns:
        return {}
    
    # Build request configs for SPARP (without isbn in the dict itself)
    requests_config = [
        {
            "method": "GET",
            "url": f"https://www.unicat.be/uniCat?func=search&query={urllib.parse.quote(isbn)}",
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-GB,en;q=0.9",
            },
        }
        for isbn in isbns
    ]
    
    # Define response handler
    def inspect_response(response: aiohttp.ClientResponse) -> ResponseState:
        if response.status == 200:
            return ResponseState.SUCCESS
        if response.status == 429 or response.status == 502 or response.status == 503:
            return ResponseState.SOFT_FAIL  # Retry on rate limit / server errors
        return ResponseState.HARD_FAIL
    
    # Define response parser
    async def parse_response(req_config: dict, response: aiohttp.ClientResponse) -> dict:
        text = await response.text()
        soup = BeautifulSoup(text, "html.parser")
        
        # Check for checkAvailability link
        has_availability = bool(soup.find("a", {"data-action": "checkAvailability"}))
        
        # Extract ISBN from URL query parameter
        url = req_config["url"]
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        isbn = query_params.get("query", [""])[0]
        
        return {
            "isbn": isbn,
            "result": "held" if has_availability else "not_held",
        }
    
    # Run parallel requests
    result = SPARP(
        requests_config,
        inspect_response=inspect_response,
        parse_response=parse_response,
        concurrency=concurrency,
        max_retries_by_soft_fail=3,
        max_retries_by_timeout=3,
        show_progress_bar=show_progress,
        estimated_input_collection_size=len(isbns),
        timeout_s=15.0,
    ).main()
    
    # Build result mapping
    results = {}
    for item in result.success:
        results[item["isbn"]] = item["result"]
    
    # Mark failed lookups as None
    for req in result.failed:
        # Extract ISBN from URL
        url = req.get("url", "")
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        isbn = query_params.get("query", [""])[0]
        if isbn:
            results[isbn] = None
    
    for req in result.max_retries_soft_fail_reached:
        url = req.get("url", "")
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        isbn = query_params.get("query", [""])[0]
        if isbn:
            results[isbn] = None
    
    for req in result.max_retries_timeout_reached:
        url = req.get("url", "")
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        isbn = query_params.get("query", [""])[0]
        if isbn:
            results[isbn] = None
    
    return results
