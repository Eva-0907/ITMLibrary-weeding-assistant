"""Core weeding decision rules engine."""

import re
from enum import Enum

from itm_weeding.core.helpers import (
    base_barnard,
    barnard_label,
    get_authors,
    get_circ_key,
    get_isbn,
    get_retention_flag,
    get_year,
    gf,
    is_historical_title,
    matches_outbreak,
)
from itm_weeding.config.rules_data import (
    AFRICA_TERMS,
    CONFERENCE_TERMS,
    CONGO_TERMS,
    DEDICATION_TERMS,
    IRCB_TERMS,
    MANUAL_GUIDE_TERMS,
    SPECIALIST_PUBLISHERS,
    TROPICAL_TERMS,
    WHO_FAO_SHORT,
    WHO_FAO_TERMS,
)


class WeedResult(Enum):
    """Possible weeding outcomes for a single record."""

    KEEP = "KEEP"
    REVIEW = "REVIEW"
    SKIP = "SKIP"
    WEED = "WEED"


class DecisionState:
    """Mutable weeding decision state threaded through each rule."""

    def __init__(self):
        self.flags: list = []
        self.recommendation: WeedResult | None = None
        self.had_keep_reason: bool = False

    def flag(self, criterion: str, detail: str, severity: str) -> None:
        """Append a flag to the decision."""
        self.flags.append({"criterion": criterion, "detail": detail, "severity": severity})


