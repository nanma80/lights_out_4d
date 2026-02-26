# Lights Out 4D — Game Spec

## Concept
A browser-based puzzle game inspired by the classic "Lights Out," played on the structure of a **4D polytope**. The polytope is visualized via **stereographic projection** into 3D, rendered with a WebGL 3D engine. Vertices appear as spheres, edges as circular arcs forming rings. Players click vertices to toggle the rings passing through them. The goal is to turn all rings OFF.

---

## Geometry

### The Polytope
- The game supports multiple **4D regular polytopes** as difficulty levels. All polytope vertices lie on the unit 3-sphere S³.
- Each polytope's edges lie along **great circles** of S³. Multiple edges concatenate to form closed **rings**. These rings are the core game objects.
- Supported polytopes (in order of complexity, v1 ships 16-cell only):

| Polytope | Vertices | Edges | Rings | Vertices/Ring | Edges/Ring | Status |
|----------|----------|-------|-------|---------------|------------|--------|
| 16-cell  | 8        | 24    | 6     | 4             | 4          | v1     |
| 24-cell  | 24       | 96    | 16    | 6             | 6          | Future |
| 600-cell | 120      | 720   | 72    | 10            | 10         | Future |

- The architecture should define a polytope as data: a list of 4D vertex coordinates + edge list. Rings, adjacency, and Hopf fibration grouping are derived or provided per polytope.

### Ring Coloring
- Each ring is assigned a **color** for its ON state. OFF-state rings are always gray.
- v1: assign each ring a **distinct color** from a palette of 6–8 vibrant hues. No Hopf fibration grouping needed yet.
- Future: rings will be grouped by **Hopf fibration** bundles — rings in the same bundle share a color. The `bundle` field in the polytope data supports this. For now, each ring can use its own index as its bundle (i.e., unique colors).
- Color palette example: `["#ff3366", "#33ff66", "#3366ff", "#ffcc00", "#ff6633", "#cc33ff"]`.

### Stereographic Projection (4D → 3D)
- All polytope vertices lie on S³ (the unit 3-sphere in R⁴).
- Project from the **south pole** (0, 0, 0, −1) onto the equatorial hyperplane w = 0:
  - Given a point (x, y, z, w) on S³: `X = x / (1 + w)`, `Y = y / (1 + w)`, `Z = z / (1 + w)`.
- **Key property**: great circles on S³ project to circles (or straight lines) in R³.
  - Edges of the 16-cell that lie along a great circle of S³ project to **circular arcs** in 3D.
  - When multiple edges share a great circle, they form a complete **ring** (circle) in the projection.

### Edge Rendering as Arcs
- Each edge connects two vertices on S³. The geodesic between them (a great-circle arc on S³) projects to a **circular arc** in R³ under stereographic projection.
- To draw each edge:
  1. Compute the great circle on S³ containing both endpoints.
  2. Stereographically project several sample points along the arc to get a 3D circular arc.
  3. Render as a tube/curve in 3D (e.g., `THREE.TubeGeometry` along the arc).
- Alternatively, compute the projected circle analytically (center + radius + plane in R³) and render an arc of that circle between the two projected endpoints.

### 4D Rotation
- The polytope can be rotated in 4D before projection using rotation matrices in the 6 rotation planes: XY, XZ, XW, YZ, YW, ZW.
- The 4D rotation is driven by the scroll/pinch interaction (see Interaction section). The rotation plane is determined by the current 3D camera view direction combined with the W axis.
- The rotation is applied to the 4D vertex coordinates, then re-projected stereographically and the 3D scene geometry is rebuilt.
- No auto-rotation — the 4D viewpoint stays fixed until the player explicitly scrolls/pinches.

---

## Rendering

### Technology
- Plain HTML/CSS/JS — no UI frameworks, no build step.
- Single or multiple files — whichever is cleaner for the implementation.
- **Three.js** for 3D rendering (load from CDN, e.g., `https://unpkg.com/three@<version>/build/three.module.js`).
- Include viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">`.
- Three.js WebGLRenderer handles devicePixelRatio automatically via `renderer.setPixelRatio(devicePixelRatio)`.

