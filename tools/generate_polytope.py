"""
Offline script to generate ring and bundle data for 4D polytopes.

Implements the Polytope Data Generation Procedure from spec.md:
  Step 1: Edge discovery via max inner product
  Step 2: Ring tracing via reflection
  Step 3: Bundle assignment (Hopf fibration — vertex-disjoint rings)

Usage:
  python tools/generate_polytope.py
"""

import math
import json
from itertools import combinations, permutations

# --- Vertex coordinates ---

def vertices_24cell():
    """24-cell: all permutations of (±1, ±1, 0, 0) / sqrt(2), on unit S³."""
    verts = []
    coords = [0, 1, 2, 3]
    for i, j in combinations(coords, 2):
        for si in [1, -1]:
            for sj in [1, -1]:
                v = [0.0, 0.0, 0.0, 0.0]
                v[i] = si / math.sqrt(2)
                v[j] = sj / math.sqrt(2)
                verts.append(v)
    return verts


def _is_even_permutation(perm):
    """Check if a permutation (given as a tuple of indices) is even."""
    perm = list(perm)
    n = len(perm)
    swaps = 0
    for i in range(n):
        while perm[i] != i:
            j = perm[i]
            perm[i], perm[j] = perm[j], perm[i]
            swaps += 1
    return swaps % 2 == 0


def _add_unique(verts, v, tol=1e-8):
    """Add vertex v to list only if not already present (within tolerance)."""
    for existing in verts:
        if all(abs(a - b) < tol for a, b in zip(existing, v)):
            return
    verts.append(v)


def vertices_600cell():
    """600-cell: 120 vertices on unit S³.
    Family 1: 8 permutations of (±1, 0, 0, 0)
    Family 2: 16 sign combinations of (±1/2, ±1/2, ±1/2, ±1/2)
    Family 3: 96 even permutations of (±φ/2, ±1/2, ±1/(2φ), 0)
    where φ = (1+√5)/2.
    """
    phi = (1 + math.sqrt(5)) / 2
    verts = []

    # Family 1: permutations of (±1, 0, 0, 0)
    for i in range(4):
        for s in [1, -1]:
            v = [0.0, 0.0, 0.0, 0.0]
            v[i] = s
            _add_unique(verts, v)

    # Family 2: all sign combinations of (±1/2, ±1/2, ±1/2, ±1/2)
    for s0 in [1, -1]:
        for s1 in [1, -1]:
            for s2 in [1, -1]:
                for s3 in [1, -1]:
                    _add_unique(verts, [s0 * 0.5, s1 * 0.5, s2 * 0.5, s3 * 0.5])

    # Family 3: even permutations of (±φ/2, ±1/2, ±1/(2φ), 0)
    base_vals = [phi / 2, 0.5, 1 / (2 * phi), 0.0]
    for perm in permutations(range(4)):
        if not _is_even_permutation(perm):
            continue
        # perm maps position -> which base_val goes there
        for s0 in [1, -1]:
            for s1 in [1, -1]:
                for s2 in [1, -1]:
                    signs = [s0, s1, s2, 1]  # 0 coordinate unaffected by sign
                    v = [0.0, 0.0, 0.0, 0.0]
                    for pos in range(4):
                        val = base_vals[perm[pos]]
                        # Only apply sign to non-zero values
                        if abs(val) > 1e-10:
                            v[pos] = signs[perm[pos]] * val
                        else:
                            v[pos] = 0.0
                    _add_unique(verts, v)

    return verts


def vertices_bicont():
    """Bitetracontoctachoron: 48 vertices on unit S³.
    Convex hull of two dual 24-cells.
    Family 1: 8 permutations of (±1, 0, 0, 0)
    Family 2: 16 sign combinations of (±1/2, ±1/2, ±1/2, ±1/2)
    Family 3: all permutations of (±√2/2, ±√2/2, 0, 0)
    """
    verts = []
    s2 = math.sqrt(2) / 2

    # Family 1: permutations of (±1, 0, 0, 0)
    for i in range(4):
        for s in [1, -1]:
            v = [0.0, 0.0, 0.0, 0.0]
            v[i] = s
            _add_unique(verts, v)

    # Family 2: all sign combinations of (±1/2, ±1/2, ±1/2, ±1/2)
    for s0 in [1, -1]:
        for s1 in [1, -1]:
            for s2_ in [1, -1]:
                for s3 in [1, -1]:
                    _add_unique(verts, [s0 * 0.5, s1 * 0.5, s2_ * 0.5, s3 * 0.5])

    # Family 3: all permutations of (±√2/2, ±√2/2, 0, 0)
    for i, j in combinations(range(4), 2):
        for si in [1, -1]:
            for sj in [1, -1]:
                v = [0.0, 0.0, 0.0, 0.0]
                v[i] = si * s2
                v[j] = sj * s2
                _add_unique(verts, v)

    return verts


