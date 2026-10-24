import pytest

from atlasguard.drift import DriftDetector, population_stability_index


def test_psi_is_small_for_similar_distribution() -> None:
    reference = [float(i % 10) for i in range(100)]
    current = [float(i % 10) for i in range(100)]
    assert population_stability_index(reference, current) < 0.05


def test_psi_detects_distribution_shift() -> None:
    reference = [float(i % 10) for i in range(100)]
    current = [float(100 + (i % 10)) for i in range(100)]
    assert population_stability_index(reference, current) > 0.20


def test_detector_builds_baseline_then_flags_shift() -> None:
    detector = DriftDetector(baseline_size=20, window_size=20, threshold=0.20)

    for i in range(20):
        score, drifted = detector.observe(float(i % 5))
        assert score is None
        assert not drifted

    last_score = None
    last_drift = False
    for i in range(20):
        last_score, last_drift = detector.observe(float(50 + (i % 5)))

    assert last_score is not None
    assert last_drift


@pytest.mark.parametrize("bins", [0, 1, -1, True, 2.5])
def test_invalid_bucket_count_is_rejected(bins):
    with pytest.raises(ValueError):
        population_stability_index([1.0] * 20, [1.0] * 20, bins=bins)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_samples_are_rejected_without_mutating_detector(invalid):
    for reference, current in (([invalid] * 10, [1.0] * 10),
                               ([1.0] * 10, [invalid] * 10)):
        with pytest.raises(ValueError):
            population_stability_index(reference, current)
    detector = DriftDetector(baseline_size=10, window_size=10)
    with pytest.raises(ValueError):
        detector.observe(invalid)
    assert detector._baseline == []
    for value in range(10):
        detector.observe(value)
    before = list(detector._baseline)
    with pytest.raises(ValueError):
        detector.observe(invalid)
    assert detector._baseline == before
    assert list(detector._window) == []
    for value in range(10):
        score, drifted = detector.observe(value)
    assert score == 0.0
    assert not drifted


@pytest.mark.parametrize("options", [
    {"baseline_size": 9}, {"window_size": 9}, {"baseline_size": True},
    {"window_size": 10.5}, {"threshold": 0}, {"threshold": -1},
    {"threshold": float("nan")}, {"threshold": float("inf")},
])
def test_invalid_detector_configuration_fails_at_construction(options):
    with pytest.raises(ValueError):
        DriftDetector(**options)


def test_numeric_samples_are_normalized_consistently():
    assert population_stability_index([str(i) for i in range(10)],
                                      [float(i) for i in range(10)]) == 0.0
