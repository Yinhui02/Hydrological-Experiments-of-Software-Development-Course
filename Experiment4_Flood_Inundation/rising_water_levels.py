import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from flood_inundation import generate_dem, simulate_flood

dem = generate_dem()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

def init():
    axes[0].clear()
    axes[1].clear()
    return axes[0], axes[1]

def update(wl):
    for ax in axes:
        ax.clear()
    mask, depth, pct = simulate_flood(dem, wl)

    overlay = np.dstack([np.zeros_like(dem), np.zeros_like(dem), np.ones_like(dem) * 0.6])
    overlay[~mask] = 1.0
    axes[0].imshow(dem, cmap="gray", aspect="auto")
    axes[0].imshow(overlay, aspect="auto", alpha=0.5)
    axes[0].set_title(f"Flood Extent at {wl:.1f}m ({pct:.1f}%)")

    im = axes[1].imshow(depth, cmap="Blues", aspect="auto", vmin=0, vmax=50)
    axes[1].set_title(f"Inundation Depth at {wl:.1f}m")
    return axes[0], axes[1]

levels = np.arange(30, 81, 0.5)
ani = FuncAnimation(fig, update, frames=levels, init_func=init, blit=False)
ani.save("rising_water_levels.gif", writer="pillow", fps=10, dpi=100)
print("Saved: rising_water_levels.gif")
plt.close()
