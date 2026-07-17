"""Command-line interface for the weeding assistant."""

import argparse


class CLI:
    """Builds and parses command-line arguments."""

    @staticmethod
    def build_parser():
        """Build the command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="ITM Library Weeding Agent — Tropical Medicine Collection"
        )
        parser.add_argument(
            "ris",
            help="Path to .ris file(s) — space-separated for multiple files",
            nargs="+",
        )
        parser.add_argument(
            "--students", help="Student loans CSV (semicolon-delimited)"
        )
        parser.add_argument("--staff", help="Staff loans CSV/TSV (tab-delimited)")
        parser.add_argument(
            "--out",
            default="data/output/weeding_report.xlsx",
            help="Output XLSX filename",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Disable UniCat cache (force re-lookup all ISBNs)",
        )
        parser.add_argument(
            "--concurrent",
            action="store_true",
            help="Use concurrent SPARP batch lookups for UniCat (faster)",
        )
        return parser

    @classmethod
    def parse_args(cls, argv=None):
        """Parse command-line arguments."""
        return cls.build_parser().parse_args(argv)
