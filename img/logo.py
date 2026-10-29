#!/usr/bin/env python3
"""logo.py -- write logo.svg, the FPTalks logo, from its geometry.

The logo is a target turned in space: four concentric rings, squashed
and tilted, on a stand, with three arrows in it. Its numbers live
below; edit them here, not in the SVG, then rebuild the SVG and the
PNG the pages show (rsvg-convert is librsvg's renderer):

    python3 img/logo.py
    rsvg-convert -w 400 -h 400 img/logo.svg -o img/logo.png

The SVG is drawn in a 400x400 box, every shape an untransformed path:
SVG lays a mask out in the turned coordinates of a transformed element,
so a transform would knock the masks out of line.
"""
import math
import os

Point = tuple[float, float]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GREEN = "#008f00"
DARK  = "#006100"

# The rings: ring k (1..4) is an ellipse k times RX by RY around CX, CY,
# tilted TILT degrees; even-odd fill leaves the gaps between them clear.
CX, CY = 171.0, 197.05
RX, RY = 48.9, 24.8
TILT   = 76.4

# The target's depth: its back face is the front moved by this much.
DEPTH = (-9.1, 0.3)

# The stand: a bar going up from its bottom-left corner, its bottom edge
# BAR_W long at BAR_ANGLE degrees, the two bottom corners rounded.
BAR_X, BAR_Y = 47.75, 369.9
BAR_W        = 64.25
BAR_ANGLE    = 20.6
BAR_LEN      = 160.0
BAR_R        = 6.0

# The arrows, each from its tip to its tail; all share one shape: the
# shaft's width, the head's length and half-width, and the notch in
# the back of the head.
ARROWS = [
    ((130.75, 80.0), (310.0, 31.75)),
    ((158.4, 189.6), (297.1, 51.0)),
    ((161.8, 197.85), (371.6, 264.9)),
]
SHAFT_W  = 11.0
HEAD_LEN = 21.25
HEAD_HW  = 10.9
NOTCH    = 3.75

# The clear gap cut around each arrow, past its edge.
GAP = 8.85


def fmt(v: float) -> str:
    """A coordinate, to two places, without trailing zeros."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pt(p: Point) -> str:
    """A point as an SVG coordinate pair."""
    return f"{fmt(p[0])} {fmt(p[1])}"


def ring(k: int, shift: Point = (0, 0)) -> str:
    """Ring k's ellipse, moved by shift, as a closed path of two arcs."""
    rx, ry = RX * k, RY * k
    cx, cy = CX + shift[0], CY + shift[1]
    tilt   = math.radians(TILT)
    c, s   = math.cos(tilt), math.sin(tilt)
    a      = (cx + rx * c, cy + rx * s)
    b      = (cx - rx * c, cy - rx * s)
    arc    = f"A{fmt(rx)} {fmt(ry)} {fmt(TILT)} 1 1 "
    return f"M{pt(a)}{arc}{pt(b)}{arc}{pt(a)}Z"


def arrow(tip: Point, tail: Point) -> str:
    """The notched head and the shaft, as two closed paths."""
    length = math.hypot(tail[0] - tip[0], tail[1] - tip[1])
    ux, uy = (tail[0] - tip[0]) / length, (tail[1] - tip[1]) / length

    def at(along: float, across: float) -> Point:
        return (tip[0] + ux * along - uy * across,
                tip[1] + uy * along + ux * across)

    half  = SHAFT_W / 2
    head  = [at(0, 0), at(HEAD_LEN, HEAD_HW),
             at(HEAD_LEN - NOTCH, 0), at(HEAD_LEN, -HEAD_HW)]
    shaft = [at(HEAD_LEN / 2, half), at(length, half),
             at(length, -half), at(HEAD_LEN / 2, -half)]
    return " ".join("M" + "L".join(pt(q) for q in poly) + "Z"
                    for poly in (head, shaft))


