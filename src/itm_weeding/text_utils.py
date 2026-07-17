"""Text normalisation and small formatting helpers."""

import re
from pathlib import Path

from itm_weeding.core import gf


class TextUtils:
    """Stateless helpers for title/author normalisation and formatting."""

    @staticmethod
    def normalise_title(title, max_length=60):
        """Normalise title for edition grouping by removing edition markers."""
        t = title.lower()
        # Remove edition markers
        t = re.sub(
            r"[;,]\s*(\d+(st|nd|rd|th)?\.?\s*(ed|edition|éd|uitgave|druk|aufl).*)",
            "",
            t,
        )
        t = re.sub(
            r"\s*(\d+(st|nd|rd|th)?\.?\s*(ed|edition|éd|uitgave|druk|aufl).*)", "", t
        )
        t = re.sub(r"[^a-z0-9 ]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t[:max_length]

    @staticmethod
    def get_edition_num(rec):
        """Extract edition number from record title."""
        title = gf(rec, "T1", "TI")
        m = re.search(
            r"(\d+)(st|nd|rd|th)?\s*(ed|edition|éd|uitgave|druk|aufl)", title, re.I
        )
        if m:
            return int(m.group(1))
        return 1

    @staticmethod
    def normalise_volume_title(title, max_length=60):
        """Normalise title for volume grouping by removing volume markers."""
        t = title.lower()
        t = re.sub(
            r"[.,;]?\s*(volume|vol|deel|band|tome|part|partie|bd|fasc)\s*\.?\s*([ivxlcdm\d]+).*",
            "",
            t,
            flags=re.I,
        )
        t = re.sub(r"[^a-z0-9 ]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t[:max_length]

    @staticmethod
    def normalise_author(rec):
        """Normalise author for translation grouping."""
        a = gf(rec, "A1", "A2").lower()
        a = re.sub(r"[^a-z ]", "", a).strip()
        return " ".join(a.split()[:2])

    @staticmethod
    def read_ris_file(path):
        """Read RIS file with auto-detected encoding."""
        for enc in ("utf-8-sig", "utf-8", "cp850", "windows-1252"):
            try:
                text = Path(path).read_text(encoding=enc)
                if "�" not in text:
                    print(f"  Encoding detected: {enc}")
                    return text
            except (UnicodeDecodeError, LookupError):
                continue
        text = Path(path).read_text(encoding="cp850", errors="replace")
        print("  Encoding detected: cp850 (fallback)")
        return text

    @staticmethod
    def render_progress_bar(current, total, width=20):
        """Render a simple text progress bar."""
        if total <= 0:
            return f"[{'' * width}] 0/{total} (0%)"

        filled = int(round(current / total * width))
        filled = max(0, min(width, filled))
        bar = "#" * filled + "-" * (width - filled)
        percent = int(round(current / total * 100))
        return f"[{bar}] {current}/{total} ({percent}%)"
