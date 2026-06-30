import numpy as np
from scipy.optimize import minimize
import time

S0 = 500_000
V_min = 100_000
V_max = 1_000_000
Q_eco = 10
Q_max = 100
inflow = np.array([15, 12, 10, 8, 12, 15, 18])
price = np.array([0.08, 0.08, 0.08, 0.08, 0.10, 0.12, 0.10])
dt = 24 * 3600

eta = 0.85
head = 30
g = 9.81
rho = 1000
power_coeff = eta * rho * g * head / 1000
hours_per_day = 24

def storage_profile(Q):
    S = np.zeros(8)
    S[0] = S0
    for t in range(7):
        S[t+1] = S[t] + (inflow[t] - Q[t]) * dt
    return S

def revenue(Q):
    daily_energy = power_coeff * Q * hours_per_day
    return np.sum(daily_energy * price)

def eco_deficit(Q):
    return np.sum(np.maximum(0, Q_eco - Q))

def objective(Q):
    return -revenue(Q)

def make_storage_cons():
    cons = []
    for t in range(1, 8):
        cons.append({'type': 'ineq', 'fun': lambda Q, t=t: storage_profile(Q)[t] - V_min})
        cons.append({'type': 'ineq', 'fun': lambda Q, t=t: V_max - storage_profile(Q)[t]})
    return cons

def penalty_objective(Q, penalty_weight=1e5):
    S = storage_profile(Q)
    obj = -revenue(Q)
    for t in range(1, 8):
        if S[t] < V_min:
            obj += penalty_weight * (V_min - S[t]) ** 2
        if S[t] > V_max:
            obj += penalty_weight * (S[t] - V_max) ** 2
    return obj


def run_slsqp(maxiter=1000):
    Q0 = np.full(7, Q_eco)
    bounds = [(Q_eco, Q_max)] * 7
    cons = make_storage_cons()

    start = time.time()
    result = minimize(objective, Q0, method='SLSQP', bounds=bounds,
                      constraints=cons, options={'maxiter': maxiter, 'ftol': 1e-12})
    elapsed = time.time() - start
    return result, elapsed


def run_lbfgsb(maxiter=1000, penalty_weight=1e5):
    Q0 = np.full(7, Q_eco)
    bounds = [(Q_eco, Q_max)] * 7

    start = time.time()
    result = minimize(lambda Q: penalty_objective(Q, penalty_weight), Q0,
                      method='L-BFGS-B', bounds=bounds,
                      options={'maxiter': maxiter, 'ftol': 1e-12})
    elapsed = time.time() - start
    return result, elapsed


def validate_solution(Q):
    S = storage_profile(Q)
    rev = revenue(Q)
    eco = eco_deficit(Q)
    violations = []

    for t in range(1, 8):
        if S[t] < V_min - 1.0:
            violations.append(f"Day {t}: Storage {S[t]:.0f} < V_min {V_min}")
        if S[t] > V_max + 1.0:
            violations.append(f"Day {t}: Storage {S[t]:.0f} > V_max {V_max}")
    for t in range(7):
        if Q[t] < Q_eco - 1e-4:
            violations.append(f"Day {t+1}: Release {Q[t]:.6f} < Q_eco {Q_eco}")
        if Q[t] > Q_max + 1e-4:
            violations.append(f"Day {t+1}: Release {Q[t]:.6f} > Q_max {Q_max}")

    return S, rev, eco, violations


def extract_feasible(result, Q_default=None):
    Q = result.x
    S = storage_profile(Q)
    ok = True
    for t in range(1, 8):
        if S[t] < V_min - 1.0 or S[t] > V_max + 1.0:
            ok = False
            break
    if ok:
        for q in Q:
            if q < -0.1 or q > Q_max + 0.1:
                ok = False
                break
    if ok:
        return Q
    return Q_default if Q_default is not None else np.full(7, Q_eco)


def feasible_Q(Q):
    S = storage_profile(Q)
    for t in range(1, 8):
        if S[t] < V_min - 1.0 or S[t] > V_max + 1.0:
            return False
    for q in Q:
        if q < -0.1 or q > Q_max + 0.1:
            return False
    return True


def _pareto_filter(deficits, revenues):
    if len(deficits) == 0:
        return deficits, revenues
    # Round to avoid floating point duplicates
    d_rounded = np.round(deficits, 4)
    r_rounded = np.round(revenues, 2)
    uniq = {}
    for d, r in zip(d_rounded, r_rounded):
        if d not in uniq or r > uniq[d]:
            uniq[d] = r
    d_s = np.array(sorted(uniq.keys()))
    r_s = np.array([uniq[d] for d in d_s])
    # Pareto dominance filter
    mask = np.ones(len(d_s), dtype=bool)
    max_r = -np.inf
    for j in range(len(d_s)):
        if r_s[j] <= max_r:
            mask[j] = False
        else:
            max_r = r_s[j]
    return d_s[mask], r_s[mask]


