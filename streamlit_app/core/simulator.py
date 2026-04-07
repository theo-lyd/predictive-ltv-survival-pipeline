"""Discount what-if simulator utilities."""

from __future__ import annotations


def simulate_nrr_impact(
    base_nrr: float,
    discount_percent: float,
    elasticity: float,
    floor_nrr: float = 0.7,
) -> float:
    """Estimate NRR after discount policy change.

    A positive elasticity implies conversion/retention improvements from discounting,
    while too much discounting applies a mild diminishing-return penalty.
    """
    discount_factor = discount_percent / 100.0
    uplift = discount_factor * elasticity
    diminishing_penalty = max(0.0, discount_factor - 0.20) * 0.25
    projected_nrr = base_nrr * (1.0 + uplift - diminishing_penalty)
    return max(floor_nrr, projected_nrr)
