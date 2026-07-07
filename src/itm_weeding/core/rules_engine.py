"""Core weeding decision rules engine."""

import re

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


class RulesEngine:
    """Apply the library weeding decision rules to a single bibliographic record."""
    
    def __init__(self, rec, all_records, borrowed_bibs, isbn_counts, barnard_counts=None):
        """Initialize the rules engine with the current record and shared context.

        The context data lets the engine evaluate a record relative to the rest
        of the collection, including circulation history and duplicate counts.
        """
        self.rec = rec
        self.all_records = all_records
        self.borrowed_bibs = borrowed_bibs
        self.isbn_counts = isbn_counts
        self.barnard_counts = barnard_counts or {}
        
        # Extract record fields
        self.year = get_year(rec)
        self.isbn = get_isbn(rec)
        self.rec_type = gf(rec, "TY").upper()
        self.title = gf(rec, "T1", "TI")
        self.abstract = gf(rec, "N2")
        kw_list = rec.get("KW", [])
        self.keywords = ", ".join(kw_list if isinstance(kw_list, list) else [kw_list])
        self.publisher = gf(rec, "PB").lower()
        self.note = gf(rec, "N1")
        self.doc_type = gf(rec, "U1")
        self.e_status = gf(rec, "U2")
        self.barnard = gf(rec, "U4")
        self.retention = get_retention_flag(self.barnard)
        self.has_e_version = (
            "e-also" in self.e_status.lower()
            or "-h" in self.doc_type.lower()
            or bool(gf(rec, "L2"))
        )
        
        # Decision state
        self.flags = []
        self.keep_override = False
        self.hard_rule = None
        self.had_keep_reason = False
    
    def _flag(self, criterion, detail, severity):
        """Record an explanation or evidence item for the final decision."""
        self.flags.append({"criterion": criterion, "detail": detail, "severity": severity})
    
    def _check_e_only(self):
        """Return True when the record is an e-only item and should be skipped."""
        if "e-only" in self.e_status.lower() or "-e" in self.doc_type.lower():
            self._flag("E-only", "No physical copy", "keep")
            return True
        return False
    
    def _apply_retention_flags(self):
        """Apply any retention-flag based keep rules to the current record."""
        if self.retention == "H1":
            self._flag(
                "Retention flag",
                f"H1 — Core historical field ({barnard_label(self.barnard)}) — retain indefinitely",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_document_type_rules(self):
        """Apply rules that depend on the document type, such as dissertations or proceedings."""
        # Dissertation
        if (
            self.rec_type in ("THES", "THESIS", "DISS")
            or "dissertation" in self.doc_type.lower()
            or "dissertation" in self.title.lower()
        ):
            self._flag("Document type", "Doctoral dissertation — always keep", "keep")
            self.keep_override = True
            self.had_keep_reason = True
            return
        
        # Proceedings
        is_proceedings = (
            self.rec_type in ("CONF", "CPAPER")
            or any(t in self.title.lower() for t in CONFERENCE_TERMS)
        )
        if is_proceedings:
            hay_conf = (self.title + " " + self.abstract + " " + self.keywords).lower()
            is_tropical_conf = any(t in hay_conf for t in TROPICAL_TERMS)
            if not self.has_e_version:
                if is_tropical_conf:
                    self._flag(
                        "Document type",
                        "Conference proceedings on tropical/colonial topic — always keep",
                        "keep",
                    )
                    self.keep_override = True
                    self.had_keep_reason = True
                else:
                    self._flag(
                        "Document type",
                        "Conference proceedings (no e-version) — keep",
                        "keep",
                    )
                    self.keep_override = True
                    self.had_keep_reason = True
            else:
                self._flag("Document type", "Conference proceedings — e-version exists", "weed")
                self.hard_rule = "WEED"
            return
        
        # Liber amicorum
        hay_ded = (self.title + " " + self.abstract).lower()
        if any(t in hay_ded for t in DEDICATION_TERMS):
            self._flag(
                "Document type",
                "Liber amicorum / dedication / commemorative edition — always keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_regional_rules(self):
        """Apply rules related to Congo, Africa, and institutional relevance."""
        # Congo / Belgium
        hay = (self.title + " " + self.abstract + " " + self.publisher + " " + self.keywords).lower()
        if any(t in hay for t in CONGO_TERMS):
            self._flag("Regional relevance", "Congo / Belgium — always keep", "keep")
            self.keep_override = True
            self.had_keep_reason = True
            return
        
        # Africa-specific
        is_atlas = "atlas" in self.title.lower() or "atlas" in (gf(self.rec, "U5") or "").lower()
        hay_africa = (
            self.title + " " + self.abstract + " " + self.keywords + " " + gf(self.rec, "CY")
        ).lower()
        is_africa_specific = any(t in hay_africa for t in AFRICA_TERMS)
        
        if is_atlas and is_africa_specific:
            self._flag(
                "Regional relevance",
                "African atlas — geographically scarce, always keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
        elif is_africa_specific and not any(
            t in hay_africa for t in ["manual", "guide", "handbook", "directory"]
        ):
            self._flag(
                "Regional relevance",
                "Africa-specific study — historical/regional value, keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
            return
        
        # IRCB / ARSC
        hay2 = (self.title + " " + self.abstract + " " + self.publisher + " " + self.keywords + " " + self.note).lower()
        if any(t in hay2 for t in IRCB_TERMS):
            self._flag("IRCB/ARSC", "IRCB or ARSC publication — always keep", "keep")
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_historical_rules(self):
        """Apply historical and outbreak-related keep rules to the record."""
        # Historical title list
        author_str = get_authors(self.rec)
        if is_historical_title(self.title, author_str):
            self._flag(
                "Historical title",
                "Listed in Top Historical Titles for Tropical Medicine",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
            return
        
        # Outbreak relevance
        outbreaks = matches_outbreak(self.title, self.abstract, self.keywords, self.barnard)
        if outbreaks:
            self._flag("Outbreak relevance", "Relates to: " + "; ".join(outbreaks[:3]), "keep")
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_circulation_rules(self):
        """Apply rules based on circulation history and special storage locations."""
        # Circulation history
        if self.borrowed_bibs and get_circ_key(self.rec) in self.borrowed_bibs:
            self._flag(
                "Circulation",
                "Borrowed at least once (2019–2026) — keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
            return
        
        # Archives-G location
        u2 = gf(self.rec, "U2").lower()
        if "archives-g" in u2:
            self._flag(
                "Archives-G",
                "Stored in Archives-G — curated special collection, always keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_publisher_rules(self):
        """Apply keep rules for specialist publishers and institutional affiliations."""
        pub_lower = gf(self.rec, "PB").lower()
        a3_vals = self.rec.get("A3", [])
        a3_vals = [a3_vals] if isinstance(a3_vals, str) else a3_vals
        a3_lower = " ".join(a3_vals).lower()
        hay_pub = pub_lower + " " + a3_lower
        
        if not self.keep_override and any(sp in hay_pub for sp in SPECIALIST_PUBLISHERS):
            self._flag(
                "Specialist publisher",
                "Published by specialist tropical medicine institution — keep",
                "keep",
            )
            self.keep_override = True
            self.had_keep_reason = True
    
    def _apply_barnard_flag(self):
        """Add an informational Barnard-class flag to the decision output."""
        if self.barnard:
            self._flag(
                "Barnard",
                barnard_label(self.barnard) + (f" [{self.retention}]" if self.retention else ""),
                "keep",
            )
    
    def _check_who_fao(self):
        """Return True when the record appears to be a WHO or FAO publication."""
        _pub_parts = [self.publisher]
        for tag in ("A1", "A2", "A3", "A4", "ED", "SE", "PB", "T3"):
            v = self.rec.get(tag, "")
            if isinstance(v, list):
                _pub_parts.extend(v)
            elif v:
                _pub_parts.append(v)
        hay_pub = " ".join(filter(None, _pub_parts)).lower()
        is_who_fao = any(t in hay_pub for t in WHO_FAO_TERMS) or any(
            re.search(r"\b" + t + r"\b", hay_pub) for t in WHO_FAO_SHORT
        )
        if is_who_fao:
            self._flag(
                "WHO/FAO",
                "WHO or FAO publication — likely available open access online — verify before keeping",
                "review",
            )
        return is_who_fao
    
    def _apply_duplicate_rules(self, is_translation_duplicate, is_older_edition):
        """Apply duplicate, translation, and older-edition weed rules."""
        # Translation duplicate
        if is_translation_duplicate:
            self.keep_override = False
            self._flag(
                "Translation",
                "Non-English version — English edition exists in collection — weed "
                "(English copy is retained as the preferred edition)",
                "weed",
            )
            self.hard_rule = "WEED"
            return
        
        # Older edition
        if is_older_edition and not self.keep_override:
            self._flag(
                "Edition",
                "Older edition — newer edition exists in collection — weed",
                "weed",
            )
            self.hard_rule = "WEED"
    
    def _apply_scarcity_protection(self):
        """Protect scarce Barnard classes from being weeded automatically."""
        if not self.keep_override and self.barnard_counts:
            bc = base_barnard(self.barnard) if self.barnard else ""
            class_count = self.barnard_counts.get(bc, 0) if bc else 0
            is_manual_guide = any(t in self.title.lower() for t in MANUAL_GUIDE_TERMS)
            if class_count <= 2 and not is_manual_guide:
                self._flag(
                    "Class scarcity",
                    f"Only {class_count} item(s) in Barnard class {bc} — keep to avoid collection gap",
                    "keep",
                )
                self.keep_override = True
                self.had_keep_reason = True
    
    def _apply_weed_rules(self):
        """Apply the default weed rules when the record has not already been kept."""
        if self.keep_override:
            return
        
        # ISBN duplicate
        if self.isbn and self.isbn_counts.get(self.isbn, 0) > 1:
            self._flag("Duplicate", f"{self.isbn_counts[self.isbn]} copies — this is a duplicate", "weed")
            self.hard_rule = "WEED"
            return
        
        # Publication date rules
        if self.year is not None:
            if 1950 <= self.year <= 1990:
                if self.retention == "H3":
                    self._flag(
                        "Publication date",
                        f"Published {self.year} [H3 class] — auto-weed",
                        "weed",
                    )
                    self.hard_rule = "WEED"
                elif self.retention == "H2":
                    self._flag(
                        "Publication date",
                        f"Published {self.year} [H2 class] — auto-weed (no special flags)",
                        "weed",
                    )
                    self.hard_rule = "WEED"
                else:
                    self._flag(
                        "Publication date",
                        f"Published {self.year} (1950–1990)",
                        "weed",
                    )
                    self.hard_rule = "WEED"
            elif self.year < 1950:
                self._flag(
                    "Publication date",
                    f"Published {self.year} (pre-1950) — potential historical value",
                    "keep",
                )
                self.keep_override = True
                self.had_keep_reason = True
            elif self.year > 1990:
                self._flag(
                    "Publication date",
                    f"Published {self.year} (post-1990, not circulated) — auto-weed",
                    "weed",
                )
                self.hard_rule = "WEED"
        else:
            self._flag(
                "Publication date",
                "No publication year — flagged for manual review",
                "review",
            )
            self.hard_rule = "REVIEW"
    
    def apply(self, older_edition=False, translation_duplicate=False):
        """Evaluate the record and return a weeding recommendation.

        The method runs the full pipeline of keep, review, and weed checks and
        returns a structured decision including the final recommendation,
        triggered flags, and human-readable reasoning.
        """
        # Check skip conditions first
        if self._check_e_only():
            return {
                "recommendation": "SKIP",
                "keep_override": False,
                "hard_rule": "SKIP",
                "flags": self.flags,
                "retention": self.retention,
                "historically_significant": False,
                "historical_reasons": [],
                "reasoning": "Skipped — e-only.",
            }
        
        # Apply keep rules in order of priority
        self._apply_retention_flags()
        if not self.keep_override:
            self._apply_document_type_rules()
        if not self.keep_override:
            self._apply_regional_rules()
        if not self.keep_override:
            self._apply_historical_rules()
        if not self.keep_override:
            self._apply_circulation_rules()
        if not self.keep_override:
            self._apply_publisher_rules()
        
        # Add informational flag
        self._apply_barnard_flag()
        
        # Check WHO/FAO
        is_who_fao = self._check_who_fao()
        
        # Apply duplicate/edition/translation rules
        self._apply_duplicate_rules(translation_duplicate, older_edition)
        
        # Apply scarcity protection
        self._apply_scarcity_protection()
        
        # Apply weed rules
        self._apply_weed_rules()
        
        # WHO/FAO final check
        if is_who_fao and (self.keep_override or self.had_keep_reason) and not translation_duplicate:
            self.keep_override = False
            self.hard_rule = "REVIEW"
        
        # Build recommendation
        recommendation = "KEEP" if self.keep_override else (self.hard_rule or "REVIEW")
        hist_criteria = {"Historical title", "Outbreak relevance", "Regional relevance", "IRCB/ARSC", "Retention flag"}
        historically = (self.keep_override or recommendation == "KEEP") and any(
            f["criterion"] in hist_criteria for f in self.flags
        )
        hist_reasons = [f["detail"] for f in self.flags if f["severity"] == "keep"]
        reasoning = ". ".join(f["detail"] for f in self.flags)
        
        return {
            "recommendation": recommendation,
            "keep_override": self.keep_override,
            "hard_rule": self.hard_rule,
            "flags": self.flags,
            "retention": self.retention,
            "historically_significant": historically,
            "historical_reasons": hist_reasons,
            "reasoning": reasoning,
        }


def apply_rules(rec, all_records, borrowed_bibs, isbn_counts, older_edition=False,
                translation_duplicate=False, barnard_counts=None):
    """Convenience wrapper that evaluates a single record with the rules engine.

    The function creates the engine, applies the full rules pipeline, and
    returns the structured recommendation for the caller.
    """
    engine = RulesEngine(rec, all_records, borrowed_bibs, isbn_counts, barnard_counts)
    return engine.apply(older_edition=older_edition, translation_duplicate=translation_duplicate)
