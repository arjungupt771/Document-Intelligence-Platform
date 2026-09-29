import pytest

from app.drift.psi import bin_numeric, population_stability_index, proportions, quantile_edges


def test_psi_is_zero_for_identical_distributions():
    dist = {"a": 0.5, "b": 0.5}
    assert population_stability_index(dist, dist) == pytest.approx(0.0, abs=1e-9)


def test_psi_is_positive_for_shifted_distributions():
    baseline = {"a": 0.9, "b": 0.1}
    current = {"a": 0.5, "b": 0.5}
    assert population_stability_index(baseline, current) > 0.1


def test_psi_handles_a_bucket_only_present_on_one_side():
    baseline = {"a": 1.0}
    current = {"a": 0.5, "b": 0.5}
    score = population_stability_index(baseline, current)
    assert score > 0


def test_proportions_normalizes_counts():
    result = proportions({"a": 3, "b": 1})
    assert result == {"a": 0.75, "b": 0.25}


def test_proportions_empty_counts_returns_empty():
    assert proportions({}) == {}


def test_bin_numeric_places_values_in_expected_buckets():
    counts = bin_numeric([50, 150, 750, 5000], bin_edges=[100, 500, 1000])
    assert counts["<100"] == 1
    assert counts["100-500"] == 1
    assert counts["500-1000"] == 1
    assert counts[">1000"] == 1


def test_quantile_edges_returns_fewer_bins_for_small_samples():
    edges = quantile_edges([1, 2], n_bins=5)
    assert len(edges) <= 2