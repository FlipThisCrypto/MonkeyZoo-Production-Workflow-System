#!/usr/bin/env python3
"""Genesis page layout synthesizer — scene/page-custom panel geometry.

The earlier layout made every panel a full-width horizontal band, because the
16:9 source composites clipped in any non-band slot. Now that character beats are
regenerated as bespoke panel-native art, that art can be *generated to its slot's
aspect*, so pages can carry genuine variety again: side-by-side pairs, asymmetric
widths, and taller feature bands, instead of one uniform stack.

This module decides, per page, an ordered list of pixel rects that preserves
reading order (rows top-to-bottom, left-to-right within a row). It is fully
deterministic (no RNG) so the generator and the assembler agree on every panel's
final shape.

Panel kinds:
  * flex  -- a close/medium character beat with recipe characters. Regenerated as
             bespoke art, so it may take ANY aspect (a tall 2-up cell, a feature
             band, etc.).
  * wide  -- everything else (establishing / wide / zero-character). Sourced from
             the 16:9 composite, so it must stay a full-width band (cover-crop
             then only trims sky, never the sides).

Only two SOLO flex panels in a row pair into a 2-up; a multi-character flex beat
keeps a full-width feature band so its cast has room to stage.
"""
from __future__ import annotations

import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
SCRIPTS = FACTORY / "00_SYSTEM" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assemble_pages as ap  # noqa: E402

PAGE_W, PAGE_H = ap.PAGE_W, ap.PAGE_H
MARGIN, GUTTER = ap.MARGIN, ap.GUTTER
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN - 90

# Char ids that have a bespoke art recipe (the six leads + Clever). A close/medium
# beat with only these characters is a flex panel; anything else stays a band.
RECIPE_IDS = {"MZ-CHAR-001", "MZ-CHAR-002", "MZ-CHAR-003", "MZ-CHAR-004",
              "MZ-CHAR-005", "MZ-CHAR-006", "MZ-CHAR-CLEVER"}


def _chars(panel: dict) -> list:
    return panel.get("characters") or []


def is_flex(panel: dict) -> bool:
    """A close/medium character beat with recipe characters -> bespoke art that
    can be generated to any slot aspect."""
    cs = _chars(panel)
    return (bool(cs) and panel.get("shot") in ("close", "medium")
            and all(c in RECIPE_IDS for c in cs))


def _wants_full(panel: dict) -> bool:
    """Panels that need a full-width row: a wide/establishing shot, a zero-char
    establishing plate, or a 3+ character staged beat (no room in a half cell)."""
    cs = _chars(panel)
    return panel.get("shot") == "wide" or len(cs) == 0 or len(cs) >= 3


def _pairable(panel: dict) -> bool:
    """Can share a 2-up row. Only bespoke (flex) close/medium beats pair: they are
    regenerated to fit any cell aspect, so a taller/narrower half cell is safe. A
    16:9 KEEP panel is always wide/establishing (`_wants_full`) and stays a full
    band, so no source composite is ever asked to fit a non-landscape cell."""
    return is_flex(panel) and not _wants_full(panel)


def _rows(panels: list[dict]) -> list[list[int]]:
    """Greedy order-preserving row packing: pair two consecutive pairable beats
    into a 2-up, otherwise the panel takes its own full-width row."""
    rows, i, n = [], 0, len(panels)
    while i < n:
        if _pairable(panels[i]) and i + 1 < n and _pairable(panels[i + 1]):
            rows.append([i, i + 1]); i += 2
        else:
            rows.append([i]); i += 1
    return rows


def _feature_row(panels: list[dict], rows: list[list[int]]) -> int:
    """Index of the one single-panel row to enlarge into the page's feature beat:
    prefer a wide establishing shot, then a close-up, then the first single row.
    -1 if the page is all pair rows (variety then comes from row-height jitter)."""
    singles = [r for r, row in enumerate(rows) if len(row) == 1]
    if not singles:
        return -1
    for want in ("wide", "close"):
        for r in singles:
            if panels[rows[r][0]].get("shot") == want:
                return r
    return singles[0]


def _weights(panels: list[dict], rows: list[list[int]], page_number: int) -> list[float]:
    """Row heights with a real hierarchy (one big feature beat + varied smaller
    rows) instead of near-identical bands. Deterministic jitter differentiates
    adjacent rows so no two neighbours share a height."""
    feat = _feature_row(panels, rows)
    base = {"wide": 1.15, "close": 1.05, "medium": 0.92}
    w = []
    for r, row in enumerate(rows):
        if r == feat:
            w.append(1.80); continue                     # the page's feature panel
        if len(row) == 2:
            val = 0.92                                    # pair rows (bespoke, fit any aspect)
        else:
            p = row[0]
            val = base.get(panels[p].get("shot"), 1.0)
            nc = len(_chars(panels[p]))
            val *= 1.12 if nc >= 3 else 1.06 if nc >= 2 else 1.0   # crowd needs vertical room
        val *= 1.0 + 0.08 * (((page_number * 5 + r) % 3) - 1)      # +/-8% gentle jitter
        w.append(max(0.62, val))
    return w


