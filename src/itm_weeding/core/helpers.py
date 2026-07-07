"""Helper functions for record processing and classification."""

import re
import urllib.parse
import unicodedata

from itm_weeding.config.barnard import BARNARD, RETENTION_FLAGS
from itm_weeding.config.rules_data import HISTORICAL_TITLES, OUTBREAK_TIMELINE


def gf(rec, *tags):
    """Return the first non-empty field value for the given RIS tags.

    The function checks the supplied tags in order and returns the first value
    that exists in the record. This is used throughout the project to read
    fields such as title, author, year, and location without repeatedly
    handling list-vs-string record values.
    """
    for t in tags:
        v = rec.get(t)
        if v:
            return v[0] if isinstance(v, list) else v
    return ""


def barnard_label(code):
    """Format a Barnard code into a readable label.

    If the full code is known, the function returns it with the matching
    descriptive label. If the code is only partially known, it falls back to
    the longest prefix that is available in the configuration dataset.
    """
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
    """Return the base Barnard class for grouping and scarcity analysis.

    The function strips whitespace, normalizes the code to uppercase, and
    keeps the first three characters so related records can be grouped by a
    shared classification prefix.
    """
    if not code:
        return ""
    c = code.strip().upper()
    return c[:3] if len(c) >= 3 else c


def get_retention_flag(code):
    """Resolve the retention flag associated with a Barnard classification.

    The function looks up the Barnard code or its known prefix in the retention
    mapping and returns the corresponding H1/H2/H3 flag when available.
    """
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
    """Extract the publication year from a RIS record.

    The function scans the common year fields in order and returns the first
    four-digit year it finds. If no year is present, it returns None.
    """
    raw = gf(rec, "Y1", "PY", "DA")
    m = re.search(r"\d{4}", raw)
    return int(m.group()) if m else None


def get_isbn(rec):
    """Extract a normalized ISBN value from a RIS record.

    Only numeric digits and the letter X are preserved so that ISBNs can be
    compared consistently across records.
    """
    return re.sub(r"[^0-9X]", "", gf(rec, "SN"), flags=re.IGNORECASE)


def get_authors(rec):
    """Format authors for display in the report.

    The function collects author values from the A1 and A2 tags and returns a
    short, human-readable string. If there are more than two authors, it trims
    the list to the first two and appends "et al.".
    """
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
    """Build a normalized circulation identifier for a bibliographic item.

    The key combines Barnard class, call number, and year so that circulation
    records can be matched against bibliographic records reliably.
    """
    b = (barnard or "").strip().upper()
    c = re.sub(r"/.*$", "", (call_num or "").strip())
    c = re.sub(r"M$", "", c, flags=re.IGNORECASE).strip()
    y = (year or "").strip()
    return f"{b}|{c}|{y}"


def get_circ_key(rec):
    """Create the circulation lookup key for a single RIS record.

    The function derives the Barnard class, normalized call number, and year
    from the record and uses them to build the same key structure used in the
    circulation data import.
    """
    b = gf(rec, "U4").strip().upper()
    c = re.sub(r"M$", "", gf(rec, "U5").strip(), flags=re.IGNORECASE).strip()
    raw = gf(rec, "Y1", "PY", "DA")
    m = re.search(r"\d{4}", raw)
    y = m.group() if m else ""
    return make_circ_key(b, c, y)


def unicat_url(rec):
    """Generate a UniCat search URL for a bibliographic record.

    If an ISBN is available, the URL searches by ISBN; otherwise the function
    falls back to a short title/author search string.
    """
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
    """Return True when a title appears to be a historically significant landmark work.

    The function compares the cleaned title and author against a curated list of
    historical titles and uses coverage heuristics to prevent weak matches.
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
    """Find outbreak-related events that match a record's content.

    The function searches the title and abstract for outbreak keywords and checks
    that the Barnard class falls within the expected prefix range for that
    event. Matching event names are returned as a list.
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
