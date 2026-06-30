import numpy as np
import matplotlib.pyplot as plt
from flood_inundation import generate_dem, simulate_flood

dem = generate_dem()

# ========== Add Building Footprints ==========
def add_building_footprints(dem, num_buildings=8):
    building_dem = dem.copy()
    building_mask = np.zeros_like(dem, dtype=bool)
    rows, cols = dem.shape
    for _ in range(num_buildings):
        h = np.random.randint(5, 15)
        w = np.random.randint(5, 15)
        r = np.random.randint(0, rows - h)
        c = np.random.randint(0, cols - w)
        building_dem[r:r+h, c:c+w] = 100.0
        building_mask[r:r+h, c:c+w] = True
    return building_dem, building_mask

building_dem, building_mask = add_building_footprints(dem, 10)

# ========== Flood Curve Comparison ==========
levels = np.arange(30, 81, 1)
pct_no_build = []
pct_with_build = []

for wl in levels:
    _, _, p = simulate_flood(dem, wl)
    pct_no_build.append(p)
    _, _, p = simulate_flood(building_dem, wl)
    pct_with_build.append(p)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

axes[0].imshow(building_dem, cmap="terrain", aspect="auto")
axes[0].set_title("DEM with Building Footprints\n(Buildings in white)")
axes[0].imshow(building_mask, cmap="gray", aspect="auto", alpha=0.3)

wl_sample = 45
mask_no, depth_no, _ = simulate_flood(dem, wl_sample)
overlay_no = np.dstack([np.zeros_like(dem), np.zeros_like(dem), np.ones_like(dem) * 0.6])
overlay_no[~mask_no] = 1.0
mask_with, depth_with, _ = simulate_flood(building_dem, wl_sample)
overlay_with = np.dstack([np.zeros_like(building_dem), np.zeros_like(building_dem), np.ones_like(building_dem) * 0.6])
overlay_with[~mask_with] = 1.0

axes[1].imshow(dem, cmap="gray", aspect="auto")
axes[1].imshow(overlay_no, aspect="auto", alpha=0.5)
axes[1].set_title(f"No Buildings - Flood at {wl_sample}m\n({np.sum(mask_no)/mask_no.size*100:.1f}%)")

axes[2].imshow(building_dem, cmap="gray", aspect="auto")
axes[2].imshow(overlay_with, aspect="auto", alpha=0.5)
axes[2].set_title(f"With Buildings - Flood at {wl_sample}m\n({np.sum(mask_with)/mask_with.size*100:.1f}%)")

plt.tight_layout()
plt.savefig("flood_comparison_buildings.png", dpi=150, bbox_inches="tight")
print("Saved: flood_comparison_buildings.png")
plt.close()

# ========== Flood Curve with Buildings ==========
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(levels, pct_no_build, "b-", linewidth=2, label="No Buildings")
ax.plot(levels, pct_with_build, "r-", linewidth=2, label="With Buildings")
ax.set_xlabel("Water Level (m)")
ax.set_ylabel("Flooded Area (%)")
ax.set_title("Water Level vs. Flooded Percentage\nEffect of Building Footprints")
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig("flood_curve_add_building.png", dpi=150, bbox_inches="tight")
print("Saved: flood_curve_add_building.png")
plt.close()

print("Building footprints simulation complete.")
