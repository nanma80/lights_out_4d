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


# --- Step 3: Bundle assignment ---

def assign_bundles(rings, num_vertices):
    """Group rings into bundles of equal size where each bundle's rings are
    pairwise vertex-disjoint and together cover all vertices.
    Uses backtracking to find a valid partition."""
    ring_sets = [set(r) for r in rings]
    n = len(rings)
    verts_per_ring = len(rings[0])
    bundle_size = num_vertices // verts_per_ring  # rings per bundle

    # Build compatibility: which rings are pairwise vertex-disjoint
    compatible = [[True] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if ring_sets[i] & ring_sets[j]:
                compatible[i][j] = False
                compatible[j][i] = False

    # Find all maximal cliques of size bundle_size that cover all vertices
    all_vertices = set(range(num_vertices))

    def find_bundle(candidates, current, covered):
        if len(current) == bundle_size:
            if covered == all_vertices:
                return [list(current)]
            return []
        results = []
        for idx, c in enumerate(candidates):
            if ring_sets[c] & covered:
                continue
            if not all(compatible[c][r] for r in current):
                continue
            current.append(c)
            results.extend(find_bundle(candidates[idx + 1:], current, covered | ring_sets[c]))
            current.pop()
            if results:
                break  # only need one per starting ring
        return results

    # Partition all rings into bundles via backtracking
    bundle = [-1] * n

    def partition(remaining, bundle_idx):
        if not remaining:
            return True
        bundles_found = find_bundle(remaining, [], set())
        for b in bundles_found:
            for r in b:
                bundle[r] = bundle_idx
            new_remaining = [r for r in remaining if r not in b]
            if partition(new_remaining, bundle_idx + 1):
                return True
            for r in b:
                bundle[r] = -1
        return False

    all_ring_indices = list(range(n))
    success = partition(all_ring_indices, 0)
    num_bundles = max(bundle) + 1 if success else -1

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
        if len(r) != expected_verts_per_ring:
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

def format_js(name, vertices, rings, bundle, num_bundles):
    """Format as JavaScript data object for polytopes.js."""
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

    bundle, num_bundles = assign_bundles(rings, len(vertices))
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

    bundle, num_bundles = assign_bundles(rings, len(vertices))
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


if __name__ == "__main__":
    generate_24cell()
    print("\n" + "=" * 60 + "\n")
    generate_600cell()