def bar() -> tuple[tuple[Point, Point, Point, Point], Point, Point]:
    """The stand's corners (bottom-left, bottom-right, top-right,
    top-left), and its directions along the bottom and up."""
    a      = math.radians(BAR_ANGLE)
    bx, by = math.cos(a), math.sin(a)
    ux, uy = math.sin(a), -math.cos(a)
    c0     = (BAR_X, BAR_Y)
    c1     = (BAR_X + bx * BAR_W, BAR_Y + by * BAR_W)
    c2     = (c1[0] + ux * BAR_LEN, c1[1] + uy * BAR_LEN)
    c3     = (BAR_X + ux * BAR_LEN, BAR_Y + uy * BAR_LEN)
    return (c0, c1, c2, c3), (bx, by), (ux, uy)


def toward(p: Point, q: Point) -> Point:
    """The point BAR_R from p toward q: where a rounded corner starts."""
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    return (p[0] + (q[0] - p[0]) * BAR_R / d,
            p[1] + (q[1] - p[1]) * BAR_R / d)


def corner(p: Point) -> str:
    """A rounded corner of the stand, arcing on to p."""
    return f"A{fmt(BAR_R)} {fmt(BAR_R)} 0 0 0 {pt(p)}"


def stand() -> str:
    """The stand's face."""
    (c0, c1, c2, c3), _, _ = bar()
    return (f"M{pt(toward(c0, c3))}{corner(toward(c0, c1))}"
            f"L{pt(toward(c1, c0))}{corner(toward(c1, c2))}"
            f"L{pt(c2)}L{pt(c3)}Z")


def stand_side() -> str:
    """The stand swept back by DEPTH: its back copy's left and bottom,
    then its face's right and top, joined where the bottom-right corner
    turns parallel to the sweep."""
    (c0, c1, c2, c3), (bx, by), (ux, uy) = bar()

    dx, dy = DEPTH

    def back(p: Point) -> Point:
        return (p[0] + dx, p[1] + dy)

    # the bottom-right corner's point whose outward normal is square
    # to the sweep, on its downward side
    center = (c1[0] + (ux - bx) * BAR_R, c1[1] + (uy - by) * BAR_R)
    n      = math.hypot(dx, dy)
    nx, ny = dy / n, -dx / n
    if ny < 0:
        nx, ny = -nx, -ny
    turn = (center[0] + nx * BAR_R, center[1] + ny * BAR_R)
    return (f"M{pt(back(c3))}L{pt(back(toward(c0, c3)))}"
            f"{corner(back(toward(c0, c1)))}"
            f"L{pt(back(toward(c1, c0)))}{corner(back(turn))}"
            f"L{pt(turn)}{corner(toward(c1, c2))}"
            f"L{pt(c2)}L{pt(c3)}Z")


def svg() -> str:
    """The whole logo as SVG text."""
    arrows = " ".join(arrow(tip, tail) for tip, tail in ARROWS)
    rings  = " ".join(ring(k) for k in (4, 3, 2, 1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <title>FPTalks</title>
  <!-- generated by logo.py; edit the numbers there, not here -->
  <defs>
    <!-- a clear gap around each arrow: the arrows, stroked round -->
    <mask id="cut">
      <rect width="400" height="400" fill="#fff"/>
      <path d="{arrows}" fill="#000" stroke="#000"
            stroke-width="{fmt(2 * GAP)}" stroke-linejoin="round"/>
    </mask>
    <!-- hides what is behind the target where its rings leave gaps -->
    <mask id="behind">
      <rect width="400" height="400" fill="#fff"/>
      <path d="{ring(3)}" fill="#000"/>
    </mask>
  </defs>
  <g mask="url(#cut)">
    <g mask="url(#behind)">
      <!-- the stand: its side, then its face -->
      <path d="{stand_side()}" fill="{DARK}"/>
      <path d="{stand()}" fill="{GREEN}"/>
      <!-- the target's side: its back face -->
      <path d="{ring(4, DEPTH)}" fill="{DARK}"/>
    </g>
    <!-- the rings -->
    <path d="{rings}" fill="{GREEN}" fill-rule="evenodd"/>
  </g>
  <!-- the arrows: each a notched head and a shaft -->
  <path d="{arrows}" fill="{GREEN}"/>
</svg>
'''


def main() -> None:
    """Write logo.svg beside this script."""
    with open(os.path.join(SCRIPT_DIR, "logo.svg"), "w") as f:
        f.write(svg())


if __name__ == "__main__":
    main()
