"""JSON caching layer for UniCat lookup results."""

import json
from pathlib import Path
from datetime import datetime, timedelta


class UniCatCache:
    """Simple JSON file cache for UniCat lookup results."""

    def __init__(self, cache_path="data/cache/unicat_cache.json", max_age_days=30):
        """Initialize cache.
        
        Args:
            cache_path: Path to cache JSON file
            max_age_days: Maximum age of cached entries in days
        """
        self.cache_path = Path(cache_path)
        self.max_age = timedelta(days=max_age_days)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        """Load cache from JSON file."""
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self):
        """Save cache to JSON file."""
        self.cache_path.write_text(json.dumps(self.data, indent=2))

    def get(self, isbn):
        """Get cached result for ISBN, if not expired."""
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
        """Store result in cache."""
        self.data[isbn] = {
            "result": result,
            "url": url,
            "timestamp": datetime.now().isoformat(),
        }
        self._save()

    def __len__(self):
        """Return number of cached entries."""
        return len(self.data)

    def clear(self):
        """Clear all cache entries."""
        self.data = {}
        self._save()

    def cleanup_expired(self):
        """Remove expired entries from cache."""
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
