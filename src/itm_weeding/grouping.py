"""Pre-computed grouping indices for edition, volume and translation detection."""

from collections import defaultdict

from itm_weeding.core import get_year, get_isbn, base_barnard, gf
from itm_weeding.text_utils import TextUtils


class GroupIndexer:
    """Pre-computes duplicate/edition/volume/translation indices over records."""

    ENGLISH_VARIANTS = {"english", "eng", "en", "anglais", "engels"}

    def __init__(self, records):
        self.records = records
        self.isbn_counts = self._compute_isbn_counts()
        self.barnard_counts = self._compute_barnard_counts()
        self.older_edition_indices = self._compute_older_edition_indices()
        self.volume_set_indices = self._compute_volume_set_indices()
        self.translation_weed_indices = self._compute_translation_weed_indices()

    def _compute_isbn_counts(self):
        """Count occurrences of each ISBN for duplicate detection."""
        isbn_counts = {}
        for rec in self.records:
            isbn = get_isbn(rec)
            if isbn:
                isbn_counts[isbn] = isbn_counts.get(isbn, 0) + 1
        return isbn_counts

    def _compute_barnard_counts(self):
        """Count records per Barnard class for scarcity protection."""
        barnard_counts = {}
        for rec in self.records:
            bc = base_barnard(gf(rec, "U4"))
            if bc:
                barnard_counts[bc] = barnard_counts.get(bc, 0) + 1
        return barnard_counts

    def _compute_older_edition_indices(self):
        """Identify record indices that are superseded by a newer edition."""
        edition_groups = defaultdict(list)
        for i, rec in enumerate(self.records):
            title = gf(rec, "T1", "TI")
            if not title:
                continue
            key = TextUtils.normalise_title(title)
            if key:
                edition_groups[key].append(i)

        older_edition_indices = set()
        for indices in edition_groups.values():
            if len(indices) < 2:
                continue

            def sort_key(i):
                ed = TextUtils.get_edition_num(self.records[i])
                yr = get_year(self.records[i]) or 0
                return (ed if ed > 1 else 0, yr)

            sorted_indices = sorted(indices, key=sort_key, reverse=True)
            for older in sorted_indices[1:]:
                older_edition_indices.add(older)
        return older_edition_indices

    def _compute_volume_set_indices(self):
        """Map record indices to their multi-volume set key."""
        volume_groups = defaultdict(list)
        for i, rec in enumerate(self.records):
            title = gf(rec, "T1", "TI")
            if not title:
                continue
            key = TextUtils.normalise_volume_title(title)
            base = TextUtils.normalise_title(title)
            if key and key != base:
                volume_groups[key].append(i)

        volume_set_indices = {}
        for key, indices in volume_groups.items():
            if len(indices) > 1:
                for i in indices:
                    volume_set_indices[i] = key
        return volume_set_indices

    def _compute_translation_weed_indices(self):
        """Identify non-English translation duplicates that can be weeded."""
        translation_groups = defaultdict(list)
        for i, rec in enumerate(self.records):
            author = TextUtils.normalise_author(rec)
            year = str(get_year(rec) or "")
            barnard = gf(rec, "U4").strip().upper()[:3]
            lang = gf(rec, "U3").strip().lower()
            if author and year and barnard:
                key = f"{author}|{year}|{barnard}"
                translation_groups[key].append((i, lang))

        translation_weed_indices = set()
        for items in translation_groups.values():
            if len(items) < 2:
                continue
            langs = [lang for _, lang in items]
            has_english = any(lang in self.ENGLISH_VARIANTS for lang in langs)
            has_multiple_langs = len(set(langs)) > 1
            if has_english and has_multiple_langs:
                for i, lang in items:
                    if lang not in self.ENGLISH_VARIANTS:
                        translation_weed_indices.add(i)
        return translation_weed_indices
