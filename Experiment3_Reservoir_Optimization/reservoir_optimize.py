import numpy as np
from scipy.optimize import minimize

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

def solve_slsqp():
    Q0 = np.full(7, Q_eco)
    bounds = [(Q_eco, Q_max)] * 7

    cons = []
    for t in range(1, 8):
        cons.append({'type': 'ineq', 'fun': lambda Q, t=t: storage_profile(Q)[t] - V_min})
        cons.append({'type': 'ineq', 'fun': lambda Q, t=t: V_max - storage_profile(Q)[t]})

    result = minimize(objective, Q0, method='SLSQP', bounds=bounds,
                      constraints=cons, options={'maxiter': 1000, 'ftol': 1e-12})
    return result

def validate(Q):
    S = storage_profile(Q)
    rev = revenue(Q)
    eco = eco_deficit(Q)
    violations = []

    for t in range(1, 8):
        if S[t] < V_min - 1.0:
            violations.append(f"Day {t}: Storage {S[t]:.0f} m^3 < V_min {V_min}")
        if S[t] > V_max + 1.0:
            violations.append(f"Day {t}: Storage {S[t]:.0f} m^3 > V_max {V_max}")

    for t in range(7):
        if Q[t] < Q_eco - 1e-4:
            violations.append(f"Day {t+1}: Release {Q[t]:.4f} m^3/s < Q_eco {Q_eco}")
        if Q[t] > Q_max + 1e-4:
            violations.append(f"Day {t+1}: Release {Q[t]:.4f} m^3/s > Q_max {Q_max}")

    for t in range(7):
        expected = S[t] + (inflow[t] - Q[t]) * dt
        if abs(expected - S[t+1]) > 1.0:
            violations.append(f"Day {t+1}: Mass balance error: {abs(expected - S[t+1]):.2f} m^3")

    return S, rev, eco, violations

