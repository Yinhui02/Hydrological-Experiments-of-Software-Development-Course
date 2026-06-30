"""
SCS-CN (Soil Conservation Service - Curve Number) runoff calculation method.

Formulas:
    S = (25400 / CN) - 254
    Ia = 0.2 * S
    Q = (P - Ia)^2 / (P - Ia + S)   for P > Ia, else 0

Where:
    P  = rainfall depth (mm)
    CN = curve number (1-100, dimensionless)
    S  = potential maximum retention (mm)
    Ia = initial abstraction (mm)
    Q  = runoff depth (mm)
"""


def calculate_runoff(P: float, CN: float) -> float:
    """Compute direct runoff using the SCS-CN method.

    Parameters
    ----------
    P  : float
        Rainfall depth in millimetres (must be >= 0).
    CN : float
        Curve number in the range [1, 100].

    Returns
    -------
    float
        Runoff depth Q in millimetres, clipped so Q <= P.
    """
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S

    if P <= Ia:
        return 0.0

    numerator = (P - Ia) ** 2
    denominator = P - Ia + S
    Q = numerator / denominator

    return min(Q, P)
