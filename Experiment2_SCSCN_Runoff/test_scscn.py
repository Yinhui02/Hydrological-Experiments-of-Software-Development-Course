"""Comprehensive tests for the SCS-CN runoff calculation."""

import math

from scscn_runoff import calculate_runoff


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def approx_eq(actual: float, expected: float, tol: float = 1e-9) -> bool:
    """Return True if *actual* is within *tol* of *expected*."""
    return abs(actual - expected) <= tol


def test_P_zero() -> None:
    """Q must be 0 when there is no rainfall."""
    assert calculate_runoff(0.0, 80) == 0.0
    assert calculate_runoff(0.0, 100) == 0.0
    assert calculate_runoff(0.0, 1) == 0.0
    print("[PASS] test_P_zero")


def test_P_less_than_Ia() -> None:
    """Q must be 0 when rainfall is less than initial abstraction."""
    CN = 80
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S
    P_just_below = Ia * 0.999
    assert calculate_runoff(P_just_below, CN) == 0.0
    print("[PASS] test_P_less_than_Ia")


def test_P_equals_Ia() -> None:
    """Q must be 0 when rainfall exactly equals Ia."""
    CN = 80
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S
    assert calculate_runoff(Ia, CN) == 0.0
    print("[PASS] test_P_equals_Ia")


def test_normal_case() -> None:
    """Known result for P = 50 mm, CN = 80."""
    P, CN = 50.0, 80.0
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S
    expected_numerator = (P - Ia) ** 2
    expected_denominator = P - Ia + S
    expected = expected_numerator / expected_denominator
    result = calculate_runoff(P, CN)
    assert approx_eq(result, expected), f"{result} != {expected}"
    print("[PASS] test_normal_case")


def test_max_CN() -> None:
    """CN = 100 => S = 0, Ia = 0, so Q should equal P (> 0)."""
    for P in [1.0, 10.0, 50.0, 100.0]:
        result = calculate_runoff(P, 100.0)
        assert approx_eq(result, P), f"CN=100, P={P}: Q={result} != P"
    print("[PASS] test_max_CN")


def test_min_CN() -> None:
    """CN = 1 => very large S, Ia >> any reasonable P, so Q = 0."""
    for P in [0.0, 10.0, 50.0, 100.0]:
        assert calculate_runoff(P, 1.0) == 0.0
    print("[PASS] test_min_CN")


def test_Q_never_exceeds_P() -> None:
    """Runoff must always be ≤ rainfall for a range of inputs."""
    for P in [0, 1, 5, 10, 25, 50, 100, 200]:
        for CN in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]:
            Q = calculate_runoff(float(P), float(CN))
            assert Q <= P + 1e-12, f"Q={Q} > P={P} for CN={CN}"
    print("[PASS] test_Q_never_exceeds_P")


def test_monotonic_CN() -> None:
    """For fixed P, a higher CN must never produce less runoff."""
    P = 50.0
    CN_values = list(range(1, 101))
    Qs = [calculate_runoff(P, float(CN)) for CN in CN_values]
    for i in range(len(Qs) - 1):
        assert Qs[i] <= Qs[i + 1] + 1e-12, (
            f"Non-monotonic at CN={CN_values[i]}: Q={Qs[i]} > Q={Qs[i+1]}"
        )
    print("[PASS] test_monotonic_CN")


def test_no_negative_runoff() -> None:
    """Runoff must never be negative."""
    for P in [0, 1, 5, 10, 25, 50, 100]:
        for CN in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]:
            Q = calculate_runoff(float(P), float(CN))
            assert Q >= 0, f"Negative Q={Q} for P={P}, CN={CN}"
    print("[PASS] test_no_negative_runoff")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_P_zero()
    test_P_less_than_Ia()
    test_P_equals_Ia()
    test_normal_case()
    test_max_CN()
    test_min_CN()
    test_Q_never_exceeds_P()
    test_monotonic_CN()
    test_no_negative_runoff()
    print("\nAll tests passed.")
