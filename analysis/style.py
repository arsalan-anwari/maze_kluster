"""
Shared matplotlib dark-theme style for HTI analysis notebooks.
Colour tokens mirror analysis/css/index.css (shadcn dark + brand accents).

Usage in a notebook:
    import style
    style.apply()
"""
from __future__ import annotations

import matplotlib as mpl
from cycler import cycler
from matplotlib.colors import LinearSegmentedColormap

# ── Core palette (matches --* vars in css/index.css) ──────────────────────
BACKGROUND  = "#09090b"
SURFACE     = "#18181b"
BORDER      = "#27272a"
TEXT        = "#fafafa"
MUTED       = "#a1a1aa"
BROWN       = "#916f6f"
GRAY        = "#999999"

# ── Extended ramp ──────────────────────────────────────────────────────────
GRAY_100    = "#fafafa"
GRAY_200    = "#d4d4d8"
GRAY_300    = "#a1a1aa"
GRAY_400    = "#71717a"
GRAY_500    = "#52525b"

LIGHT_BROWN = "#b89090"

# ── Series palette (ordered by visual priority) ────────────────────────────
SERIES = [GRAY_100, BROWN, GRAY, GRAY_200, LIGHT_BROWN, GRAY_300, GRAY_400]

# ── Bot colours ────────────────────────────────────────────────────────────
BOT_PALETTE: dict[str, str] = {
    "baseline": GRAY_100,    # white
    "rf":       BROWN,       # warm brown
    "gbt":      GRAY,        # cool gray
    "gp":       GRAY_200,    # light gray
}

# ── Maze colour list (7 training mazes) ───────────────────────────────────
MAZE_COLORS: list[str] = [
    GRAY_100, GRAY_200, GRAY_300, BROWN, LIGHT_BROWN, GRAY, GRAY_400
]


# ── Colormaps ──────────────────────────────────────────────────────────────

def score_cmap() -> LinearSegmentedColormap:
    """Sequential: dark border → brown → near-white. For score efficiency 0→1."""
    return LinearSegmentedColormap.from_list("hti_score", [BORDER, BROWN, GRAY_100])


def div_cmap() -> LinearSegmentedColormap:
    """Diverging: gray → dark border → brown. For correlation matrices −1→+1."""
    return LinearSegmentedColormap.from_list("hti_div", [GRAY, BORDER, BROWN])


# ── Theme application ──────────────────────────────────────────────────────

def apply() -> None:
    """Apply the HTI dark theme globally to all subsequent matplotlib figures."""
    mpl.rcParams.update({
        # Figure
        "figure.facecolor":       BACKGROUND,
        "figure.edgecolor":       BACKGROUND,
        # Axes
        "axes.facecolor":         BACKGROUND,
        "axes.edgecolor":         BORDER,
        "axes.labelcolor":        TEXT,
        "axes.titlecolor":        TEXT,
        "axes.titleweight":       "bold",
        "axes.labelsize":         10,
        "axes.titlesize":         11,
        # Spines: keep left + bottom only (shadcn-style minimal frame)
        "axes.spines.top":        False,
        "axes.spines.right":      False,
        # Grid: off
        "axes.grid":              False,
        "axes.grid.which":        "both",
        # Ticks
        "xtick.color":            MUTED,
        "ytick.color":            MUTED,
        "xtick.labelcolor":       MUTED,
        "ytick.labelcolor":       MUTED,
        "xtick.labelsize":        8.5,
        "ytick.labelsize":        8.5,
        "xtick.direction":        "out",
        "ytick.direction":        "out",
        # Text / font
        "text.color":             TEXT,
        "font.family":            "sans-serif",
        "font.size":              10,
        # Lines & patches
        "lines.linewidth":        1.8,
        "patch.linewidth":        0.6,
        # Legend
        "legend.facecolor":       SURFACE,
        "legend.edgecolor":       BORDER,
        "legend.labelcolor":      TEXT,
        "legend.fontsize":        8.5,
        "legend.title_fontsize":  9,
        "legend.framealpha":      0.9,
        # SVG export
        "savefig.facecolor":      BACKGROUND,
        "savefig.edgecolor":      BACKGROUND,
        "savefig.bbox":           "tight",
        # Default colour cycle
        "axes.prop_cycle": cycler(color=SERIES),
    })
