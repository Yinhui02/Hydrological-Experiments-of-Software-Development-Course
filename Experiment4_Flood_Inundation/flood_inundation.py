import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

# ========== DEM Generation ==========
def generate_dem(rows=100, cols=100, min_elev=30, max_elev=80):
    x = np.linspace(0, 1, cols)
    y = np.linspace(0, 1, rows)
    xx, yy = np.meshgrid(x, y)
    slope = 50 * (1 - yy) + 30
    noise = np.random.normal(0, 5, (rows, cols))
    dem = slope + noise
    dem = np.clip(dem, min_elev, max_elev)
    return dem

dem = generate_dem()
np.save("dem_data.npy", dem)
print(f"DEM shape: {dem.shape}, range: {dem.min():.2f} - {dem.max():.2f} m")

# ========== Flood Simulation ==========
def simulate_flood(dem, water_level):
    mask = dem < water_level
    depth = np.where(mask, water_level - dem, 0.0)
    percentage = 100.0 * np.sum(mask) / mask.size
    return mask, depth, percentage

# ========== Visualization ==========
def plot_flood_extent(dem, water_level, save_path=None):
    mask, depth, pct = simulate_flood(dem, water_level)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    im0 = axes[0].imshow(dem, cmap="terrain", aspect="auto")
    axes[0].set_title(f"Original DEM ({dem.shape[0]}\u00d7{dem.shape[1]})")
    fig.colorbar(im0, ax=axes[0], label="Elevation (m)")

    overlay = np.dstack([np.zeros_like(dem), np.zeros_like(dem), np.ones_like(dem) * 0.6])
    overlay[~mask] = 1.0
    axes[1].imshow(dem, cmap="gray", aspect="auto")
    axes[1].imshow(overlay, aspect="auto", alpha=0.5)
    axes[1].set_title(f"Flood Extent at {water_level}m ({pct:.1f}%)")

    im2 = axes[2].imshow(depth, cmap="Blues", aspect="auto", vmin=0)
    axes[2].set_title("Inundation Depth (m)")
    fig.colorbar(im2, ax=axes[2], label="Depth (m)")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")
    plt.close()

def side_by_side_comparison(dem, levels, save_path=None):
    fig, axes = plt.subplots(1, len(levels), figsize=(6 * len(levels), 5))
    if len(levels) == 1:
        axes = [axes]
    for ax, wl in zip(axes, levels):
        mask, depth, pct = simulate_flood(dem, wl)
        overlay = np.dstack([np.zeros_like(dem), np.zeros_like(dem), np.ones_like(dem) * 0.6])
        overlay[~mask] = 1.0
        ax.imshow(dem, cmap="gray", aspect="auto")
        ax.imshow(overlay, aspect="auto", alpha=0.5)
        ax.set_title(f"Water Level {wl}m\nFlooded: {pct:.1f}%")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")
    plt.close()

plot_flood_extent(dem, 40, "flood_extent_40m.png")
plot_flood_extent(dem, 50, "flood_extent_50m.png")
side_by_side_comparison(dem, [40, 45, 50], "comparison_side_by_side.png")

# ========== Dynamic Simulation ==========
def dynamic_simulation(dem, levels):
    percentages = []
    for wl in levels:
        _, _, pct = simulate_flood(dem, wl)
        percentages.append(pct)
    return percentages

levels = np.arange(30, 81, 1)
percentages = dynamic_simulation(dem, levels)
is_monotonic = all(percentages[i] <= percentages[i+1] for i in range(len(percentages)-1))

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(levels, percentages, "b-", linewidth=2)
ax.axvline(40, color="gray", linestyle="--", alpha=0.5, label="40m")
ax.axvline(50, color="red", linestyle="--", alpha=0.5, label="50m")
ax.set_xlabel("Water Level (m)")
ax.set_ylabel("Flooded Area (%)")
ax.set_title(f"Water Level vs. Flooded Percentage\nMonotonic: {is_monotonic}")
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig("flood_curve.png", dpi=150, bbox_inches="tight")
print(f"Saved: flood_curve.png")
plt.close()
print(f"Flooded area increases monotonically: {is_monotonic}")

# ========== Validation ==========
print("\n========== Validation ==========")
min_elev = dem.min()
max_elev = dem.max()
print(f"DEM elevation range: {min_elev:.2f} - {max_elev:.2f} m")

# 1. Monotonic check
print(f"1. Flooded area increases with water level: {is_monotonic}")

# 2. Max depth check at various levels
for wl in [35, 45, 55, 70]:
    _, depth, pct = simulate_flood(dem, wl)
    theoretical_max = max(0, wl - min_elev)
    actual_max = depth.max()
    print(f"2. Water level {wl}m: max depth={actual_max:.2f}m, theoretical max={theoretical_max:.2f}m, match={np.isclose(actual_max, theoretical_max)}")

# 3. Percentage range check
for wl in [20, 40, 50, 90]:
    _, _, pct = simulate_flood(dem, wl)
    in_range = 0 <= pct <= 100
    print(f"3. Water level {wl}m: {pct:.2f}% (0-100%: {in_range})")

# 4. Edge cases
mask_below, _, pct_below = simulate_flood(dem, min_elev - 5)
mask_above, _, pct_above = simulate_flood(dem, max_elev + 5)
print(f"4. Below min elevation ({(min_elev-5):.1f}m): flooded%={pct_below:.2f}%, any flooded={mask_below.any()}")
print(f"4. Above max elevation ({(max_elev+5):.1f}m): flooded%={pct_above:.2f}%, all flooded={mask_above.all()}")

print("\nAll deliverables generated successfully.")
