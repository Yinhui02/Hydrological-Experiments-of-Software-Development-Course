"""Sensitivity analysis and interactive visualisation for the SCS-CN method."""

import numpy as np
from matplotlib import pyplot as plt

from scscn_runoff import calculate_runoff


# ---------------------------------------------------------------------------
# 1.  CN sensitivity at fixed P = 50 mm
# ---------------------------------------------------------------------------

def plot_cn_sensitivity(P_fixed: float = 50.0) -> plt.Figure:
    """Line plot: curve number vs runoff for a given rainfall depth."""
    CN_vals = np.array([60, 70, 80, 90, 95, 100])
    Q_vals = np.array([calculate_runoff(P_fixed, float(cn)) for cn in CN_vals])

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(CN_vals, Q_vals, marker="o", linestyle="-", color="tab:blue")
    ax.set_xlabel("Curve Number (CN)")
    ax.set_ylabel(f"Runoff Q (mm) for P = {P_fixed} mm")
    ax.set_title("SCS-CN Sensitivity: CN vs Runoff")
    ax.grid(True, linestyle="--", alpha=0.6)

    for cn, q in zip(CN_vals, Q_vals):
        ax.annotate(f"({cn}, {q:.2f})", (cn, q),
                    textcoords="offset points", xytext=(0, 10), ha="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 2.  Rainfall-runoff comparison for different CN values
# ---------------------------------------------------------------------------

def plot_rainfall_runoff_comparison() -> plt.Figure:
    """Comparison plot: rainfall (P) vs runoff (Q) for several CN curves."""
    P_range = np.linspace(0, 150, 300)
    CN_curves = [60, 70, 80, 90, 95, 100]

    fig, ax = plt.subplots(figsize=(8, 5))
    for CN in CN_curves:
        Q = np.array([calculate_runoff(p, float(CN)) for p in P_range])
        ax.plot(P_range, Q, label=f"CN = {CN}")

    ax.plot(P_range, P_range, "k--", linewidth=0.8, label="Q = P (limit)")
    ax.set_xlabel("Rainfall P (mm)")
    ax.set_ylabel("Runoff Q (mm)")
    ax.set_title("Rainfall-Runoff Curves for Different CN Values")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 150)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 3.  Interactive widget (ipywidgets / Jupyter compatible)
# ---------------------------------------------------------------------------

try:
    from ipywidgets import interact, FloatSlider
    _HAS_IPYWIDGETS = True
except ImportError:
    _HAS_IPYWIDGETS = False


def interactive_runoff(P: float = 50.0, CN: float = 80.0) -> None:
    """Compute and print runoff for interactive slider values."""
    Q = calculate_runoff(P, CN)
    S = (25400.0 / CN) - 254.0
    Ia = 0.2 * S
    print(f"P  = {P:.1f} mm")
    print(f"CN = {CN:.1f}")
    print(f"S  = {S:.2f} mm")
    print(f"Ia = {Ia:.2f} mm")
    print(f"Q  = {Q:.2f} mm")


def launch_interactive() -> None:
    """Launch an interactive widget (requires ipywidgets in Jupyter)."""
    if not _HAS_IPYWIDGETS:
        print("ipywidgets is not installed.  Install with:  pip install ipywidgets")
        return

    interact(
        interactive_runoff,
        P=FloatSlider(value=50.0, min=0, max=200, step=1, description="P (mm)"),
        CN=FloatSlider(value=80.0, min=1, max=100, step=1, description="CN"),
    )


# ---------------------------------------------------------------------------
# 4.  Documentation of observations
# ---------------------------------------------------------------------------

OBSERVATIONS = """
SCS-CN Sensitivity Analysis — Observations
===========================================

1. CN vs Runoff (fixed P = 50 mm):
   - Runoff increases non-linearly as CN increases.
   - The increase is gradual at low CN and sharp at high CN (> 90).
   - At CN = 100, all rainfall becomes runoff (Q = P) because S = 0.

2. Rainfall-Runoff curves:
   - For low CN (e.g. 60), runoff only begins after significant rainfall
     because Ia is large.
   - As CN increases, the curves shift upward, meaning more runoff for the
     same rainfall depth.
   - All curves approach the Q = P line asymptotically as P grows large.
   - The initial abstraction Ia creates a "threshold" effect — no runoff
     until P exceeds Ia.

3. Physical correctness:
   - Q is always non-negative and never exceeds P.
   - Higher CN always produces equal or greater runoff (monotonic).
   - Q = 0 when P <= Ia (no runoff for small events on dry/wet soil).
   - Q = P when CN = 100 (impervious surface).
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(OBSERVATIONS)

    fig1 = plot_cn_sensitivity()
    fig1.savefig("cn_sensitivity.png", dpi=150)
    print("[SAVED] cn_sensitivity.png")

    fig2 = plot_rainfall_runoff_comparison()
    fig2.savefig("rainfall_runoff_comparison.png", dpi=150)
    print("[SAVED] rainfall_runoff_comparison.png")

    plt.show()

    # Quick reference values for the report
    print("\n--- Reference: P = 50 mm ---")
    for CN in [60, 70, 80, 90, 95, 100]:
        Q = calculate_runoff(50.0, float(CN))
        print(f"  CN = {CN:3d}  ->  Q = {Q:.2f} mm")