def tradeoff_analysis():
    cons = make_storage_cons()

    # Solve eco-baseline (all releases >= Q_eco)
    res_base = minimize(lambda Q: -revenue(Q), np.full(7, Q_eco), method='SLSQP',
                        bounds=[(Q_eco, Q_max)] * 7, constraints=cons,
                        options={'maxiter': 1000, 'ftol': 1e-12})
    Q_prev = extract_feasible(res_base, np.full(7, Q_eco))
    all_d = [eco_deficit(Q_prev)]
    all_r = [revenue(Q_prev)]

    # Sweep weights from revenue-priority to ecology-priority
    # Use Q_prev (always feasible) as warm start for each weight
    for w in np.logspace(-2, 5, 60):
        def weighted_obj(Q):
            return -revenue(Q) + w * eco_deficit(Q)
        res = minimize(weighted_obj, Q_prev, method='SLSQP',
                       bounds=[(0, Q_max)] * 7, constraints=cons,
                       options={'maxiter': 1000, 'ftol': 1e-12})
        Q_new = extract_feasible(res, Q_prev)
        if not feasible_Q(Q_new):
            continue
        if np.allclose(Q_new, Q_prev, atol=1e-4):
            continue
        Q_prev = Q_new
        all_d.append(eco_deficit(Q_prev))
        all_r.append(revenue(Q_prev))

    return _pareto_filter(np.array(all_d), np.array(all_r))


