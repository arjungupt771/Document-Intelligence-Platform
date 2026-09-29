from __future__ import annotations

import math


def population_stability_index(baseline: dict[str, float], current: dict[str, float]) -> float:
    """
    Standard PSI over two distributions expressed as {bucket_label:
    proportion} (each should sum to ~1.0). A bucket present on only one
    side is given a small epsilon share on the other rather than dropped,
    so a genuinely new category still contributes to the score instead of
    silently vanishing.
    """
    epsilon = 1e-4
    buckets = set(baseline) | set(current)
    psi = 0.0
    for bucket in buckets:
        b = max(baseline.get(bucket, 0.0), epsilon)
        c = max(current.get(bucket, 0.0), epsilon)
        psi += (c - b) * math.log(c / b)
    return psi


def proportions(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {}
    return {key: value / total for key, value in counts.items()}


def quantile_edges(values: list[float], n_bins: int = 5) -> list[float]:
    """Baseline-derived bin edges (quantiles of the baseline sample), so bins fit that field's actual scale."""
    if len(values) < n_bins:
        return sorted(set(values))
    sorted_values = sorted(values)
    step = len(sorted_values) / n_bins
    return [sorted_values[int(step * i)] for i in range(1, n_bins)]


def bin_numeric(values: list[float], bin_edges: list[float]) -> dict[str, int]:
    """
    Buckets values against ascending bin_edges, e.g. edges=[100, 500,
    1000] -> buckets '<100', '100-500', '500-1000', '>1000'.
    """
    if not bin_edges:
        return {"all": len(values)}

    labels = [f"<{bin_edges[0]}"]
    labels += [f"{lo}-{hi}" for lo, hi in zip(bin_edges, bin_edges[1:])]
    labels.append(f">{bin_edges[-1]}")

    counts = {label: 0 for label in labels}
    for value in values:
        placed = False
        for i, edge in enumerate(bin_edges):
            if value < edge:
                counts[labels[i]] += 1
                placed = True
                break
        if not placed:
            counts[labels[-1]] += 1
    return counts