def _split(page_number: int, r: int) -> list[tuple[float, float]]:
    """Deterministic 2-up width split (x, w) in [0,1] -- alternates symmetric and
    asymmetric so pairs vary in width, not just height."""
    return [[(0.0, 0.5), (0.5, 0.5)],
            [(0.0, 0.58), (0.58, 0.42)],
            [(0.0, 0.42), (0.42, 0.58)]][(page_number * 3 + r) % 3]


# A 2-up cell must stay LANDSCAPE: two characters are staged side by side, so the
# cell needs width, not height. Cap a pair row's height so even the narrower split
# cell (~0.42 of the content width) keeps a landscape ratio; hand the freed height
# to the single/feature rows (which absorb it as bigger establishing/feature beats).
_NARROW = 0.42 * CONTENT_W                              # narrower split-cell width
PAIR_CELL_MIN_RATIO = 1.35
PAIR_ROW_MAX_H = _NARROW / PAIR_CELL_MIN_RATIO          # landscape target
PAIR_ROW_SQUARE_H = _NARROW                             # never taller than square (ratio 1.0)


def _row_heights(panels: list[dict], rows: list[list[int]], page_number: int) -> list[float]:
    weights = _weights(panels, rows, page_number)
    total = sum(weights) or 1.0
    h = [CONTENT_H * w / total for w in weights]
    pair_rows = [r for r, row in enumerate(rows) if len(row) == 2]
    singles = [r for r, row in enumerate(rows) if len(row) == 1]
    # cap pair rows to stay landscape; collect the freed height
    freed = 0.0
    for r in pair_rows:
        if h[r] > PAIR_ROW_MAX_H:
            freed += h[r] - PAIR_ROW_MAX_H
            h[r] = PAIR_ROW_MAX_H
    # single/feature rows absorb the freed height first (bigger establishing beats)
    sw = sum(weights[r] for r in singles)
    if freed > 0 and sw > 0:
        for r in singles:
            h[r] += freed * weights[r] / sw
        freed = 0.0
    # on an all-pair page there is nothing to absorb it, so grow the pair cells back
    # toward SQUARE (never portrait) to fill the page; any remainder becomes even
    # vertical gaps (handled by the caller) instead of a blank strip at the bottom.
    if freed > 0 and pair_rows:
        room = sum(PAIR_ROW_SQUARE_H - h[r] for r in pair_rows)
        add = min(freed, room)
        if room > 0:
            for r in pair_rows:
                h[r] += (PAIR_ROW_SQUARE_H - h[r]) / room * add
    return h                                            # may sum < CONTENT_H -> caller centres with gaps


def synth_page_rects(panels: list[dict], page_number: int) -> list[tuple[int, int, int, int]]:
    """Ordered pixel (x, y, w, h) per panel. Deterministic; reading-order safe."""
    n = len(panels)
    if n == 1:                                           # splash / single
        return [(MARGIN, MARGIN, CONTENT_W, CONTENT_H)]
    rows = _rows(panels)
    heights = _row_heights(panels, rows, page_number)
    # any height the rows could not use (a sparse all-pair page) becomes EVEN vertical
    # gaps around/between the rows, so the page reads centred with breathing room
    # instead of a blank strip at the bottom.
    gap = max(0.0, CONTENT_H - sum(heights)) / (len(rows) + 1)
    rects: list[tuple[int, int, int, int] | None] = [None] * n
    y = float(MARGIN) + gap
    for r, row in enumerate(rows):
        rh = heights[r]
        xs = [(0.0, 1.0)] if len(row) == 1 else _split(page_number, r)
        for (nx, nw), idx in zip(xs, row):
            x = MARGIN + nx * CONTENT_W
            w = nw * CONTENT_W
            ix = x + (GUTTER / 2 if nx > 0.001 else 0)
            iw = w - (GUTTER / 2 if nx > 0.001 else 0) - (GUTTER / 2 if nx + nw < 0.999 else 0)
            iy = y + (GUTTER / 2 if r > 0 else 0)
            ih = rh - (GUTTER / 2 if r > 0 else 0) - (GUTTER / 2 if r < len(rows) - 1 else 0)
            rects[idx] = (int(ix), int(iy), int(iw), int(ih))
        y += rh + gap
    return [rc for rc in rects if rc is not None]


def slot_band_px(rect: tuple[int, int, int, int], long_edge: int = 1280) -> tuple[int, int]:
    """Composite resolution for a slot: preserve the slot aspect, cap the long edge
    (the assembler upsamples to the real slot size, as before)."""
    _, _, w, h = rect
    if w >= h:
        bw, bh = long_edge, max(2, round(long_edge * h / w))
    else:
        bw, bh = max(2, round(long_edge * w / h)), long_edge
    return (bw - bw % 2, bh - bh % 2)
