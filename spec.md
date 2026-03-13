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

| Polytope | Vertices | Edges | Rings | Vertices/Ring | Edges/Ring | Hopf Bundles | GF(2) Rank | God's # | Status      |
|----------|----------|-------|-------|---------------|------------|--------------|------------|---------|-------------|
| 16-cell  | 8        | 24    | 6     | 4             | 4          | 3 (2+2+2)    | 3          | 2       | Implemented |
| 24-cell  | 24       | 96    | 16    | 6             | 6          | 4 (4+4+4+4)  | 8          | 4       | Implemented |
| 600-cell | 120      | 720   | 72    | 10            | 10         | 6 (12×6)     | 36         | ≥ 10    | Implemented |
| Bicont   | 48       | 336   | 50    | 6 or 8        | 6 or 8     | 7             | 20         | ≥ 8     | Implemented |
| Bideca   | 10       | 40    | 10    | 4             | 4          | 5 (2+2+2+2+2)| 4          | 2       | Implemented |
| {6}+{6}  | 12       | 48    | 11    | 4 or 6        | 4 or 6     | 4 (3+3+3+2)  | 6          | 6       | Implemented |
| {8}+{8}  | 16       | 80    | 18    | 4 or 8        | 4 or 8     | 5 (4+4+4+4+2)| 7          | 4       | Implemented |
| {10}+{10}| 20       | 120   | 27    | 4 or 10       | 4 or 10    | 6 (5×5+2)    | 10         | 10      | Implemented |
| {12}+{12}| 24       | 168   | 38    | 4 or 12       | 4 or 12    | 7 (6×6+2)    | 11         | 6       | Implemented |

- Each polytope is defined as a data object (see Polytope Data Format below). Adding a new polytope = adding a new data file.

### Incidence Matrix and GF(2) Analysis

The incidence matrix **A** is an *n × m* binary matrix (vertices × rings) where A[i][j] = 1 iff vertex i belongs to ring j. Clicking vertex i toggles exactly the rings in row i, so the game's toggle space is the row space of **A** over GF(2).

- The rank equals exactly half the number of rings for the regular polytopes (16-cell, 24-cell, 600-cell). For bicont (which has mixed ring sizes), rank/rings = 20/50 = 2/5. For bideca, rank/rings = 4/10 = 2/5.
- **Reachable states**: only 2^rank of the 2^rings total ring-state configurations can be reached from the all-off state by clicking vertices.
- **Nullity** (kernel dimension = rings − rank): the number of independent "null toggles" — sets of vertex clicks that leave all rings unchanged.

#### Rank formula for {2m}+{2n} duopyramids

**Theorem.** The GF(2) rank of the {2m}+{2n} duopyramid incidence matrix is **m+n** if at least one of m,n is odd, and **m+n−1** if both m,n are even.

**Structure.** The {2m}+{2n} duopyramid has 2(m+n) vertices forming m+n antipodal pairs: m pairs P₀,…,P_{m−1} from the {2m}-gon in the XY plane, and n pairs Q₀,…,Q_{n−1} from the {2n}-gon in the ZW plane. Each antipodal pair toggles the same set of rings, giving m+n independent controls. The rings are:
- 1 XY-polygon ring (through all {2m}-gon vertices)
- 1 ZW-polygon ring (through all {2n}-gon vertices)
- mn cross rings, one for each pair (Pᵢ, Qⱼ), forming a great circle through both pairs

The reduced incidence matrix after identifying antipodal pairs has rows:
- **Pᵢ**: 1 on the XY-polygon ring, and 1 on cross ring (i,j) for all j = 0,…,n−1
- **Qⱼ**: 1 on the ZW-polygon ring, and 1 on cross ring (i,j) for all i = 0,…,m−1

**Proof.** A linear dependency Σ aᵢPᵢ + Σ bⱼQⱼ = 0 over GF(2) requires:
1. From cross column (i,j): aᵢ + bⱼ = 0 for all i,j ⟹ all aᵢ and bⱼ equal some constant c
2. From the XY-polygon column: mc = 0 (mod 2)
3. From the ZW-polygon column: nc = 0 (mod 2)

A nontrivial solution c = 1 exists iff m ≡ 0 and n ≡ 0 (mod 2), giving kernel dimension 1 and rank m+n−1. Otherwise the kernel is trivial and rank = m+n. ∎

