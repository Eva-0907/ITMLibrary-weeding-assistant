"""Helper functions for record processing and classification."""

import re
import urllib.parse
import unicodedata

from itm_weeding.config.barnard import BARNARD, RETENTION_FLAGS
from itm_weeding.config.rules_data import HISTORICAL_TITLES, OUTBREAK_TIMELINE


def gf(rec, *tags):
    """Get first non-empty value from record by tag priority."""
    for t in tags:
        v = rec.get(t)
        if v:
            return v[0] if isinstance(v, list) else v
    return ""


def barnard_label(code):
    """Format Barnard code with human-readable label."""
    if not code:
        return ""
    c = code.strip().upper()
    if c in BARNARD:
        return f"{c} — {BARNARD[c]}"
    for i in range(len(c) - 1, 0, -1):
        p = c[:i]
        if p in BARNARD:
            return f"{c} — {BARNARD[p]}"
    return c


def base_barnard(code):
    """Normalise Barnard code to base class (first 2-3 chars)."""
    if not code:
        return ""
    c = code.strip().upper()
    return c[:3] if len(c) >= 3 else c


def get_retention_flag(code):
    """Get retention flag (H1-H3) from Barnard classification."""
    if not code:
        return None
    c = code.strip().upper()
    if c in RETENTION_FLAGS:
        return RETENTION_FLAGS[c]
    for i in range(len(c) - 1, 0, -1):
        p = c[:i]
        if p in RETENTION_FLAGS:
            return RETENTION_FLAGS[p]
    return None


def get_year(rec):
    """Extract publication year from record."""
    raw = gf(rec, "Y1", "PY", "DA")
    m = re.search(r"\d{4}", raw)
    return int(m.group()) if m else None


def get_isbn(rec):
    """Extract ISBN from record (numeric digits only)."""
    return re.sub(r"[^0-9X]", "", gf(rec, "SN"), flags=re.IGNORECASE)


def get_authors(rec):
    """Format authors as semicolon-separated list."""
    all_authors = []
    for tag in ("A1", "A2"):
        v = rec.get(tag, [])
        all_authors += v if isinstance(v, list) else [v]
    if not all_authors:
        return ""
    if len(all_authors) <= 2:
        return "; ".join(all_authors)
    return "; ".join(all_authors[:2]) + " et al."


def make_circ_key(barnard, call_num, year):
    """Create a unique key for circulation tracking (barnard|call_num|year)."""
    b = (barnard or "").strip().upper()
    c = re.sub(r"/.*$", "", (call_num or "").strip())
    c = re.sub(r"M$", "", c, flags=re.IGNORECASE).strip()
    y = (year or "").strip()
    return f"{b}|{c}|{y}"


def get_circ_key(rec):
    """Extract circulation key from record."""
    b = gf(rec, "U4").strip().upper()
    c = re.sub(r"M$", "", gf(rec, "U5").strip(), flags=re.IGNORECASE).strip()
    raw = gf(rec, "Y1", "PY", "DA")
    m = re.search(r"\d{4}", raw)
    y = m.group() if m else ""
    return make_circ_key(b, c, y)


def unicat_url(rec):
    """Generate UniCat search URL for a record."""
    isbn = get_isbn(rec)
    if isbn:
        return f"https://www.unicat.be/uniCat?func=search&query={urllib.parse.quote(isbn)}"
    # Clean title: strip punctuation, take first 4 meaningful words
    raw_title = gf(rec, "T1", "TI")
    clean_title = re.sub(r"[\[\];:,!?(){}]", " ", raw_title)
    clean_title = re.sub(r"\s+", " ", clean_title).strip()
    title = " ".join(clean_title.split()[:4])
    author = " ".join(gf(rec, "A1", "A2").split()[:2])
    q = " ".join(filter(None, [title, author]))
    return f"https://www.unicat.be/uniCat?func=search&query={urllib.parse.quote(q)}"


def is_historical_title(title, author=""):
    """Check if record matches a known landmark work in medical literature.
    
    Title fragment must appear in cleaned title and cover ≥60% of its words.
    If author fragment is set, at least one author token must appear.
    """
    t = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    t = re.sub(r"\s+", " ", t).strip()
    a = re.sub(r"[^a-z ]", " ", author.lower())
    a = re.sub(r"\s+", " ", a).strip()

    for title_frag, author_frag in HISTORICAL_TITLES:
        if title_frag not in t:
            # Also allow: historical fragment starts with first 20 chars of record title
            if not (len(t) >= 20 and title_frag.startswith(t[:20])):
                continue
        # Coverage guard: fragment must cover ≥60% of the record title's words
        ht_words = len(title_frag.split())
        t_words = len(t.split())
        if t_words > 0 and (ht_words / t_words) < 0.6:
            continue
        # Author guard — author_frag may contain space-separated alternatives
        if author_frag is not None:
            alternatives = author_frag.split()
            if not any(alt in a for alt in alternatives):
                continue
        return True
    return False


def matches_outbreak(title, abstract, keywords, barnard):
    """Check if record matches an outbreak timeline event.
    
    Keywords must appear in title + abstract (not keywords field).
    Barnard classification must start with one of the event's prefixes.
    """
    raw_hay = (title + " " + abstract).lower()
    # Strip accents so "fièvre" matches "fievre", "doença" matches "doenca"
    hay = unicodedata.normalize("NFKD", raw_hay).encode("ascii", "ignore").decode("ascii")
    barnard_upper = (barnard or "").upper()
    matched = []
    
    for ev in OUTBREAK_TIMELINE:
        if not any(k in hay for k in ev["keywords"]):
            continue
        prefixes = ev.get("barnard_prefixes", [])
        if prefixes and not any(barnard_upper.startswith(p) for p in prefixes):
            continue
        matched.append(ev["event"])
    
    return matched
