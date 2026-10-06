from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("cannot compute quantile of empty input")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def population_stability_index(
    reference: list[float], current: list[float], bins: int = 10
) -> float:
    """Compute PSI using quantile buckets derived from the reference distribution."""
    if len(reference) < bins or len(current) < bins:
        raise ValueError("reference and current windows need at least bins values")

    ref = sorted(float(x) for x in reference)
    boundaries = [_quantile(ref, i / bins) for i in range(1, bins)]
    boundaries = sorted(set(boundaries))

    def bucket_counts(values: list[float]) -> list[int]:
        counts = [0] * (len(boundaries) + 1)
        for value in values:
            idx = 0
            while idx < len(boundaries) and value > boundaries[idx]:
                idx += 1
            counts[idx] += 1
        return counts

    ref_counts = bucket_counts(reference)
    cur_counts = bucket_counts(current)
    eps = 1e-6
    score = 0.0
    for r_count, c_count in zip(ref_counts, cur_counts):
        r = max(r_count / len(reference), eps)
        c = max(c_count / len(current), eps)
        score += (c - r) * math.log(c / r)
    return score


@dataclass
class DriftDetector:
    baseline_size: int = 100
    window_size: int = 100
    threshold: float = 0.20
    _baseline: list[float] = field(default_factory=list)
    _window: deque[float] = field(default_factory=lambda: deque(maxlen=100))

    def __post_init__(self) -> None:
        self._window = deque(maxlen=self.window_size)

    def observe(self, value: float) -> tuple[float | None, bool]:
        value = float(value)
        if len(self._baseline) < self.baseline_size:
            self._baseline.append(value)
            return None, False

        self._window.append(value)
        if len(self._window) < self.window_size:
            return None, False

        score = population_stability_index(self._baseline, list(self._window))
        return score, score >= self.threshold