**Corollary.** The {2m}+{2n} duopyramid is full rank (all 2^{m+n} states reachable, every scramble solvable) iff m and n are not both even. For the duopyramids in the game: {4}+{6} has m=2, n=3 (n odd → full rank 5); {6}+{6} has m=n=3 (both odd → full rank 6). The 16-cell = {4}+{4} has m=n=2 (both even → rank 3 = m+n−1).

#### General {2m}+{2n} duopyramid formulas

The {2m}+{2n} duopyramid (dual of {2m}×{2n} duoprism) has:
- **Vertices**: 2(m+n), forming m+n antipodal pairs
- **Edges**: 2m + 2n + 4mn
- **Rings**: 2 + mn — two polygon rings (lengths 2m and 2n) plus mn cross rings (each length 4)
- **Ring decomposition constraint**: requires 2m and 2n both even (i.e., m,n ≥ 2), since all vertex degrees must be even. Odd polygon sides give odd vertex degrees, making edge-disjoint ring decomposition impossible.

**God's number** (proven for all {2m}+{2n}):
- **Full rank** (m or n odd): God's number = m+n, move distribution = C(m+n, k).
- **Not full rank** (both even): God's number = (m+n)/2, distribution = C(m+n, k) for k < (m+n)/2, halved at k = (m+n)/2. The kernel vector (click all antipodal pairs) identifies states at distance k with distance (m+n)−k.

**Asymmetric (m≠n) reference** (not in the game, included for analysis):

| Polytope | Vertices | Edges | Rings | Rank | God's # |
|----------|----------|-------|-------|------|---------|
| {4}+{6}  | 10       | 34    | 8     | 5    | 5       |
| {4}+{8}  | 12       | 44    | 10    | 5    | 3       |
| {4}+{10} | 14       | 54    | 12    | 7    | 7       |
| {6}+{8}  | 14       | 62    | 14    | 7    | 7       |
| {6}+{10} | 16       | 76    | 17    | 8    | 8       |
| {8}+{12} | 20       | 116   | 26    | 9    | 5       |

#### {2n}+{2n} duopyramid reference table

| Polytope | Vertices | Edges | Rings | Hopf Bundles (sizes) | Rank | God's # | Reachable States |
|----------|----------|-------|-------|----------------------|------|---------|------------------|
| {4}+{4}  | 8        | 24    | 6     | 3 (2+2+2)            | 3    | 2       | 2³ = 8           |
| {6}+{6}  | 12       | 48    | 11    | 4 (3+3+3+2)          | 6    | 6       | 2⁶ = 64          |
| {8}+{8}  | 16       | 80    | 18    | 5 (4+4+4+4+2)        | 7    | 4       | 2⁷ = 128         |
| {10}+{10}| 20       | 120   | 27    | 6 (5+5+5+5+5+2)      | 10   | 10      | 2¹⁰ = 1024       |
| {12}+{12}| 24       | 168   | 38    | 7 (6+6+6+6+6+6+2)    | 11   | 6       | 2¹¹ = 2048       |

- **Hopf bundles**: always n+1 bundles — one bundle of 2 (the two polygon rings) plus n bundles of n (cross rings).
- **Full rank** (n odd): God's number = n, move distribution = C(n, k). Every scramble solvable.
- **Not full rank** (n even): God's number = n/2, move distribution = C(n, k) for k < n/2, halved at k = n/2. The kernel vector (click all antipodal pairs) identifies states at distance k with distance n−k.

### God's Number

God's number is the maximum number of moves needed to solve any solvable puzzle optimally. Since click order doesn't matter and double-clicking cancels out, the minimum moves for a state equals the minimum Hamming weight solution vector over GF(2).

Lower bounds are established by counting: with n independent click choices, at most Σ C(n,i) for i=0..k distinct states are reachable in ≤k moves. For polytopes with antipodal symmetry (e.g., Bicont), each vertex and its antipode toggle the same rings, so n = vertices/2.

Move distributions for polytopes with exact God's numbers:

| Polytope | Move Distribution |
|----------|-------------------|
| 16-cell  | 0:1, 1:4, 2:3 |
| 24-cell  | 0:1, 1:12, 2:66, 3:116, 4:61 |
| Bideca   | 0:1, 1:5, 2:10 |
| {6}+{6}  | 0:1, 1:6, 2:15, 3:20, 4:15, 5:6, 6:1 |

