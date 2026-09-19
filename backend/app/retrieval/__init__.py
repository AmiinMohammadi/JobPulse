"""Retrieval & generation pipeline for Job Pulse.

Stage 5 adds the retrieval logic; Stage 6 adds the LLM-based gap analysis.
"""

from app.retrieval.generation import generate_gap_analysis

__all__ = ["generate_gap_analysis"]
