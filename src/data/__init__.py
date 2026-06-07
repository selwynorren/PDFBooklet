# PDFBooklet/src/data/__init__.py
"""
Data tier: persistence and data models.

Dependency rule: this tier imports NOTHING from src.logic or src.gui. Higher tiers
depend on it, never the reverse (GUI -> Logic -> Data).
"""
