"""Compute GF(2) rank of incidence matrices for all polytopes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from generate_polytope import vertices_24cell, vertices_600cell, find_edges, trace_rings
from sympy import Matrix, GF
from sympy.polys.matrices import DomainMatrix


def gf2_rank(name, vertices, rings):
    n = len(vertices)
    m = len(rings)
    M = [[0] * m for _ in range(n)]
    for j, ring in enumerate(rings):
        for vi in ring:
            M[vi][j] = 1
    dm = DomainMatrix.from_Matrix(Matrix(M)).convert_to(GF(2))
    rank = dm.rank()
    print(f"{name}: {n} vertices x {m} rings, GF(2) rank = {rank}")
    print(f"  Nullity (kernel dim) = {m} - {rank} = {m - rank}")
    print(f"  Reachable states = 2^{rank}")
    print(f"  Total ring states = 2^{m}")
    print()


# 16-cell
rings_16 = [[0,2,1,3],[0,4,1,5],[0,6,1,7],[2,4,3,5],[2,6,3,7],[4,6,5,7]]
verts_16 = [[1,0,0,0],[-1,0,0,0],[0,1,0,0],[0,-1,0,0],
            [0,0,1,0],[0,0,-1,0],[0,0,0,1],[0,0,0,-1]]
gf2_rank("16-cell", verts_16, rings_16)

# 24-cell
v24 = vertices_24cell()
e24, _ = find_edges(v24)
r24 = trace_rings(v24, e24)
gf2_rank("24-cell", v24, r24)

# 600-cell
v600 = vertices_600cell()
e600, _ = find_edges(v600)
r600 = trace_rings(v600, e600)
gf2_rank("600-cell", v600, r600)
