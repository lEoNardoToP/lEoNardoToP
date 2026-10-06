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
