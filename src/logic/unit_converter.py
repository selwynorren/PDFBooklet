# PDFBooklet/src/logic/unit_converter.py
def mm_to_inches(mm_value: float) -> float:
    """Converts a value from millimeters to inches."""
    return mm_value / 25.4


def inches_to_mm(inches_value: float) -> float:
    """Converts a value from inches to millimeters."""
    return inches_value * 25.4