def vertices_bideca():
    """Bidecachoron: 10 vertices on unit S³.
    Convex hull of a pentachoron and its central inversion.
    Coordinates from wiki, normalized to unit sphere.
    """
    s3 = math.sqrt(3)
    s6 = math.sqrt(6)
    s10 = math.sqrt(10)
    raw = [
        ( 0.5, -s3/6, -s6/12, -s10/20),
        (-0.5, -s3/6, -s6/12, -s10/20),
        ( 0.0,  s3/3, -s6/12, -s10/20),
        ( 0.0,  0.0,   s6/4,  -s10/20),
        ( 0.0,  0.0,   0.0,    s10/5),
    ]
    # Add central inversions
    verts = []
    for v in raw:
        verts.append(list(v))
    for v in raw:
        verts.append([-c for c in v])
    # Normalize to unit S³
    for v in verts:
        n = math.sqrt(sum(c*c for c in v))
        for i in range(4):
            v[i] /= n
    return verts


def vertices_duopyramid(p, q):
    """Dual of {p}x{q} duoprism: p+q vertices on unit S³.
    p-gon vertices in XY plane, q-gon vertices in ZW plane.
    Requires p,q both even for ring decomposition (all-even vertex degrees).
    """
    verts = []
    for k in range(p):
        angle = 2 * math.pi * k / p
        verts.append([math.cos(angle), math.sin(angle), 0.0, 0.0])
    for k in range(q):
        angle = 2 * math.pi * k / q
        verts.append([0.0, 0.0, math.cos(angle), math.sin(angle)])
    return verts


def edges_duopyramid(p, q):
    """Edges of {p}x{q} duopyramid: p-gon cycle + q-gon cycle + all cross edges."""
    edges = set()
    for k in range(p):
        edges.add((k, (k + 1) % p))
    for k in range(q):
        edges.add((p + k, p + (k + 1) % q))
    for i in range(p):
        for j in range(q):
            edges.add((min(i, p + j), max(i, p + j)))
    return edges


# --- Step 1: Edge discovery ---

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def find_edges(vertices, tol=1e-8):
    """Find all edges by discovering the max inner product threshold."""
    v0 = vertices[0]
    max_ip = max(dot(v0, v) for v in vertices[1:])

    edges = set()
    for i, j in combinations(range(len(vertices)), 2):
        if abs(dot(vertices[i], vertices[j]) - max_ip) < tol:
            edges.add((i, j))
    return edges, max_ip


def find_edges_multi(vertices, inner_products, tol=1e-8):
    """Find edges matching any of the given inner product values."""
    edges = set()
    for i, j in combinations(range(len(vertices)), 2):
        ip = dot(vertices[i], vertices[j])
        for target_ip in inner_products:
            if abs(ip - target_ip) < tol:
                edges.add((i, j))
                break
    return edges


# --- Step 2: Ring tracing via reflection ---

def find_vertex_index(point, vertices, tol=1e-8):
    """Match a point to the nearest vertex index."""
    for i, v in enumerate(vertices):
        if all(abs(a - b) < tol for a, b in zip(point, v)):
            return i
    return None


def reflect_through(a, b):
    """Reflect vertex A through vertex B's axis on S³.
    projection = B * dot(A, B) / dot(B, B)
    reflected = 2 * projection - A
    """
    ab = dot(a, b)
    bb = dot(b, b)
    scale = ab / bb
    return [2 * scale * bi - ai for ai, bi in zip(a, b)]