### Visual Style
- **Reference**: the stereographic projection style from Wikipedia's 16-cell article ([Stereographic_polytope_16cell_colour.png](https://commons.wikimedia.org/wiki/File:Stereographic_polytope_16cell_colour.png)) — smooth colored rings as 3D circles, small spheres at vertices, dark background.
- Background: black or very dark (#0a0a0a).
- **Vertices**: rendered as `THREE.SphereGeometry` meshes. Small, neutral color (white or light gray). Always visible.
- **Rings (ON state)**: rendered as glowing colored tubes — like glowsticks. Color determined by Hopf fibration bundle. Smooth, continuous circles in 3D (not segmented edges).
- **Rings (OFF state)**: rendered as dark gray tubes, subtle/muted, semi-transparent.
- **Lighting**: ambient light + one or two point/directional lights for depth cues on spheres.
- Optional: post-processing bloom pass (via Three.js `UnrealBloomPass`) for glowing ON rings.

### 3D Camera
- Use `THREE.PerspectiveCamera`.
- **No gimbal lock**: camera rotation must use quaternion-based or trackball-style controls — no Euler angle orbit that snaps or locks at poles.
- Rotation should feel **uniform and smooth** in all directions — no detectable equator, no north/south pole behavior. The user should be able to drag continuously in any direction without resistance or discontinuity.
- Recommended: custom trackball implementation or `THREE.TrackballControls` with **zoom disabled** (zoom is handled by UI buttons, scroll is reserved for 4D rotation).
- The **4D rotation** (see Geometry section) is separate from 3D camera movement.
- Default camera position: looking at the origin from a distance that frames the full projected polytope.
- No auto-rotation. The view stays exactly where the player leaves it.

---

## Interaction

### Mouse / Touch
Two types of viewpoint changes:

1. **3D Camera Orbit** (standard 3D navigation):
   - **Mouse drag** or **single-finger swipe** on touch screen.
   - Rotates the 3D camera around the scene using trackball-style controls (quaternion-based, no gimbal lock).
   - **Zoom is NOT on scroll/pinch** — scroll and pinch are reserved for 4D rotation (see below).
   - Zoom is controlled via **"+" and "−" buttons** in the UI overlay. Moves the camera closer/farther from the origin.

2. **4D Rotation**:
   - **Mouse scroll wheel** (up/down) or **two-finger pinch** on touch screen.
   - Rotates the polytope in 4D so that the origin of the 3D view rotates towards/away from the viewer.
   - Implementation: rotate in the plane spanned by the **current 3D camera view direction** and the **W axis**. This means the 4D rotation axis adapts to where the camera is looking.
   - Scroll up / pinch out → rotate one direction; scroll down / pinch in → rotate the other.
   - After rotation, re-project all 4D vertices via stereographic projection and rebuild the 3D geometry.

These two controls together provide full navigation of the 4D viewpoint.

- Distinguish click vs drag by movement threshold (< 5px = click).
- Handle both mouse events (`mousedown`/`mousemove`/`mouseup`/`wheel`) and touch events (`touchstart`/`touchmove`/`touchend` with gesture detection).
- On touch, call `preventDefault()` to suppress browser scroll, zoom, and long-press menus during interaction with the canvas.
- Detect pinch gesture by tracking distance between two touch points across `touchmove` events.

### Vertex Adjacency (16-cell)
- Two vertices are adjacent if they are connected by an edge in the polytope.
- On the 16-cell, each vertex is adjacent to 6 other vertices (all except its antipodal vertex).
- Precompute the adjacency list for all 8 vertices at startup.

### Hit Testing
- Use Three.js `Raycaster` to detect clicks on vertex sphere meshes.
- On click, cast a ray from the camera through the click point; intersect with all vertex spheres.
- Pick the closest intersected sphere.

### Game State — Rings and Spheres
- Each polytope's edges form a set of **rings** (great circles on S³).
- **Game state lives on the rings.** Each ring is either ON or OFF.
  - ON ring: rendered as a glowing tube in its **Hopf bundle color**.
  - OFF ring: rendered as a dark gray tube, subtle/muted.
- **Clicking a vertex (sphere)** toggles the ON/OFF state of all rings passing through that vertex.
- **Vertices (spheres)** are always visible but carry no ON/OFF state themselves. They are interactive targets only.

### Polytope Data Format
Each polytope is defined as a data object with the following structure:
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
    { vertices: [2, 4, 3, 5], bundle: 2 },  // YZ plane
    { vertices: [2, 6, 3, 7], bundle: 1 },  // YW plane
    { vertices: [4, 6, 5, 7], bundle: 0 },  // ZW plane
  ],
  bundleColors: ["#ff3366", "#33ff66", "#3366ff"],
};
```

- `vertices`: array of 4D coordinates (on unit S³).
- `rings`: array of ring objects. Each ring has:
  - `vertices`: ordered list of vertex indices forming the great circle cycle. Consecutive pairs (+ last→first) define edges.
  - `bundle`: index into `bundleColors` for Hopf fibration color grouping.
- `bundleColors`: array of hex colors for ON-state rings in each bundle.
- Edges are **not listed separately** — derived from ring vertex order.
- Vertex-to-ring mapping (which rings a vertex belongs to) is computed at startup from the ring data.

### Polytopes Included in v1
- **16-cell** only (data above). Ring and bundle assignments are known.
- 24-cell and 600-cell deferred to future iterations. Their vertex coordinates are standard; ring membership and Hopf bundle assignments will be computed separately (e.g., via Mathematica) and added in the same data format.

### 16-cell Rings (Starter Polytope)
With vertices at (±1,0,0,0), (0,±1,0,0), (0,0,±1,0), (0,0,0,±1):
| Ring | Plane | Vertices (indices) |
|------|-------|--------------------|
| 1 | XY | +X, +Y, −X, −Y |
| 2 | XZ | +X, +Z, −X, −Z |
| 3 | XW | +X, +W, −X, −W |
| 4 | YZ | +Y, +Z, −Y, −Z |
| 5 | YW | +Y, +W, −Y, −W |
| 6 | ZW | +Z, +W, −Z, −W |

Each vertex is on 3 rings. Clicking a vertex toggles 3 rings. 6 binary states, 8 possible moves.

---

## Puzzle Logic

### Initial State
- **New Game**: start from the solved state where **all rings are OFF**.
- The program then **simulates N random vertex clicks** to scramble the rings into a random ON/OFF state. This guarantees the puzzle is always solvable (every scramble can be reversed).
- The scramble clicks are animated or happen instantly (TBD), then the player takes over.
- Difficulty scales with the polytope:
  - 16-cell (6 rings): ~3–4 random clicks.
  - 24-cell (16 rings): ~6–8 random clicks.
  - 600-cell (72 rings): ~15–20 random clicks.

### Win Condition
- **Primary win (All OFF)**: all rings are gray → background briefly pulses to a deep blue (#0a0a3a), then a centered message fades in: "Lights Out! 🎉" with move count.
- **Secondary win (All ON)**: all rings are lit → background briefly pulses to a warm amber (#3a2a0a), then a centered message fades in: "All Lit Up! ✨ Now try turning them all off!" with move count.
- Both celebrations:
  - Background color shift is subtle and temporary (fades back after a few seconds or stays until dismissed).
  - Message overlay is minimal — translucent, centered text over the scene (not a blocking modal). The polytope remains visible behind it.
  - Show "Scramble" button to play again.
  - The player can dismiss the message by tapping anywhere or clicking the Scramble button.

### Polytope Selector
- A dropdown or button group to switch between polytopes.
- v1: only 16-cell available. UI element present but other options disabled/hidden until data is added.
- Switching polytopes starts a new game with the selected polytope.

### Move Counter
- Display current move count in the corner.

---

## UI

### Layout
- Full-viewport canvas.
- Minimal overlay (top-right corner):
  - Move counter
  - "Scramble" button — applies random vertex clicks to scramble the rings from current state (or from all-OFF)
  - "Reset" button — restores all rings to OFF (the solved state), reinforcing to the player that all-OFF is the goal. Resets the move counter to 0.
  - "+" / "−" zoom buttons — move camera closer/farther from the origin
  - Polytope selector (16-cell / 24-cell / 600-cell)
- Win overlay: centered modal with congratulations message, move count, new game button.

### Responsive
- Canvas resizes with window (listen to `resize` event, update canvas dimensions and re-render).
- Works in both portrait and landscape orientations on mobile.
- The projected polytope scales to fill available space — adjust camera distance or FOV based on viewport.
- All overlay buttons/text must be at least **44×44px** touch targets (Apple HIG / Android minimum).
- UI overlay text and buttons should use responsive font sizes (e.g., `clamp()` or viewport units).

---

## File Structure
```
index.html        ← entry point
*.js / *.css      ← additional files as needed for clean separation
```
Load Three.js from CDN — no local node_modules or build step required.

---

## Deployment
- Hosted as a **static site on GitHub Pages**.
- No backend, no server-side logic, no network requests (beyond CDN loads).
- All assets loaded from CDN (Three.js) or inlined.
- The repository root should be deployable directly (index.html at root).

---

## Out of Scope
- Saving game state (no localStorage for v1).
- Sound effects.
- Undo button (may add later).
- Solving hints.
