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
| 24-cell  | 24       | 96    | 16    | 6             | 6          | Implemented |
| 600-cell | 120      | 720   | 72    | 10            | 10         | Implemented |

- Each polytope is defined as a data object (see Polytope Data Format below). Adding a new polytope = adding a new data file.

### Ring Coloring
- Each ring is assigned a **color** for its ON state. OFF-state rings are always medium gray (#888888, 70% opacity).
- **16-cell**: each ring gets a unique color (one color per ring, 6 colors for 6 rings).
- **24-cell and 600-cell**: rings are grouped into **Hopf fibration bundles** via quaternion quotients — rings in the same bundle share a color. The `bundle` field in the polytope data encodes this grouping.
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
- **Geometry pooling**: vertex spheres and edge tubes are allocated once into pools and reused across rebuilds by updating buffer attributes in-place. This avoids GPU memory leaks on Safari/iOS where `BufferGeometry.dispose()` doesn't reliably free resources.
- 4D rotation events are coalesced via a dirty flag and processed once per animation frame.

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
2. **Scramble**: iterate through every vertex, clicking each with 50% probability. Retry if result is all-ON or all-OFF. Enters **challenge mode**.
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
- In **challenge mode**, Reset requires confirmation: first click changes button to "Sure?" (muted gold text and border); a second click within 3 seconds confirms. Reverts after 3 seconds if unconfirmed.
- Outside challenge mode, Reset works immediately with one click.
- Sets all rings to OFF, resets move counter to 0, background turns blue.

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
- `rings[].bundle`: color group index. 16-cell: unique per ring. 24-cell/600-cell: Hopf fibration bundle.
- `bundleColors`: hex colors for ON-state rings.
- To add a new polytope: create a new data object in the same format with vertex coordinates, ring membership, and bundle assignments.

### Polytope Data Generation Procedure

The following algorithm generates ring and bundle data from vertex coordinates. It applies to any regular 4D polytope whose edges form great-circle rings on S³.

**Input**: vertex coordinates on the unit 3-sphere S³.

**Step 1 — Edge discovery**:
1. Pick any vertex V₀. Compute the inner product of V₀ with every other vertex. The largest inner product (excluding self, which is 1) is the edge threshold `max_ip`.
2. Enumerate all unordered pairs of vertices. A pair (Vᵢ, Vⱼ) is an edge if `dot(Vᵢ, Vⱼ) ≈ max_ip` (within floating-point tolerance).
3. Store edges as a set of unordered index pairs.

**Step 2 — Ring tracing via reflection**:
1. Maintain a set of unused edges. Pick any unused edge (A, B) to start a new ring.
2. Compute the next vertex by reflecting A through B's axis on S³:
   - `projection = B × dot(A, B) / dot(B, B)`
   - `reflected = 2 × projection − A`
   - Match `reflected` to the nearest vertex index (within tolerance).
3. The next edge is (B, reflected). Mark edge (A, B) as used. Advance: A ← B, B ← reflected.
4. Repeat until returning to the starting edge. Record the ordered vertex sequence as one ring.
5. Repeat from step 1 until all edges are consumed.
6. **Validation**: confirm the expected ring count (e.g., 16 for 24-cell, 72 for 600-cell) and that each ring has the expected vertex count (6 for 24-cell, 10 for 600-cell).

**Step 3 — Bundle assignment (Hopf fibration, for 24-cell and 600-cell)**:
1. For each ring, take the first edge (v1, v2) and treat each vertex as a quaternion [x, y, z, w].
2. Compute the quotient q1 × q2⁻¹ and normalize it.
3. Canonicalize by rounding components (6 decimals), eliminating negative zeros, and making the first nonzero component positive.
4. Group rings whose canonical quotients form inverse pairs (q and q⁻¹) — these belong to the same bundle.
5. **Validation**: confirm all bundles have equal size (e.g., 4 bundles × 4 rings for 24-cell, 6 bundles × 12 rings for 600-cell) and that rings within each bundle are fully vertex-disjoint.

**16-cell**: uses one bundle per ring (6 bundles of 1 ring each) for maximum color variety.

---

## UI

### Layout
- Full-viewport canvas.
- Minimal overlay (top-right corner):
  - Move counter
  - "Scramble" button
  - "Reset" button
  - "+" / "−" zoom buttons
  - Polytope selector (dropdown: 16-cell, 24-cell, 600-cell)
- Win overlay: centered translucent text over the scene.

### Responsive
- Canvas resizes with window.
- Works in portrait and landscape on mobile.
- All buttons ≥ 44×44px touch targets.
- Responsive font sizes via `clamp()`.

### Debug Overlay
- Hidden by default. Activated by adding `?debug` to the URL.
- Shows Three.js geometry count, texture count, triangle count, and draw calls.
- Also catches and displays uncaught JS errors and unhandled promise rejections.

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

