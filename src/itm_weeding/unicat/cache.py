"""JSON caching layer for UniCat lookup results."""

import json
from pathlib import Path
from datetime import datetime, timedelta


class UniCatCache:
    """Persist UniCat lookup results to disk so repeated runs can reuse them."""

    def __init__(self, cache_path="data/cache/unicat_cache.json", max_age_days=30):
        """Initialize the cache, loading any existing entries from disk."""
        self.cache_path = Path(cache_path)
        self.max_age = timedelta(days=max_age_days)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        """Load cached lookup data from the JSON file if it exists."""
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self):
        """Persist the current in-memory cache contents back to disk."""
        self.cache_path.write_text(json.dumps(self.data, indent=2))

    def get(self, isbn):
        """Return the cached UniCat result for an ISBN if it is still valid."""
        if isbn not in self.data:
            return None
        entry = self.data[isbn]
        timestamp = datetime.fromisoformat(entry.get("timestamp", datetime.now().isoformat()))
        if datetime.now() - timestamp > self.max_age:
            del self.data[isbn]
            self._save()
            return None
        return entry

    def set(self, isbn, result, url=""):
        """Store a UniCat lookup result for later reuse."""
        self.data[isbn] = {
            "result": result,
            "url": url,
            "timestamp": datetime.now().isoformat(),
        }
        self._save()

    def __len__(self):
        """Return the number of cached entries currently stored."""
        return len(self.data)

    def clear(self):
        """Remove all cached entries and rewrite the cache file."""
        self.data = {}
        self._save()

    def cleanup_expired(self):
        """Remove expired cache entries and return the number of deletions."""
        now = datetime.now()
        expired = [
            isbn
            for isbn, entry in self.data.items()
            if now - datetime.fromisoformat(entry.get("timestamp", "")) > self.max_age
        ]
        for isbn in expired:
            del self.data[isbn]
        if expired:
            self._save()
        return len(expired)
