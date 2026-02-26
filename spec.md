# Lights Out 4D — Game Spec

## Concept
A browser-based puzzle game inspired by the classic "Lights Out," played on the structure of a **4D polytope**. The polytope is visualized via **stereographic projection** into 3D, rendered with Three.js (WebGL). Vertices appear as spheres, edges as circular arcs forming rings. Players click vertices to toggle the rings passing through them. The goal is to turn all rings OFF.

**Live**: https://nanma80.github.io/lights_out_4d

---

## Geometry

### The Polytope
- The game supports multiple **4D regular polytopes** as difficulty levels. All polytope vertices lie on the unit 3-sphere S³.
- Each polytope's edges lie along **great circles** of S³. Multiple edges concatenate to form closed **rings**. These rings are the core game objects.
- Supported polytopes (in order of complexity):

| Polytope | Vertices | Edges | Rings | Vertices/Ring | Edges/Ring | Status      |
|----------|----------|-------|-------|---------------|------------|-------------|
| 16-cell  | 8        | 24    | 6     | 4             | 4          | Implemented |
| 24-cell  | 24       | 96    | 16    | 6             | 6          | Future      |
| 600-cell | 120      | 720   | 72    | 10            | 10         | Future      |

- Each polytope is defined as a data object (see Polytope Data Format below). Adding a new polytope = adding a new data file.