class RulesEngine:
    """Weeding decision rules engine.

    Holds collection-level context.  Call ``get_weed_result(rec, ...)`` for
    each record to obtain a weeding recommendation dict.
    """

    def __init__(self, all_records, borrowed_bibs, isbn_counts, barnard_counts=None):
        self.all_records = all_records
        self.borrowed_bibs = borrowed_bibs
        self.isbn_counts = isbn_counts
        self.barnard_counts = barnard_counts or {}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def get_weed_result(
        self,
        rec,
        unicat_result=None,
        older_edition: bool = False,
        translation_duplicate: bool = False,
    ) -> dict:
        """Apply all weeding rules to *rec* and return a recommendation dict."""
        result = DecisionState()

        # SKIP check — must come first
        result = self._rule_e_only(result, rec)
        if result.recommendation == WeedResult.SKIP:
            return self._build(result, rec)

        # Keep rules — first match wins
        for keep_rule in (
            self._rule_retention_flags,
            self._rule_document_type,
            self._rule_regional,
            self._rule_historical,
            self._rule_circulation,
            self._rule_publisher,
        ):
            result = keep_rule(result, rec)
            if result.recommendation == WeedResult.KEEP:
                break

        # Informational Barnard flag (always)
        result = self._rule_barnard_flag(result, rec)

        # WHO/FAO check — flag now, re-check after weed rules
        is_who_fao = self._is_who_fao(rec)
        if is_who_fao:
            result.flag(
                "WHO/FAO",
                "WHO or FAO publication — likely available open access online — verify before keeping",
                "review",
            )

        # Duplicate / edition / translation rules
        result = self._rule_duplicates(result, rec, translation_duplicate, older_edition)

        # Scarcity protection
        result = self._rule_scarcity(result, rec)

        # Weed rules
        result = self._rule_weed(result, rec)
        result = self._rule_unicat_review(result, unicat_result)

        # WHO/FAO final override: downgrade a kept WHO/FAO item to REVIEW
        if is_who_fao and (result.recommendation == WeedResult.KEEP or result.had_keep_reason) and not translation_duplicate:
            result.recommendation = WeedResult.REVIEW

        return self._build(result, rec)

    # ------------------------------------------------------------------
    # Rules — each takes (DecisionState, rec) and returns DecisionState
    # ------------------------------------------------------------------

    def _rule_e_only(self, result: DecisionState, rec) -> DecisionState:
        """Mark e-only records for SKIP."""
        e_status = gf(rec, "U2")
        doc_type = gf(rec, "U1")
        if "e-only" in e_status.lower() or "-e" in doc_type.lower():
            result.flag("E-only", "No physical copy", "keep")
            result.recommendation = WeedResult.SKIP
        return result

    def _rule_retention_flags(self, result: DecisionState, rec) -> DecisionState:
        """Keep records with H1 retention flag indefinitely."""
        barnard = gf(rec, "U4")
        retention = get_retention_flag(barnard)
        if retention == "H1":
            result.flag(
                "Retention flag",
                f"H1 — Core historical field ({barnard_label(barnard)}) — retain indefinitely",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
        return result

    def _rule_document_type(self, result: DecisionState, rec) -> DecisionState:
        """Apply keep/weed rules based on document type."""
        rec_type = gf(rec, "TY").upper()
        title = gf(rec, "T1", "TI").lower()
        doc_type = gf(rec, "U1").lower()

        result = self._check_dissertation(result, rec_type, title, doc_type)
        if result.recommendation is None:
            result = self._check_proceedings(result, rec, rec_type, title, doc_type)
        if result.recommendation is None:
            result = self._check_dedication(result, rec, title)
        return result

    def _check_dissertation(self, result: DecisionState, rec_type, title, doc_type) -> DecisionState:
        if rec_type in ("THES", "THESIS", "DISS") or "dissertation" in doc_type or "dissertation" in title:
            result.flag("Document type", "Doctoral dissertation — always keep", "keep")
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
        return result

    def _check_proceedings(self, result: DecisionState, rec, rec_type, title, doc_type) -> DecisionState:
        if not (rec_type in ("CONF", "CPAPER") or any(t in title for t in CONFERENCE_TERMS)):
            return result
        has_e_version = "e-also" in gf(rec, "U2").lower() or "-h" in doc_type or bool(gf(rec, "L2"))
        if has_e_version:
            result.flag("Document type", "Conference proceedings — e-version exists", "weed")
            result.recommendation = WeedResult.WEED
        else:
            kw_list = rec.get("KW", [])
            keywords = ", ".join(kw_list if isinstance(kw_list, list) else [kw_list])
            hay = title + " " + gf(rec, "N2").lower() + " " + keywords.lower()
            is_tropical = any(t in hay for t in TROPICAL_TERMS)
            detail = (
                "Conference proceedings on tropical/colonial topic — always keep"
                if is_tropical
                else "Conference proceedings (no e-version) — keep"
            )
            result.flag("Document type", detail, "keep")
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
        return result

    def _check_dedication(self, result: DecisionState, rec, title) -> DecisionState:
        if any(t in title + " " + gf(rec, "N2").lower() for t in DEDICATION_TERMS):
            result.flag(
                "Document type",
                "Liber amicorum / dedication / commemorative edition — always keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
        return result

    def _rule_regional(self, result: DecisionState, rec) -> DecisionState:
        """Apply keep rules based on regional/institutional relevance."""
        title = gf(rec, "T1", "TI")
        abstract = gf(rec, "N2")
        publisher = gf(rec, "PB").lower()
        kw_list = rec.get("KW", [])
        keywords = ", ".join(kw_list if isinstance(kw_list, list) else [kw_list])
        note = gf(rec, "N1")

        hay = (title + " " + abstract + " " + publisher + " " + keywords).lower()

        # Congo / Belgium
        if any(t in hay for t in CONGO_TERMS):
            result.flag("Regional relevance", "Congo / Belgium — always keep", "keep")
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
            return result

        # Africa-specific
        is_atlas = "atlas" in title.lower() or "atlas" in (gf(rec, "U5") or "").lower()
        hay_africa = (title + " " + abstract + " " + keywords + " " + gf(rec, "CY")).lower()
        is_africa_specific = any(t in hay_africa for t in AFRICA_TERMS)

        if is_atlas and is_africa_specific:
            result.flag(
                "Regional relevance",
                "African atlas — geographically scarce, always keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
        elif is_africa_specific and not any(
            t in hay_africa for t in ["manual", "guide", "handbook", "directory"]
        ):
            result.flag(
                "Regional relevance",
                "Africa-specific study — historical/regional value, keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
            return result

        # IRCB / ARSC
        hay2 = (title + " " + abstract + " " + publisher + " " + keywords + " " + note).lower()
        if any(t in hay2 for t in IRCB_TERMS):
            result.flag("IRCB/ARSC", "IRCB or ARSC publication — always keep", "keep")
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True

        return result

    def _rule_historical(self, result: DecisionState, rec) -> DecisionState:
        """Keep historically significant titles and outbreak-relevant works."""
        title = gf(rec, "T1", "TI")
        barnard = gf(rec, "U4")
        kw_list = rec.get("KW", [])
        keywords = ", ".join(kw_list if isinstance(kw_list, list) else [kw_list])
        abstract = gf(rec, "N2")
        author_str = get_authors(rec)

        if is_historical_title(title, author_str):
            result.flag(
                "Historical title",
                "Listed in Top Historical Titles for Tropical Medicine",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
            return result

        outbreaks = matches_outbreak(title, abstract, keywords, barnard)
        if outbreaks:
            result.flag("Outbreak relevance", "Relates to: " + "; ".join(outbreaks[:3]), "keep")
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True

        return result

    def _rule_circulation(self, result: DecisionState, rec) -> DecisionState:
        """Keep records that have active circulation or special location."""
        if self.borrowed_bibs and get_circ_key(rec) in self.borrowed_bibs:
            result.flag(
                "Circulation",
                "Borrowed at least once (2019–2026) — keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True
            return result

        u2 = gf(rec, "U2").lower()
        if "archives-g" in u2:
            result.flag(
                "Archives-G",
                "Stored in Archives-G — curated special collection, always keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True

        return result

    def _rule_publisher(self, result: DecisionState, rec) -> DecisionState:
        """Keep items from specialist tropical medicine publishers."""
        pub_lower = gf(rec, "PB").lower()
        a3_vals = rec.get("A3", [])
        a3_vals = [a3_vals] if isinstance(a3_vals, str) else a3_vals
        hay_pub = pub_lower + " " + " ".join(a3_vals).lower()

        if any(sp in hay_pub for sp in SPECIALIST_PUBLISHERS):
            result.flag(
                "Specialist publisher",
                "Published by specialist tropical medicine institution — keep",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True

        return result

    def _rule_barnard_flag(self, result: DecisionState, rec) -> DecisionState:
        """Add an informational Barnard classification flag."""
        barnard = gf(rec, "U4")
        retention = get_retention_flag(barnard)
        if barnard:
            result.flag(
                "Barnard",
                barnard_label(barnard) + (f" [{retention}]" if retention else ""),
                "keep",
            )
        return result

    def _rule_duplicates(
        self,
        result: DecisionState,
        rec,
        is_translation_duplicate: bool,
        is_older_edition: bool,
    ) -> DecisionState:
        """Apply weed rules for translation duplicates and older editions."""
        if is_translation_duplicate:
            result.flag(
                "Translation",
                "Non-English version — English edition exists in collection — weed "
                "(English copy is retained as the preferred edition)",
                "weed",
            )
            result.recommendation = WeedResult.WEED
            return result

        if is_older_edition and result.recommendation != WeedResult.KEEP:
            result.flag(
                "Edition",
                "Older edition — newer edition exists in collection — weed",
                "weed",
            )
            result.recommendation = WeedResult.WEED

        return result

    def _rule_scarcity(self, result: DecisionState, rec) -> DecisionState:
        """Protect records in Barnard classes with very few items."""
        if result.recommendation == WeedResult.KEEP or not self.barnard_counts:
            return result

        barnard = gf(rec, "U4")
        title = gf(rec, "T1", "TI")
        bc = base_barnard(barnard) if barnard else ""
        class_count = self.barnard_counts.get(bc, 0) if bc else 0
        is_manual_guide = any(t in title.lower() for t in MANUAL_GUIDE_TERMS)

        if class_count <= 2 and not is_manual_guide:
            result.flag(
                "Class scarcity",
                f"Only {class_count} item(s) in Barnard class {bc} — keep to avoid collection gap",
                "keep",
            )
            result.recommendation = WeedResult.KEEP
            result.had_keep_reason = True

        return result

    def _rule_weed(self, result: DecisionState, rec) -> DecisionState:
        """Apply primary weeding rules (publication date, ISBN duplicates)."""
        if result.recommendation == WeedResult.KEEP:
            return result

        isbn = get_isbn(rec)
        if isbn and self.isbn_counts.get(isbn, 0) > 1:
            result.flag("Duplicate", f"{self.isbn_counts[isbn]} copies — this is a duplicate", "weed")
            result.recommendation = WeedResult.WEED
            return result

        year = get_year(rec)
        retention = get_retention_flag(gf(rec, "U4"))

        if year is not None:
            if 1950 <= year <= 1990:
                suffix = f" [{retention} class] — auto-weed" if retention in ("H2", "H3") else " (1950–1990)"
                extra = " (no special flags)" if retention == "H2" else ""
                result.flag("Publication date", f"Published {year}{suffix}{extra}", "weed")
                result.recommendation = WeedResult.WEED
            elif year < 1950:
                result.flag(
                    "Publication date",
                    f"Published {year} (pre-1950) — potential historical value",
                    "keep",
                )
                result.recommendation = WeedResult.KEEP
                result.had_keep_reason = True
            else:  # > 1990
                result.flag(
                    "Publication date",
                    f"Published {year} (post-1990, not circulated) — auto-weed",
                    "weed",
                )
                result.recommendation = WeedResult.WEED
        else:
            result.flag(
                "Publication date",
                "No publication year — flagged for manual review",
                "review",
            )
            result.recommendation = WeedResult.REVIEW

        return result

    def _rule_unicat_review(self, result: DecisionState, unicat_result) -> DecisionState:
        """Downgrade WEED to REVIEW when the item is not held in Belgian libraries."""
        if unicat_result == "not_held" and result.recommendation == WeedResult.WEED:
            result.flag(
                "UniCat availability",
                "UniCat shows this ISBN is not held in Belgian libraries — review before weeding",
                "review",
            )
            result.recommendation = WeedResult.REVIEW
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_who_fao(self, rec) -> bool:
        """Return True if the record is a WHO or FAO publication."""
        parts = [gf(rec, "PB").lower()]
        for tag in ("A1", "A2", "A3", "A4", "ED", "SE", "PB", "T3"):
            v = rec.get(tag, "")
            if isinstance(v, list):
                parts.extend(v)
            elif v:
                parts.append(v)
        hay = " ".join(filter(None, parts)).lower()
        return any(t in hay for t in WHO_FAO_TERMS) or any(
            re.search(r"\b" + t + r"\b", hay) for t in WHO_FAO_SHORT
        )

    def _build(self, result: DecisionState, rec) -> dict:
        """Assemble the final recommendation dict from a DecisionState."""
        retention = get_retention_flag(gf(rec, "U4"))
        recommendation = result.recommendation or WeedResult.REVIEW
        hist_criteria = {"Historical title", "Outbreak relevance", "Regional relevance", "IRCB/ARSC", "Retention flag"}
        historically = (recommendation == WeedResult.KEEP) and any(
            f["criterion"] in hist_criteria for f in result.flags
        )
        return {
            "recommendation": recommendation.value,
            "keep_override": recommendation == WeedResult.KEEP,
            "hard_rule": recommendation.value,
            "flags": result.flags,
            "retention": retention,
            "historically_significant": historically,
            "historical_reasons": [f["detail"] for f in result.flags if f["severity"] == "keep"],
            "reasoning": ". ".join(f["detail"] for f in result.flags),
        }
