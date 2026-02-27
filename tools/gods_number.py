"""Compute God's number for Lights Out on polytopes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_polytope import vertices_24cell, find_edges, trace_rings

def gods_number(name, n, m, all_rings):
    vert_rings = [[] for _ in range(n)]
    for j, ring in enumerate(all_rings):
        for vi in ring:
            vert_rings[vi].append(j)

    state_min = {}
    total = 1 << n
    for mask in range(total):
        state = 0  # use bitmask for speed
        weight = 0
        for i in range(n):
            if (mask >> i) & 1:
                weight += 1
                for j in vert_rings[i]:
                    state ^= (1 << j)
        if state not in state_min or weight < state_min[state]:
            state_min[state] = weight
        if mask % 1000000 == 0 and mask > 0:
            print(f"  ...{mask}/{total} ({100*mask//total}%)", flush=True)

    print(f"\n{name}:")
    print(f"  Reachable states: {len(state_min)}")
    # Distribution of moves
    dist = {}
    for moves in state_min.values():
        dist[moves] = dist.get(moves, 0) + 1
    for k in sorted(dist):
        print(f"  {dist[k]} states need {k} moves")
    gods = max(state_min.values())
    print(f"  God's number: {gods}")
    return gods

# 16-cell
rings_16 = [[0,2,1,3],[0,4,1,5],[0,6,1,7],[2,4,3,5],[2,6,3,7],[4,6,5,7]]
gods_number("16-cell", 8, 6, rings_16)

# 24-cell
v24 = vertices_24cell()
e24, _ = find_edges(v24)
r24 = trace_rings(v24, e24)
gods_number("24-cell", 24, 16, r24)