### Ring Coloring
- Each ring is assigned a **color** for its ON state. OFF-state rings are always medium gray (#888888, 70% opacity).
- v1: each ring gets a **distinct color** from a palette of 6 vibrant hues.
- Future: rings will be grouped by **Hopf fibration** bundles — rings in the same bundle share a color. The `bundle` field in the polytope data supports this.
- Color palette: `["#ff3366", "#33ff66", "#3366ff", "#ffcc00", "#ff6633", "#cc33ff"]`.

### Stereographic Projection (4D → 3D)
- Project from the **south pole** (0, 0, 0, −1) onto the equatorial hyperplane w = 0:
  - Given a point (x, y, z, w) on S³: `X = x / (1 + w)`, `Y = y / (1 + w)`, `Z = z / (1 + w)`.
- **Key property**: great circles on S³ project to circles (or straight lines) in R³.
- Edges are drawn by sampling points along the great-circle arc on S³, projecting each to R³, and rendering as a tube (`THREE.TubeGeometry` along a `CatmullRomCurve3`).

### 4D Rotation
- Driven by **scroll wheel / two-finger pinch** (see Interaction section).
- Rotates in the plane spanned by the **current 3D camera view direction** and the **W axis**. Decomposed into weighted XW, YW, ZW rotations.
- Applied to 4D vertex coordinates before projection. Scene geometry is fully rebuilt after rotation.
- Initial 4D viewpoint: small rotations in XW (0.4), YW (0.3), ZW (0.2), XY (0.15) to break symmetry and avoid degenerate projections.
- No auto-rotation.

---

## Rendering

### Technology
- Plain HTML/CSS/JS — no UI frameworks, no build step.
- **Three.js v0.160.0** loaded from CDN (`unpkg.com`).
- Viewport meta tag with `user-scalable=no`.
- `renderer.setPixelRatio(devicePixelRatio)` for crisp rendering on high-DPI screens.

### Visual Style
- **Reference**: [Wikipedia 16-cell stereographic projection](https://commons.wikimedia.org/wiki/File:Stereographic_polytope_16cell_colour.png).
- Background: very dark (#0a0a0a), changes on win states (see Win Condition).
- **Vertices**: `SphereGeometry` (radius 0.12), white with subtle emissive glow. Pointer cursor on canvas.
- **Rings ON**: colored tube geometry with emissive glow (emissiveIntensity 0.5). Full opacity.
- **Rings OFF**: gray (#888888) tube geometry, 70% opacity, no emissive.
- **Lighting**: ambient (0.6) + directional (0.8) from (5, 5, 5).
- Edges rendered as 48-segment arcs with tube radius 0.03.

### 3D Camera
- `THREE.PerspectiveCamera` (FOV 50).
- Custom **trackball** implementation — quaternion-based, no gimbal lock.
  - Rotation uses screen-space axis decomposition: horizontal drag rotates around camera's up vector, vertical drag rotates around camera's right vector.
  - Uniform and smooth in all directions — no equator/pole artifacts.
- Zoom via **UI buttons only** (not scroll — scroll is 4D rotation).
- Initial 3D camera: offset by Euler(π/6, π/5, 0) so no vertex sits at screen center.
- Camera distance range: 2–20, default 5.
- No auto-rotation.

---

## Interaction

### Controls Summary
| Input | Action |
|-------|--------|
| Mouse drag / single-finger swipe | 3D camera orbit (trackball) |
| Mouse scroll / two-finger pinch | 4D rotation |
| Click / tap vertex | Toggle rings through that vertex |
| + / − buttons | Zoom in/out |
| Scramble button | Randomize ring states |
| Reset button | All rings OFF |

### Implementation Details
- Click vs drag threshold: < 5px total movement = click.
- Mouse: `mousedown`/`mousemove`/`mouseup`/`wheel` events.
- Touch: `touchstart`/`touchmove`/`touchend`. CSS `touch-action: none` on html/body/canvas to prevent browser gesture interference.
- Pinch detection: track distance between two touch points.
- **Pinch → single-finger transition**: trackball is disabled during pinch and reset when transitioning to single finger to prevent viewport jumps.
- **Click debouncing**: 100ms debounce to prevent double-fire on Windows touchscreens (which emit both touch and mouse events).
- Hit testing: `THREE.Raycaster` against vertex sphere meshes, pick closest intersection.

---

## Game State

### Rings and Spheres
- **Game state lives on the rings.** Each ring is ON or OFF (boolean array).
- **Clicking a vertex** toggles all rings passing through it.
- **Vertices** have no state — they are click targets only.
- Vertex-to-ring mapping computed at startup from polytope data.

### 16-cell Details
- 6 rings (one per coordinate plane: XY, XZ, XW, YZ, YW, ZW).
- Each vertex is on 3 rings → clicking toggles 3 rings.
- 6 binary states, 8 possible moves.

| Ring | Plane | Vertices |
|------|-------|----------|
| 0 | XY | +X, +Y, −X, −Y |
| 1 | XZ | +X, +Z, −X, −Z |
| 2 | XW | +X, +W, −X, −W |
| 3 | YZ | +Y, +Z, −Y, −Z |
| 4 | YW | +Y, +W, −Y, −W |
| 5 | ZW | +Z, +W, −Z, −W |

---

## Puzzle Logic

### Flow
1. Start: all rings OFF (solved state, blue background). Auto-scramble on first load.
2. **Scramble**: simulate N random vertex clicks (N=4 for 16-cell). Ensure at least one ring is ON. Enters **challenge mode**.
3. Player clicks vertices to toggle rings.
4. **Win** when all rings are OFF (primary) or all ON (secondary). Win popup shows **only once** per scramble.
5. After winning, the player can continue clicking (exploration) but no further win popups until next scramble.

### Game Modes
- **Challenge mode** (`isChallenge = true`): active after Scramble. Win detection is enabled. Win popup shows once (`hasWon` flag).
- **Exploration mode** (`isChallenge = false`): active after Reset or after a win is dismissed. Player can freely toggle rings. No win popup. Move counter still tracks clicks.
- Scramble resets both `isChallenge = true` and `hasWon = false`.

### Win Condition
- **All OFF**: scene background → deep blue (#0a0a3a). Overlay: "Lights Out! 🎉" + move count.
- **All ON**: scene background → warm amber (#3a2a0a). Overlay: "All Lit Up! ✨ Now try turning them all off!" + move count.
- Background color syncs with ring state at all times (not just on win).
- Overlay is translucent, non-blocking. Dismiss by tapping anywhere or pressing Scramble.

### Reset
- Sets all rings to OFF, resets move counter to 0, background turns blue.
- Reinforces that all-OFF is the target state.

---

## Polytope Data Format

```js
const POLYTOPE_16CELL = {
  name: "16-cell",
  vertices: [
    [1,0,0,0], [-1,0,0,0],   // 0,1: ±X
    [0,1,0,0], [0,-1,0,0],   // 2,3: ±Y
    [0,0,1,0], [0,0,-1,0],   // 4,5: ±Z
    [0,0,0,1], [0,0,0,-1],   // 6,7: ±W
  ],
  rings: [
    { vertices: [0, 2, 1, 3], bundle: 0 },  // XY plane
    { vertices: [0, 4, 1, 5], bundle: 1 },  // XZ plane
    { vertices: [0, 6, 1, 7], bundle: 2 },  // XW plane
    { vertices: [2, 4, 3, 5], bundle: 3 },  // YZ plane
    { vertices: [2, 6, 3, 7], bundle: 4 },  // YW plane
    { vertices: [4, 6, 5, 7], bundle: 5 },  // ZW plane
  ],
  bundleColors: ["#ff3366", "#33ff66", "#3366ff", "#ffcc00", "#ff6633", "#cc33ff"],
};
```

- `vertices`: 4D coords on unit S³.
- `rings[].vertices`: ordered vertex indices forming a great circle. Consecutive pairs + wrap = edges.
- `rings[].bundle`: color group index. v1 uses unique per ring; future Hopf fibration grouping.
- `bundleColors`: hex colors for ON-state rings.
- To add a new polytope: create a new data object in the same format with vertex coordinates, ring membership, and bundle assignments.
- 24-cell and 600-cell vertex coordinates are standard. Ring membership and Hopf bundle assignments to be computed via Mathematica.

---

## UI

### Layout
- Full-viewport canvas.
- Minimal overlay (top-right corner):
  - Move counter
  - "Scramble" button
  - "Reset" button
  - "+" / "−" zoom buttons
  - Polytope selector (future — only 16-cell in v1)
- Win overlay: centered translucent text over the scene.

### Responsive
- Canvas resizes with window.
- Works in portrait and landscape on mobile.
- All buttons ≥ 44×44px touch targets.
- Responsive font sizes via `clamp()`.

---

## File Structure
```
index.html              ← entry point
css/
  style.css             ← UI overlay styles
src/
  main.js               ← bootstrap, wires everything together
  polytopes.js          ← polytope data (16-cell)
  math4d.js             ← 4D rotation, stereographic projection, great circle arcs
  rendering.js          ← Three.js scene, ring tubes, vertex spheres
  controls.js           ← trackball camera, 4D rotation controller, raycaster
  game.js               ← game state, toggle, scramble, reset, win detection
spec.md                 ← this file
.github/
  copilot-instructions.md
```

---

## Deployment
- Hosted as a **static site on GitHub Pages** from `main` branch root.
- No backend, no server-side logic.
- Three.js loaded from CDN (unpkg.com). No node_modules or build step.
- Repo: https://github.com/nanma80/lights_out_4d

---

## Out of Scope (v1)
- Saving game state (no localStorage).
- Sound effects.
- Undo button.
- Solving hints.
- Bloom/post-processing effects.