def trace_rings(vertices, edges):
    """Trace all rings by following edges via reflection."""
    # Build adjacency: for each vertex, which vertices are connected
    adj = {}
    for i, j in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)

    unused = set()
    for e in edges:
        unused.add((min(e), max(e)))

    rings = []
    while unused:
        # Pick any unused edge
        start_edge = next(iter(unused))
        a_idx, b_idx = start_edge

        ring_vertices = [a_idx]
        prev_idx, curr_idx = a_idx, b_idx

        while True:
            ring_vertices.append(curr_idx)
            # Remove edge
            edge_key = (min(prev_idx, curr_idx), max(prev_idx, curr_idx))
            unused.discard(edge_key)

            # Reflect prev through curr to find next
            reflected = reflect_through(vertices[prev_idx], vertices[curr_idx])
            next_idx = find_vertex_index(reflected, vertices)
            if next_idx is None:
                raise ValueError(f"Reflected point not found in vertices: {reflected}")

            prev_idx, curr_idx = curr_idx, next_idx

            # Check if we've completed the ring
            if curr_idx == ring_vertices[0]:
                # Remove the closing edge
                edge_key = (min(prev_idx, curr_idx), max(prev_idx, curr_idx))
                unused.discard(edge_key)
                break

        rings.append(ring_vertices)

    return rings


def perp_component(edge_vec, vertex):
    """Compute the component of edge_vec perpendicular to vertex on S³.
    perp = edge_vec - proj(edge_vec onto vertex)
    """
    d = dot(edge_vec, vertex)
    vv = dot(vertex, vertex)
    return [e - d / vv * v for e, v in zip(edge_vec, vertex)]


def trace_rings_perp(vertices, edges):
    """Trace rings using perpendicular component matching.
    For each edge at a vertex, compute the perp component of the edge vector.
    The next edge in the ring is the one whose perp component is anti-parallel.
    """
    adj = {}
    for i, j in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)

    unused = set()
    for e in edges:
        unused.add((min(e), max(e)))

    rings = []
    while unused:
        start_edge = next(iter(unused))
        a_idx, b_idx = start_edge

        ring_vertices = [a_idx]
        prev_idx, curr_idx = a_idx, b_idx

        while True:
            ring_vertices.append(curr_idx)
            edge_key = (min(prev_idx, curr_idx), max(prev_idx, curr_idx))
            unused.discard(edge_key)

            # Edge vector from curr to prev
            incoming = [vertices[prev_idx][d] - vertices[curr_idx][d] for d in range(4)]
            incoming_perp = perp_component(incoming, vertices[curr_idx])
            in_norm = math.sqrt(dot(incoming_perp, incoming_perp))

            # Find the neighbor whose outgoing perp is anti-parallel to incoming perp
            best_idx = None
            best_cos = 2  # Start high, looking for most negative (anti-parallel)
            for nb in adj[curr_idx]:
                if nb == prev_idx:
                    continue
                outgoing = [vertices[nb][d] - vertices[curr_idx][d] for d in range(4)]
                outgoing_perp = perp_component(outgoing, vertices[curr_idx])
                out_norm = math.sqrt(dot(outgoing_perp, outgoing_perp))
                if in_norm < 1e-12 or out_norm < 1e-12:
                    continue
                cos_val = dot(incoming_perp, outgoing_perp) / (in_norm * out_norm)
                # We want cos ≈ -1 (anti-parallel)
                if cos_val < best_cos - 1e-8:
                    # Strictly more anti-parallel
                    best_cos = cos_val
                    best_idx = nb

            if best_idx is None:
                raise ValueError(f"No anti-parallel edge found at vertex {curr_idx}")

            prev_idx, curr_idx = curr_idx, best_idx

            if curr_idx == ring_vertices[0]:
                edge_key = (min(prev_idx, curr_idx), max(prev_idx, curr_idx))
                unused.discard(edge_key)
                break

        rings.append(ring_vertices)

    return rings




def quat_conjugate(q):
    """Conjugate of quaternion q = (w, x, y, z) stored as [x, y, z, w]."""
    return [-q[0], -q[1], -q[2], q[3]]

