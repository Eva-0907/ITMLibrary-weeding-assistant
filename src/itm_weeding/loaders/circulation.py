"""Circulation (loan) data loading."""

from itm_weeding.core import load_circulation


class CirculationData:
    """Loan records loaded from student and staff circulation files."""

    def __init__(self, borrowed: set):
        self.borrowed = borrowed


class CirculationDataLoader:
    """Loads circulation (loan) data from CSV files."""

    @staticmethod
    def load(students_path, staff_path) -> CirculationData:
        """Load student and staff loan files into a CirculationData object."""
        borrowed = set()
        if students_path:
            print(f"Loading student loans: {students_path}")
            s = load_circulation(students_path, delimiter=";")
            borrowed |= s
            print(f"  {len(s):,} student loan records")
        if staff_path:
            print(f"Loading staff loans: {staff_path}")
            s = load_circulation(staff_path, delimiter="\t")
            borrowed |= s
            print(f"  {len(s):,} staff loan records")
        if borrowed:
            print(f"  {len(borrowed):,} unique circulated items total")
        return CirculationData(borrowed)
