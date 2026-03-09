# Lights Out 4D

The classic puzzle game, but on stereographic projections of 4D polytopes.

**Play it**: [nan.ma/lights_out_4d](https://www.nan.ma/lights_out_4d/)

Works on phone, tablet, or desktop — no install needed.

## How to Play

For each polytope, edges form great circles called **rings**. Click a vertex to toggle the state of the rings passing through it. The objective is to **turn off all rings**.

**Controls**:
- **3D viewpoint**: swipe (touch) or drag (mouse)
- **4D rotation**: pinch (touch) or scroll (mouse wheel)
- **Zoom**: use the +/− buttons

## Polytopes

| Polytope | Vertices | Rings | Difficulty |
|----------|----------|-------|------------|
| 16-cell  | 8        | 6     | Easy       |
| 24-cell  | 24       | 16    | Medium     |
| 600-cell | 120      | 72    | Hard       |
| Bicont   | 48       | 50    | Hard       |
| Bideca   | 10       | 10    | Easy       |
| {6}+{6}  | 12       | 11    | Medium     |
| {8}+{8}  | 16       | 18    | Easy       |
| {10}+{10}| 20       | 27    | Medium     |
| {12}+{12}| 24       | 38    | Medium     |

Bicont and bideca are the duals of the bitruncated 24-cell and bitruncated 5-cell, respectively. The {2n}+{2n} shapes are duals of {2n}×{2n} duoprisms.

## Motivation

Lights Out puzzles are much easier than twisty puzzles because the moves are commutative. That also means you can play with 4D shapes more casually, on a touch screen.

The motivation for Lights Out 4D came from the Mirror_Z puzzles in [MPUlt](https://superliminal.com/andrey/mpu/): 3^4, 24-cell, 120-cell, and 48-cell. In these puzzles, there's only one operation per cell: flipping it. The 2C pieces move in many orbits, each of which is a great circle. The parity analysis of these orbits is an interesting sub-puzzle that works just like Lights Out: flipping a cell changes the parity of all the great circles passing through it. Fixing the parity of all orbits is a necessary step toward solving all the 2C pieces.

When I solved these puzzles, I found this step particularly interesting, especially for the 120-cell and 48-cell Mirror_Z. However, not many people have had the chance to appreciate it — few have attempted the full puzzle. So for a long time, I wanted to extract this step into a standalone puzzle that more people could play on more platforms. Lights Out 4D is that idea realized.

## Tech

- Plain HTML/CSS/JS — no build step, no frameworks
- [Three.js](https://threejs.org/) for WebGL rendering
- Deployed to GitHub Pages

See [spec.md](spec.md) for detailed design documentation.

## Local Development

```sh
python -m http.server 8080
```

Then open http://localhost:8080.

## Author

Nan Ma · 2026
