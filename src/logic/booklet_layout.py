# PDFBooklet/src/logic/booklet_layout.py
"""
Pure layout generation logic.
No file I/O, no rendering, no PDF operations.
Just data structures representing page arrangements.
"""

from typing import List, Tuple, Union

# Type aliases for clarity
PageIndex = int
PagePair = Tuple[PageIndex, PageIndex]  # (left/top, right/bottom)
SinglePage = PageIndex
LayoutMap = List[Union[PagePair, SinglePage]]


class BookletLayout:
    """
    Generates page arrangement maps for different imposition modes.
    Handles padding calculations and layout logic.
    """

    def __init__(self, original_page_count: int):
        """
        Args:
            original_page_count: Number of pages in the source PDF
        """
        self.original_page_count = original_page_count
        self.active_mode = "booklet"
        self.active_layout: LayoutMap = []

        # Calculate padding needed for booklet mode (multiple of 4)
        self.padding_needed = (4 - original_page_count % 4) % 4
        self.padded_page_count = original_page_count + self.padding_needed

    def generate_booklet_layout(self) -> LayoutMap:
        """
        Generate booklet imposition (left-right spreads).

        Classic booklet folding pattern:
        - Front side: [last - 2i] | [2i]
        - Back side: [(2i)+1] | [last - ((2i)+1)]

        Returns:
            List of (left_page, right_page) tuples
        """
        layout = []
        num_sheets = self.padded_page_count // 4

        for i in range(num_sheets):
            # Front side
            front_left = self.padded_page_count - 1 - (2 * i)
            front_right = 2 * i
            layout.append((front_left, front_right))

            # Back side
            back_left = (2 * i) + 1
            back_right = self.padded_page_count - 1 - ((2 * i) + 1)
            layout.append((back_left, back_right))

        self.active_layout = layout
        self.active_mode = "booklet"
        return layout

    def generate_calendar_layout(self) -> LayoutMap:
        """
        Generate calendar imposition (top-bottom spreads).

        Sequential top-bottom pairs:
        - Page 0 on top, page 1 on bottom
        - Page 2 on top, page 3 on bottom
        - etc.

        Returns:
            List of (top_page, bottom_page) tuples
        """
        layout = []

        for i in range(0, self.original_page_count, 2):
            top = i
            bottom = i + 1 if (i + 1) < self.original_page_count else -1
            layout.append((top, bottom))

        self.active_layout = layout
        self.active_mode = "calendar"
        return layout

    def generate_single_page_layout(self) -> LayoutMap:
        """
        Generate single-page layout (one page per output sheet).

        Returns:
            List of single page indices (not tuples)
        """
        layout = list(range(self.original_page_count))

        self.active_layout = layout
        self.active_mode = "single"
        return layout

    def get_layout_count(self) -> int:
        """Returns the number of output pages/spreads in the active layout."""
        return len(self.active_layout)

    def get_page_indices(self, layout_index: int) -> Tuple[int, int]:
        """
        Get the original PDF page indices for a given layout position.

        Args:
            layout_index: Index in the layout map

        Returns:
            (first_page, second_page) tuple
            - For booklet/calendar: actual page pair
            - For single: (page, -1)
            - -1 indicates blank/missing page
        """
        if layout_index < 0 or layout_index >= len(self.active_layout):
            return -1, -1

        entry = self.active_layout[layout_index]

        if isinstance(entry, tuple):
            return entry
        else:
            # Single page mode
            return entry, -1

    def is_blank_page(self, page_index: int) -> bool:
        """
        Check if a page index represents a blank (padding) page.

        Args:
            page_index: Original PDF page index

        Returns:
            True if this is a padding page beyond original content
        """
        return page_index >= self.original_page_count