def generate_report(result, Q_opt, S_opt, rev_opt, eco_opt, violations):
    lines = []
    lines.append("=" * 60)
    lines.append("RESERVOIR OPTIMIZATION - VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Parameters:")
    lines.append(f"  Initial Storage: {S0:,} m^3")
    lines.append(f"  V_min: {V_min:,} m^3")
    lines.append(f"  V_max: {V_max:,} m^3")
    lines.append(f"  Q_eco: {Q_eco} m^3/s")
    lines.append(f"  Q_max: {Q_max} m^3/s")
    lines.append(f"  Time step: {dt} s ({dt/3600:.0f} hours)")
    lines.append(f"  Power coeff: {power_coeff:.4f} kW/(m^3/s)")
    lines.append("")
    lines.append("Optimizer Info:")
    lines.append(f"  Method: SLSQP")
    lines.append(f"  Success: {result.success}")
    lines.append(f"  Message: {result.message}")
    lines.append(f"  Iterations: {result.nit}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("1. Storage Bounds Check")
    lines.append("-" * 60)
    for t in range(8):
        S_val = S_opt[t]
        if V_min <= S_val <= V_max:
            status = "OK"
        else:
            status = "VIOLATION"
        lines.append(f"  Day {t}: Storage = {S_val:>10,.2f} m^3  [{V_min:>7,} - {V_max:>7,}]  {status}")
    lines.append(f"  Min storage: {S_opt.min():,.2f} m^3")
    lines.append(f"  Max storage: {S_opt.max():,.2f} m^3")
    lines.append("")

    lines.append("-" * 60)
    lines.append("2. Release Bounds Check")
    lines.append("-" * 60)
    for t in range(7):
        Q_val = Q_opt[t]
        if Q_eco <= Q_val <= Q_max:
            status = "OK"
        else:
            status = "VIOLATION"
        lines.append(f"  Day {t+1}: Release = {Q_val:>10.4f} m^3/s  [{Q_eco:>4} - {Q_max:>4}]  {status}")
    lines.append(f"  Min release: {Q_opt.min():.4f} m^3/s")
    lines.append(f"  Max release: {Q_opt.max():.4f} m^3/s")
    lines.append("")

    lines.append("-" * 60)
    lines.append("3. Mass Balance Check")
    lines.append("-" * 60)
    max_error = 0
    for t in range(7):
        expected = S_opt[t] + (inflow[t] - Q_opt[t]) * dt
        error = abs(expected - S_opt[t+1])
        max_error = max(max_error, error)
        status = "OK" if error < 1.0 else "ERROR"
        lines.append(f"  Day {t+1}: S_{t} + (I-Q)*dt = {S_opt[t]:,.2f} + ({inflow[t]:.0f} - {Q_opt[t]:.4f})*{dt}")
        lines.append(f"           = {expected:,.2f} vs S_opt[{t+1}]={S_opt[t+1]:,.2f}  error={error:.6f}  {status}")
    lines.append(f"  Max mass balance error: {max_error:.6f} m^3")
    lines.append("")

    lines.append("-" * 60)
    lines.append("4. Revenue Calculation")
    lines.append("-" * 60)
    daily_energies = power_coeff * Q_opt * hours_per_day
    daily_revs = daily_energies * price
    for t in range(7):
        lines.append(f"  Day {t+1}: Q={Q_opt[t]:.4f} m^3/s, Energy={daily_energies[t]:.2f} kWh, "
                     f"Price=${price[t]:.4f}/kWh, Revenue=${daily_revs[t]:.2f}")
    lines.append(f"  Total Revenue: ${rev_opt:,.2f}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("5. Ecological Compliance")
    lines.append("-" * 60)
    total_def = 0
    for t in range(7):
        deficit = max(0, Q_eco - Q_opt[t])
        total_def += deficit
        lines.append(f"  Day {t+1}: Q={Q_opt[t]:.4f}, Q_eco={Q_eco}, Deficit={deficit:.4f} m^3/s")
    lines.append(f"  Total ecological deficit: {total_def:.4f} m^3/s")
    lines.append("")

    lines.append("-" * 60)
    lines.append("6. Constraint Violation Summary")
    lines.append("-" * 60)
    if violations:
        lines.append(f"  {len(violations)} violation(s) found:")
        for v in violations:
            lines.append(f"    - {v}")
    else:
        lines.append("  No constraint violations detected (within tolerance).")
    lines.append("")

    lines.append("=" * 60)
    lines.append(f"Validation Result: {'PASS' if not violations else 'FAIL'}")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == '__main__':
    result = solve_slsqp()
    Q_opt = result.x
    S_opt, rev_opt, eco_opt, violations = validate(Q_opt)

    print(f"Optimization success: {result.success}")
    print(f"Message: {result.message}")
    print(f"Iterations: {result.nit}")
    print(f"Total revenue: ${rev_opt:,.2f}")
    print(f"Ecological deficit: {eco_opt:.2f} m^3/s")
    print(f"Optimal releases (m^3/s): {[f'{q:.4f}' for q in Q_opt]}")
    print(f"Storage profile (m^3):    {[f'{s:.2f}' for s in S_opt]}")

    days = np.arange(1, 8)
    daily_energies = power_coeff * Q_opt * hours_per_day
    daily_revs = daily_energies * price
    np.savetxt('optimal_schedule.csv',
               np.column_stack([days, inflow, Q_opt, price, daily_energies, daily_revs]),
               delimiter=',',
               header='Day,Inflow_m3s,Release_m3s,Price_per_kWh,Energy_kWh,Revenue_USD',
               comments='',
               fmt=['%d', '%.4f', '%.4f', '%.4f', '%.2f', '%.2f'])
    print("\noptimal_schedule.csv saved.")

    report = generate_report(result, Q_opt, S_opt, rev_opt, eco_opt, violations)
    with open('validation_report.txt', 'w') as f:
        f.write(report)
    print("validation_report.txt saved.")