def run_comparison():
    lines = []
    lines.append("=" * 60)
    lines.append("ALGORITHM COMPARISON ANALYSIS: SLSQP vs L-BFGS-B")
    lines.append("=" * 60)
    lines.append("")

    res_slsqp, t_slsqp = run_slsqp()
    res_lbfgsb, t_lbfgsb = run_lbfgsb()

    S_slsqp, rev_slsqp, eco_slsqp, viol_slsqp = validate_solution(res_slsqp.x)
    S_lbfgsb, rev_lbfgsb, eco_lbfgsb, viol_lbfgsb = validate_solution(res_lbfgsb.x)

    lines.append("1. Convergence Behavior:")
    lines.append(f"   SLSQP:    success={res_slsqp.success}, message='{res_slsqp.message.strip()}'")
    lines.append(f"   L-BFGS-B: success={res_lbfgsb.success}, message='{res_lbfgsb.message.strip()}'")
    lines.append("")

    lines.append("2. Solution Quality:")
    lines.append(f"   {'Metric':<30} {'SLSQP':<20} {'L-BFGS-B':<20}")
    lines.append("   " + "-" * 70)
    lines.append(f"   {'Total Revenue ($)':<30} {rev_slsqp:<20,.2f} {rev_lbfgsb:<20,.2f}")
    lines.append(f"   {'Eco Deficit (m^3/s)':<30} {eco_slsqp:<20.4f} {eco_lbfgsb:<20.4f}")
    lines.append(f"   {'Violations':<30} {len(viol_slsqp):<20} {len(viol_lbfgsb):<20}")
    lines.append(f"   {'Final Storage (m^3)':<30} {S_slsqp[-1]:<20,.2f} {S_lbfgsb[-1]:<20,.2f}")

    lines.append(f"\n   Release Schedule (m^3/s):")
    lines.append(f"   {'Day':<8} {'SLSQP':<20} {'L-BFGS-B':<20}")
    lines.append("   " + "-" * 48)
    for t in range(7):
        lines.append(f"   {t+1:<8} {res_slsqp.x[t]:<20.6f} {res_lbfgsb.x[t]:<20.6f}")
    lines.append("")

    lines.append(f"   Storage Profile (m^3):")
    lines.append(f"   {'Day':<8} {'SLSQP':<20} {'L-BFGS-B':<20}")
    lines.append("   " + "-" * 48)
    for t in range(8):
        lines.append(f"   {t:<8} {S_slsqp[t]:<20,.2f} {S_lbfgsb[t]:<20,.2f}")
    lines.append("")

    lines.append("3. Computational Performance:")
    lines.append(f"   SLSQP:    {t_slsqp:.6f}s, {res_slsqp.nit} iterations")
    lines.append(f"   L-BFGS-B: {t_lbfgsb:.6f}s, {res_lbfgsb.nit} iterations")
    if t_slsqp < t_lbfgsb:
        lines.append(f"   SLSQP is {t_lbfgsb/t_slsqp:.1f}x faster")
    else:
        lines.append(f"   L-BFGS-B is {t_slsqp/t_lbfgsb:.1f}x faster")
    lines.append("")

    lines.append("4. Constraint Satisfaction:")
    lines.append("   SLSQP:")
    if viol_slsqp:
        lines.append(f"     {len(viol_slsqp)} violation(s):")
        for v in viol_slsqp:
            lines.append(f"       - {v}")
    else:
        lines.append("     All constraints satisfied.")
    lines.append("   L-BFGS-B:")
    if viol_lbfgsb:
        lines.append(f"     {len(viol_lbfgsb)} violation(s):")
        for v in viol_lbfgsb:
            lines.append(f"       - {v}")
    else:
        lines.append("     All constraints satisfied.")
    lines.append("")

    rev_diff = abs(rev_slsqp - rev_lbfgsb)
    lines.append("5. Key Differences:")
    lines.append(f"   - SLSQP uses exact constraint handling (Lagrange multipliers).")
    lines.append(f"     Storage constraints are strictly enforced.")
    lines.append(f"   - L-BFGS-B uses penalty method for storage constraints,")
    lines.append(f"     which may cause small violations if penalty weight is insufficient.")
    lines.append(f"   - Revenue difference: ${rev_diff:.2f}")
    lines.append(f"   - L-BFGS-B may fail to fully utilize high-price periods because")
    lines.append(f"     the penalty objective may not perfectly enforce storage constraints.")
    lines.append("")

    lines.append("6. Recommendation:")
    lines.append("   SLSQP is the preferred method for this reservoir optimization")
    lines.append("   problem because it natively handles nonlinear inequality")
    lines.append("   constraints (storage bounds) via exact Lagrange multiplier")
    lines.append("   methods. L-BFGS-B requires penalty-based approximation which")
    lines.append("   can compromise solution quality.")
    lines.append("")

    lines.append("7. Trade-off Analysis Summary:")
    lines.append("   - The Pareto frontier (tradeoff_analysis.png) shows the")
    lines.append("     relationship between hydropower revenue and ecological deficit.")
    lines.append("   - Prioritizing ecology (low deficit) requires reducing releases")
    lines.append("     during high-price periods, lowering revenue.")
    lines.append("   - Zero ecological deficit is achieved when all releases >= Q_eco.")
    lines.append("   - Maximum revenue occurs with largest possible releases during")
    lines.append("     high-price periods, but is limited by storage constraints.")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("Running algorithm comparison...")
    report = run_comparison()

    with open('algorithms_compare.txt', 'w') as f:
        f.write(report)
    print("algorithms_compare.txt saved.")

    print("Running trade-off analysis for Pareto frontier...")
    deficits, revenues = tradeoff_analysis()

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(deficits, revenues, 'b-o', markersize=6, linewidth=1.5, label='Pareto frontier',
            markerfacecolor='white', markeredgewidth=1.5)

    if len(deficits) > 0:
        idx_max_rev = np.argmax(revenues)
        idx_min_dec = np.argmin(deficits)

        ax.plot(deficits[idx_max_rev], revenues[idx_max_rev], 'rs', markersize=10,
                label=f'Max revenue ${revenues[idx_max_rev]:.0f}')
        ax.plot(deficits[idx_min_dec], revenues[idx_min_dec], 'gs', markersize=10,
                label=f'Min deficit {deficits[idx_min_dec]:.2f} m$^3$/s')

        ax.annotate('Prioritize\nRevenue',
                    xy=(deficits[idx_max_rev], revenues[idx_max_rev]),
                    xytext=(deficits[idx_max_rev] + max(deficits)*0.1, revenues[idx_max_rev] - abs(revenues[idx_max_rev]-revenues[idx_min_dec])*0.3),
                    arrowprops=dict(arrowstyle='->', color='red', lw=1.5), fontsize=10, color='red', fontweight='bold')
        ax.annotate('Prioritize\nEcology',
                    xy=(deficits[idx_min_dec], revenues[idx_min_dec]),
                    xytext=(deficits[idx_min_dec] + max(deficits)*0.1, revenues[idx_min_dec] + abs(revenues[idx_max_rev]-revenues[idx_min_dec])*0.3),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1.5), fontsize=10, color='green', fontweight='bold')

        # Fill area under the curve
        ax.fill_between(deficits, revenues, alpha=0.15, color='blue')

    ax.set_xlabel('Ecological Deficit (m$^3$/s)', fontsize=12)
    ax.set_ylabel('Hydropower Revenue ($)', fontsize=12)
    ax.set_title('Pareto Frontier: Hydropower Revenue vs Ecological Deficit', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='lower right')

    fig.subplots_adjust(left=0.12, right=0.88, top=0.92, bottom=0.12)
    plt.savefig('tradeoff_analysis.png', dpi=150)
    plt.close()
    print("tradeoff_analysis.png saved.")