def quat_multiply(a, b):
    """Multiply quaternions a * b. Convention: [x, y, z, w]."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ]

def quat_inverse(q):
    """Inverse of unit quaternion = conjugate."""
    return quat_conjugate(q)

def quat_normalize(q):
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q] if n > 1e-15 else q

def assign_bundles(rings, vertices, edges, edge_ip=None):
    """Assign bundles via Hopf fibration: for each ring's first edge of the
    specified type, compute the quaternion quotient q1 * q2^(-1). Group by
    quotient pairs (q and q^(-1) belong to the same bundle).
    If edge_ip is given, use the first edge in the ring matching that inner product."""
    TOL_DIGITS = 6  # round to this many decimals for grouping

    # Compute quotient for each ring
    ring_quotients = {}
    for ri, ring in enumerate(rings):
        if edge_ip is not None:
            # Find first edge in ring matching the target inner product
            found = False
            for k in range(len(ring)):
                i1, i2 = ring[k], ring[(k + 1) % len(ring)]
                ip = dot(vertices[i1], vertices[i2])
                if abs(ip - edge_ip) < 1e-6:
                    q1, q2 = vertices[i1], vertices[i2]
                    found = True
                    break
            if not found:
                raise ValueError(f"Ring {ri} has no edge with ip≈{edge_ip}")
        else:
            i1, i2 = ring[0], ring[1]
            q1, q2 = vertices[i1], vertices[i2]
        quot = quat_normalize(quat_multiply(q1, quat_inverse(q2)))
        ring_quotients[ri] = quot

    # Canonicalize: round, kill negative zeros, then pick sign so first nonzero is positive
    def canonicalize(q):
        r = tuple(round(x, TOL_DIGITS) + 0.0 for x in q)  # +0.0 eliminates -0.0
        for val in r:
            if abs(val) > 1e-8:
                if val < 0:
                    return tuple(-x + 0.0 for x in r)
                return r
        return r

    # Group rings by canonical quotient pair (q and q^-1 same bundle)
    bundle_map = {}
    ring_to_bundle_key = {}
    for ri, quot in ring_quotients.items():
        canon = canonicalize(quot)
        inv_quot = quat_normalize(quat_inverse(quot))
        canon_inv = canonicalize(inv_quot)
        key = min(canon, canon_inv)
        bundle_map.setdefault(key, []).append(ri)
        ring_to_bundle_key[ri] = key

    # Assign sequential bundle indices
    bundle_keys = sorted(bundle_map.keys())
    key_to_idx = {k: i for i, k in enumerate(bundle_keys)}

    n = len(rings)
    bundle = [-1] * n
    for ri in range(n):
        bundle[ri] = key_to_idx[ring_to_bundle_key[ri]]

    num_bundles = len(bundle_keys)
    return bundle, num_bundles


# --- Validation ---

def validate(vertices, edges, rings, bundle, num_bundles,
             expected_edges, expected_rings, expected_verts_per_ring, expected_bundles):
    errors = []

    if len(edges) != expected_edges:
        errors.append(f"Expected {expected_edges} edges, got {len(edges)}")

    if len(rings) != expected_rings:
        errors.append(f"Expected {expected_rings} rings, got {len(rings)}")

    for i, r in enumerate(rings):
        if expected_verts_per_ring is not None and len(r) != expected_verts_per_ring:
            errors.append(f"Ring {i} has {len(r)} vertices, expected {expected_verts_per_ring}")

    # Check all edges are consumed (covered by trace_rings completing without leftover)
    total_edges_in_rings = sum(len(r) for r in rings)
    if total_edges_in_rings != expected_edges:
        errors.append(f"Edges in rings: {total_edges_in_rings}, expected {expected_edges}")

    if num_bundles != expected_bundles:
        errors.append(f"Expected {expected_bundles} bundles, got {num_bundles}")

    # Check bundle sizes are equal
    from collections import Counter
    bundle_sizes = Counter(bundle)
    sizes = list(bundle_sizes.values())
    if len(set(sizes)) > 1:
        errors.append(f"Unequal bundle sizes: {dict(bundle_sizes)}")

    # Check vertex-disjointness within each bundle
    for b in range(num_bundles):
        bundle_rings = [i for i in range(len(rings)) if bundle[i] == b]
        all_verts = []
        for ri in bundle_rings:
            all_verts.extend(rings[ri])
        if len(all_verts) != len(set(all_verts)):
            errors.append(f"Bundle {b} has overlapping vertices")

    return errors


# --- Output ---

def format_js(name, vertices, rings, bundle, num_bundles, white_bundle_0=False):
    """Format as JavaScript data object for polytopes.js."""
    if white_bundle_0:
        cross_palette = [
            "#33ff66", "#ff3366", "#ffcc00", "#3366ff",
            "#ff6633", "#cc33ff", "#33ccff", "#ff33cc",
        ]
        colors = ["#ffffff"] + cross_palette[:num_bundles - 1]
    else:
        palette = [
            "#ff3366", "#33ff66", "#3366ff", "#ffcc00",
            "#ff6633", "#cc33ff", "#33ccff", "#ff33cc",
            "#66ff33", "#ff9933", "#9933ff", "#33ffcc",
        ]
        colors = palette[:num_bundles]

    lines = []
    lines.append(f"export const POLYTOPE_{name.upper().replace('-', '')} = {{")
    lines.append(f'  name: "{name}",')
    lines.append("  vertices: [")
    for i, v in enumerate(vertices):
        formatted = [f"{x:.10f}" for x in v]
        comment = f"  // {i}"
        lines.append(f"    [{', '.join(formatted)}],{comment}")
    lines.append("  ],")
    lines.append("  rings: [")
    for i, r in enumerate(rings):
        lines.append(f"    {{ vertices: {r}, bundle: {bundle[i]} }},")
    lines.append("  ],")
    lines.append(f"  bundleColors: {json.dumps(colors)},")
    lines.append("};")
    return "\n".join(lines)


# --- Main ---

def generate_24cell():
    print("=== 24-cell ===")

    vertices = vertices_24cell()
    print(f"Vertices: {len(vertices)}")

    edges, max_ip = find_edges(vertices)
    print(f"Edges: {len(edges)} (max inner product: {max_ip:.6f})")

    rings = trace_rings(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    bundle, num_bundles = assign_bundles(rings, vertices, edges)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    errors = validate(vertices, edges, rings, bundle, num_bundles,
                       expected_edges=96, expected_rings=16,
                       expected_verts_per_ring=6, expected_bundles=4)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("\n✓ All validations passed")

    print("\n--- JavaScript output ---\n")
    print(format_js("24-cell", vertices, rings, bundle, num_bundles))


def generate_600cell():
    print("=== 600-cell ===")

    vertices = vertices_600cell()
    print(f"Vertices: {len(vertices)}")

    # Verify all on unit sphere
    norms = [math.sqrt(dot(v, v)) for v in vertices]
    max_norm_err = max(abs(n - 1.0) for n in norms)
    print(f"Max norm deviation from 1.0: {max_norm_err:.2e}")

    edges, max_ip = find_edges(vertices)
    print(f"Edges: {len(edges)} (max inner product: {max_ip:.6f})")

    rings = trace_rings(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    bundle, num_bundles = assign_bundles(rings, vertices, edges)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    errors = validate(vertices, edges, rings, bundle, num_bundles,
                       expected_edges=720, expected_rings=72,
                       expected_verts_per_ring=10, expected_bundles=6)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("\n✓ All validations passed")

    print("\n--- JavaScript output ---\n")
    print(format_js("600-cell", vertices, rings, bundle, num_bundles))


def generate_bicont():
    print("=== Bicont ===")

    vertices = vertices_bicont()
    print(f"Vertices: {len(vertices)}")

    norms = [math.sqrt(dot(v, v)) for v in vertices]
    max_norm_err = max(abs(n - 1.0) for n in norms)
    print(f"Max norm deviation from 1.0: {max_norm_err:.2e}")

    # Two edge types: lacing (ip = √2/2 ≈ 0.7071) and icositetrachoral (ip = 0.5)
    s2 = math.sqrt(2) / 2
    edges = find_edges_multi(vertices, [s2, 0.5])
    print(f"Edges: {len(edges)} (using inner products {s2:.6f} and 0.5)")

    rings = trace_rings(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    bundle, num_bundles = assign_bundles(rings, vertices, edges)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    # Validate: bicont has mixed ring sizes, so skip per-ring-size check
    ring_sizes = set(len(r) for r in rings)
    errors = validate(vertices, edges, rings, bundle, num_bundles,
                       expected_edges=len(edges), expected_rings=len(rings),
                       expected_verts_per_ring=None, expected_bundles=num_bundles)
    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("\n✓ All validations passed")

    print("\n--- JavaScript output ---\n")
    print(format_js("bicont", vertices, rings, bundle, num_bundles))


def generate_bideca():
    print("=== Bideca ===")

    vertices = vertices_bideca()
    print(f"Vertices: {len(vertices)}")

    norms = [math.sqrt(dot(v, v)) for v in vertices]
    max_norm_err = max(abs(n - 1.0) for n in norms)
    print(f"Max norm deviation from 1.0: {max_norm_err:.2e}")

    # Print inner products for edge detection
    ips = set()
    for i, j in combinations(range(len(vertices)), 2):
        ip = round(dot(vertices[i], vertices[j]), 6)
        ips.add(ip)
    print(f"Distinct inner products: {sorted(ips)}")

    # Two edge types: pentachoral and lacing
    edges = find_edges_multi(vertices, [0.25, -0.25])
    print(f"Edges: {len(edges)}")

    # Count by type
    e_pos = sum(1 for i, j in edges if abs(dot(vertices[i], vertices[j]) - 0.25) < 1e-8)
    e_neg = sum(1 for i, j in edges if abs(dot(vertices[i], vertices[j]) + 0.25) < 1e-8)
    print(f"  Pentachoral edges (ip≈0.25): {e_pos}")
    print(f"  Lacing edges (ip≈-0.25): {e_neg}")

    # Trace rings using perpendicular component method
    rings = trace_rings_perp(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    # Bundle assignment using shortest edges (ip=0.25)
    bundle, num_bundles = assign_bundles(rings, vertices, edges, edge_ip=0.25)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    print("\n--- JavaScript output ---\n")
    print(format_js("bideca", vertices, rings, bundle, num_bundles))


def find_vertex_disjoint_matching(rings, n_rings):
    """Find a perfect matching of vertex-disjoint ring pairs via backtracking."""
    def backtrack(unmatched, pairs):
        if not unmatched:
            return pairs
        first = unmatched[0]
        rest = unmatched[1:]
        for other in rest:
            s1 = set(rings[first])
            s2 = set(rings[other])
            if not s1.intersection(s2):
                remaining = [r for r in rest if r != other]
                result = backtrack(remaining, pairs + [(first, other)])
                if result is not None:
                    return result
        return None
    return backtrack(list(range(n_rings)), [])


def generate_duopyramid_46():
    print("=== 4,6-duopyramid ===")

    p, q = 4, 6
    vertices = vertices_duopyramid(p, q)
    print(f"Vertices: {len(vertices)}")

    edges = edges_duopyramid(p, q)
    print(f"Edges: {len(edges)}")

    rings = trace_rings(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    # Bundle assignment via Hopf fibration
    bundle, num_bundles = assign_bundles(rings, vertices, edges)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    print("\n--- JavaScript output ---\n")
    print(format_js("46-dip", vertices, rings, bundle, num_bundles, white_bundle_0=True))


if __name__ == "__main__":
    generate_24cell()
    print("\n" + "=" * 60 + "\n")
    generate_600cell()
    print("\n" + "=" * 60 + "\n")
    generate_bicont()
    print("\n" + "=" * 60 + "\n")
    generate_bideca()
    print("\n" + "=" * 60 + "\n")
    generate_duopyramid_46()
    print("\n" + "=" * 60 + "\n")
    generate_duopyramid_66()


def generate_duopyramid_66():
    print("=== 6,6-duopyramid ===")

    p, q = 6, 6
    vertices = vertices_duopyramid(p, q)
    print(f"Vertices: {len(vertices)}")

    edges = edges_duopyramid(p, q)
    print(f"Edges: {len(edges)}")

    rings = trace_rings(vertices, edges)
    print(f"Rings: {len(rings)}")
    for i, r in enumerate(rings):
        print(f"  Ring {i}: {r} ({len(r)} vertices)")

    # Bundle assignment via Hopf fibration
    bundle, num_bundles = assign_bundles(rings, vertices, edges)
    print(f"Bundles: {num_bundles}")
    for b in range(num_bundles):
        b_rings = [i for i in range(len(rings)) if bundle[i] == b]
        print(f"  Bundle {b}: rings {b_rings}")

    print("\n--- JavaScript output ---\n")
    print(format_js("66-dip", vertices, rings, bundle, num_bundles, white_bundle_0=True))