### Ring Coloring
- Each ring is assigned a **color** for its ON state. OFF-state rings are always medium gray (#888888, 70% opacity).
- **16-cell**: each ring gets a unique color (one color per ring, 6 colors for 6 rings). Hopf fibration gives 3 bundles of 2, but 6 individual colors are used for visual variety.
- **Bideca**: 5 bundles of 2 vertex-disjoint rings each. Quaternion quotient gives 10 distinct quotients (no shared bundles), so bundles are assigned by finding a perfect matching of vertex-disjoint ring pairs instead.
- **{2n}+{2n} duopyramids**: n+1 Hopf bundles via quaternion quotients — 1 bundle of 2 polygon rings (white, aligned to main axes) + n bundles of n cross rings. Cross-bundle colors are consistent across all duopyramids: green, red, yellow, blue, orange, purple.
- **24-cell, 600-cell, and Bicont**: rings are grouped into **Hopf fibration bundles** via quaternion quotients — rings in the same bundle share a color. The `bundle` field in the polytope data encodes this grouping.
- Color palette: `["#ff3366", "#33ff66", "#3366ff", "#ffcc00", "#ff6633", "#cc33ff", "#33ccff"]`.

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
- **Distance fade**: vertices and ring tubes gradually fade to transparent when their stereographic projection places them far from the origin (approaching infinity). Fade uses a smoothstep from distance 10 to 15. Tubes use a custom `ShaderMaterial` with per-vertex fade computed in GLSL; vertex spheres set `material.opacity` from the same distance range.
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
- After 1 second, "Scramble Again" button and "or try a different polytope" hint appear. Tapping the hint dismisses the overlay and pulses the polytope selector to draw attention.

### Reset
- Reset works immediately with one click.
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

**Step 2 — Ring tracing**:

Two methods are available depending on the polytope's edge geometry:

**Method A — Reflection** (for polytopes whose edges lie on great circles, e.g., 16-cell, 24-cell, 600-cell, Bicont):
1. Maintain a set of unused edges. Pick any unused edge (A, B) to start a new ring.
2. Compute the next vertex by reflecting A through B's axis on S³:
   - `projection = B × dot(A, B) / dot(B, B)`
   - `reflected = 2 × projection − A`
   - Match `reflected` to the nearest vertex index (within tolerance).
3. The next edge is (B, reflected). Mark edge (A, B) as used. Advance: A ← B, B ← reflected.
4. Repeat until returning to the starting edge. Record the ordered vertex sequence as one ring.
5. Repeat from step 1 until all edges are consumed.

**Method B — Perpendicular component** (for polytopes whose edges don't individually lie on great circles, e.g., Bideca):
1. For a given edge (A, B), compute the edge vector `e = A − B` and its component perpendicular to B on S³: `perp = e − (e·B / B·B) × B`.
2. Among all other edges incident to B, find the one whose perpendicular component is most anti-parallel (cosine ≈ −1) to the incoming perpendicular. This is the continuation of the ring.
3. Follow edges using this rule until the ring closes.
4. Repeat until all edges are consumed.

**Validation**: confirm the expected ring count and that each ring has the expected vertex count. Polytopes with mixed edge lengths (e.g., Bicont, Bideca) may have rings of different sizes or alternating edge types.

**Note**: Method B generalizes Method A. When edges lie on great circles, the reflection C = 2(A·B)B − A gives `perp_out = (A·B)B − A = −perp_in`, so the perpendicular components are exactly anti-parallel (cosine = −1) and both methods select the same next edge. Method A is more direct (computes the exact target point), while Method B works even when edges don't form great circles.

**Step 3 — Bundle assignment**:

**Method A — Hopf fibration via quaternion quotients** (24-cell, 600-cell, Bicont):
1. For each ring, take the first edge of a chosen type (v1, v2) and treat each vertex as a quaternion [x, y, z, w].
2. Compute the quotient q1 × q2⁻¹ and normalize it.
3. Canonicalize by rounding components (6 decimals), eliminating negative zeros, and making the first nonzero component positive.
4. Group rings whose canonical quotients form inverse pairs (q and q⁻¹) — these belong to the same bundle.
5. For polytopes with mixed edge types (e.g., Bicont, Bideca), use only the shortest edges for the quotient computation.
6. **Validation**: confirm expected bundle count. Regular polytopes have equal-size bundles (e.g., 4 bundles × 4 rings for 24-cell, 6 bundles × 12 rings for 600-cell). Bicont has 7 bundles of unequal sizes.

**Method B — Combinatorial vertex-disjoint pairing** (Bideca):
If the quaternion quotient method yields all-distinct quotients (no shared bundles), bundles can instead be assigned by finding a perfect matching of vertex-disjoint ring pairs. Two rings are vertex-disjoint if they share no vertices. A perfect matching partitions all rings into pairs. This is solved as a combinatorial search (backtracking over disjoint pairs). Bideca has 6 possible perfect matchings; any one gives 5 bundles of 2 rings each.

**Override for aesthetics** (16-cell):
16-cell has 3 Hopf bundles of 2 rings each, but intentionally uses 6 bundles (one per ring) for maximum color variety.

**Step 4 — Cell center**:
The `cellCenter` field positions the polytope's initial 4D orientation. It should be a vertex of the **dual polytope**, normalized to unit S³. This places a cell face toward the viewer for a visually appealing default view. Look up the dual on a polytope wiki and use one of its vertex coordinates.

### Adding a New Polytope — Walkthrough

This documents the full process used to add Bideca (bidecachoron) as a worked example.

**1. Look up vertex coordinates**:
- Source: [polytope.miraheze.org/wiki/Bidecachoron](https://polytope.miraheze.org/wiki/Bidecachoron)
- Bideca = convex hull of a pentachoron and its central inversion (10 vertices).
- Copy coordinates from the wiki. Normalize all vertices to lie on the unit 3-sphere S³ (divide by circumradius).
- Verify: all vertex norms should equal 1.0 within floating-point tolerance.

**2. Identify edge types and discover edges**:
- Compute all pairwise inner products between vertices. Distinct values indicate different edge lengths.
- Bideca has inner products {−1.0, −0.25, 0.25}. The value −1.0 is the antipodal pair, leaving two edge types: ip = 0.25 (pentachoral edges, 20) and ip = −0.25 (lacing edges, 20), totaling 40 edges.
- For polytopes with a single edge type, use `find_edges()`. For multiple types, use `find_edges_multi()` with a list of target inner products.

**3. Trace rings**:
- First attempt: reflection method (Method A). If the reflected point lands on a vertex, rings are successfully traced.
- If reflection fails (reflected point not found among vertices), the edges don't lie on great circles. Use the perpendicular component method (Method B) instead.
- Bideca: reflection failed because pentachoron edges don't form great circles. Perpendicular component method succeeded, yielding 10 rings of 4 vertices each, alternating between the two edge types.
- Verify: all edges consumed, each vertex appears in the expected number of rings (4 for bideca).

**4. Assign bundles**:
- Try quaternion quotient method first (using shortest edges for mixed-type polytopes).
- Bideca: all 10 quotients were distinct with w = 0.25 — no inverse pairs matched. Quaternion method gives 10 singleton bundles.
- Fallback: search for vertex-disjoint ring pairs via combinatorial matching. Found 6 perfect matchings, each giving 5 bundles of 2 rings. Chose first matching: {(0,3), (1,2), (4,9), (5,6), (7,8)}.
- Assign 5 colors (reusing palette from other polytopes).

**5. Set cell center**:
- Look up the dual polytope (Bideca's dual = Decachoron).
- Source: [polytope.miraheze.org/wiki/Decachoron](https://polytope.miraheze.org/wiki/Decachoron)
- Take a vertex of the decachoron, normalize to unit S³: [0.75, 0.25, 0.25, √5/4].
- Verify it is NOT a vertex of the bideca itself.

**6. Add to codebase**:
- Add polytope data object to `src/polytopes.js` with vertices, rings (with bundle indices), bundleColors, and cellCenter.
- Add import and map entry in `src/main.js`.
- Add `<option>` to selector in `index.html`.
- If the polytope has many vertices/edges, adjust vertex and tube scaling in `src/rendering.js`.
- Update `tools/generate_polytope.py` with the vertex generation and ring tracing functions.
- Update `tools/gf2_rank.py` to include the new polytope.
- Run GF(2) rank analysis and God's number computation (if feasible).
- Update `spec.md` tables.

**7. Verify**:
- Run `python tools/generate_polytope.py` to verify ring/bundle generation.
- Test locally with `python -m http.server 8080`.
- Check visual appearance: rings should form visible closed loops, colors should be distinct.

---

## UI

### Layout
- Full-viewport canvas.
- Minimal overlay (top-right corner):
  - Move counter
  - "Scramble" button
  - "Reset" button
  - "+" / "−" zoom buttons
  - Polytope selector (dropdown: 16-cell, 24-cell, 600-cell, Bicont, Bideca, {6}+{6}, {8}+{8}, {10}+{10}, {12}+{12})
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

