# PDFBooklet/src/data/models.py
"""
Plain data models shared across the app.

These are pure value objects — no Qt, no PDF libraries, no behavior beyond simple
derived properties. Behavior that operates on these models lives in the logic tier
(e.g. PageTransformManager in src/logic/page_transforms.py).
"""

from dataclasses import dataclass


@dataclass
class Transform:
    """
    Represents a set of transformations to apply to a page.
    All measurements in millimeters, scales in percentages, rotation in degrees.
    """

    h_shift_mm: float = 0.0  # Horizontal shift in mm
    v_shift_mm: float = 0.0  # Vertical shift in mm
    scale_percent: float = 100.0  # Uniform scale percentage
    rotation_deg: float = 0.0  # Rotation in degrees (0-360)
    h_flip: bool = False  # Horizontal mirror
    v_flip: bool = False  # Vertical mirror
    h_scale_percent: float = 100.0  # Horizontal-only scale percentage
    v_scale_percent: float = 100.0  # Vertical-only scale percentage

    def is_identity(self) -> bool:
        """Check if this transform does nothing (all default values)."""
        return (
            self.h_shift_mm == 0.0
            and self.v_shift_mm == 0.0
            and self.scale_percent == 100.0
            and self.rotation_deg == 0.0
            and not self.h_flip
            and not self.v_flip
            and self.h_scale_percent == 100.0
            and self.v_scale_percent == 100.0
        )
