# PDFBooklet/src/logic/page_transforms.py
"""
Page transformation system for PDF manipulation.
Handles global and per-page transformations with domain rules.
"""

from typing import Dict, Optional, Set

# Transform is a pure data model and now lives in the data tier. Re-exported here
# so existing `from .page_transforms import Transform` imports keep working.
from ..data.models import Transform

__all__ = ["Transform", "PageTransformManager", "create_transform_from_gui"]


class PageTransformManager:
    """
    Manages transformations for all pages in a document.
    Handles global transforms and per-page overrides with domain rules.
    """

    def __init__(self, total_pages: int):
        """
        Initialize the transform manager.

        Args:
            total_pages: Total number of pages in the original PDF
        """
        self.total_pages = total_pages
        self.global_transform = Transform()

        # Per-page transforms: key is page index (0-based)
        self.page_transforms: Dict[int, Transform] = {}

        # Domain transforms: special rules for even/odd pages
        self.even_pages_transform: Optional[Transform] = None
        self.odd_pages_transform: Optional[Transform] = None

        # Track which pages have explicit overrides
        self.explicit_overrides: Set[int] = set()

    def set_global_transform(self, transform: Transform):
        """Set the global transformation applied to all pages by default."""
        self.global_transform = transform

    def set_page_transform(
        self, page_index: int, transform: Transform, domain: str = "this"
    ):
        """
        Set a transformation for a specific page or domain.

        Args:
            page_index: The page index (0-based) that was selected
            transform: The transformation to apply
            domain: One of "this", "all", "even", "odd"
        """
        if domain == "this":
            # Apply to this specific page only
            self.page_transforms[page_index] = transform
            self.explicit_overrides.add(page_index)

        elif domain == "all":
            # Apply to all pages in the same position
            # For booklet layout, this means all pages at this booklet page index
            # This effectively becomes a global override
            self.page_transforms[page_index] = transform
            self.explicit_overrides.add(page_index)

        elif domain == "even":
            # Apply to all even-numbered pages (0, 2, 4, ...)
            self.even_pages_transform = transform

        elif domain == "odd":
            # Apply to all odd-numbered pages (1, 3, 5, ...)
            self.odd_pages_transform = transform

    def get_transform_for_page(self, page_index: int) -> Transform:
        """
        Get the final transformation for a specific page.
        Compounds all three layers: global + even/odd + per-page
        """
        if page_index < 0 or page_index >= self.total_pages:
            return Transform()

        global_t = self.global_transform

        # Start with global
        result = Transform(
            h_shift_mm=global_t.h_shift_mm,
            v_shift_mm=global_t.v_shift_mm,
            scale_percent=global_t.scale_percent,
            rotation_deg=global_t.rotation_deg,
            h_flip=global_t.h_flip,
            v_flip=global_t.v_flip,
            h_scale_percent=global_t.h_scale_percent,
            v_scale_percent=global_t.v_scale_percent,
        )

        # Add even/odd domain if applicable
        page_number = page_index + 1
        domain_t = None
        if page_number % 2 == 0 and self.even_pages_transform:
            domain_t = self.even_pages_transform
        elif page_number % 2 == 1 and self.odd_pages_transform:
            domain_t = self.odd_pages_transform

        if domain_t:
            result = Transform(
                h_shift_mm=result.h_shift_mm + domain_t.h_shift_mm,
                v_shift_mm=result.v_shift_mm + domain_t.v_shift_mm,
                scale_percent=result.scale_percent * domain_t.scale_percent / 100,
                rotation_deg=result.rotation_deg + domain_t.rotation_deg,
                h_flip=result.h_flip != domain_t.h_flip,
                v_flip=result.v_flip != domain_t.v_flip,
                h_scale_percent=result.h_scale_percent * domain_t.h_scale_percent / 100,
                v_scale_percent=result.v_scale_percent * domain_t.v_scale_percent / 100,
            )

        # Add per-page if applicable
        if page_index in self.page_transforms:
            page_t = self.page_transforms[page_index]
            result = Transform(
                h_shift_mm=result.h_shift_mm + page_t.h_shift_mm,
                v_shift_mm=result.v_shift_mm + page_t.v_shift_mm,
                scale_percent=result.scale_percent * page_t.scale_percent / 100,
                rotation_deg=result.rotation_deg + page_t.rotation_deg,
                h_flip=result.h_flip != page_t.h_flip,
                v_flip=result.v_flip != page_t.v_flip,
                h_scale_percent=result.h_scale_percent * page_t.h_scale_percent / 100,
                v_scale_percent=result.v_scale_percent * page_t.v_scale_percent / 100,
            )

        return result

    def clear_page_transform(self, page_index: int):
        """Clear any explicit transform for a specific page."""
        if page_index in self.page_transforms:
            del self.page_transforms[page_index]
        self.explicit_overrides.discard(page_index)

    def clear_domain_transforms(self):
        """Clear even/odd domain transforms."""
        self.even_pages_transform = None
        self.odd_pages_transform = None

    def clear_all_page_transforms(self):
        """Clear all per-page transforms (keeps global)."""
        self.page_transforms.clear()
        self.explicit_overrides.clear()
        self.clear_domain_transforms()

    def reset(self):
        """Reset everything to identity transforms."""
        self.global_transform = Transform()
        self.page_transforms.clear()
        self.explicit_overrides.clear()
        self.clear_domain_transforms()

    def has_any_transforms(self) -> bool:
        """Check if any non-identity transforms are active."""
        if not self.global_transform.is_identity():
            return True
        if self.even_pages_transform and not self.even_pages_transform.is_identity():
            return True
        if self.odd_pages_transform and not self.odd_pages_transform.is_identity():
            return True
        for transform in self.page_transforms.values():
            if not transform.is_identity():
                return True
        return False

    def get_page_only_transform(self, page_index: int) -> Transform:
        """
        Get ONLY the per-page transform (not merged with global).

        Returns the transform that was explicitly set for this page,
        or an identity transform if nothing was set.

        Args:
            page_index: The page index (0-based) in the original PDF

        Returns:
            The per-page transform only (identity if not set)
        """
        if page_index in self.page_transforms:
            return self.page_transforms[page_index]
        return Transform()  # Identity


# Convenience function for creating transforms from GUI values (MODULE-LEVEL, not in class)
def create_transform_from_gui(
    h_shift_mm: float = 0.0,
    v_shift_mm: float = 0.0,
    scale_percent: float = 100.0,
    rotation_deg: float = 0.0,
    h_flip: bool = False,
    v_flip: bool = False,
    h_scale_percent: float = 100.0,
    v_scale_percent: float = 100.0,
) -> Transform:
    """
    Create a Transform object from GUI widget values.

    This function exists to make it clear when we're converting from
    GUI units to internal representation.
    """
    return Transform(
        h_shift_mm=h_shift_mm,
        v_shift_mm=v_shift_mm,
        scale_percent=scale_percent,
        rotation_deg=rotation_deg,
        h_flip=h_flip,
        v_flip=v_flip,
        h_scale_percent=h_scale_percent,
        v_scale_percent=v_scale_percent,
    )
