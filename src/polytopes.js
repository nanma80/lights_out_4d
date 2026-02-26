// polytopes.js — 4D polytope data definitions

export const POLYTOPE_16CELL = {
  name: "16-cell",
  vertices: [
    [1, 0, 0, 0],  // 0: +X
    [-1, 0, 0, 0], // 1: -X
    [0, 1, 0, 0],  // 2: +Y
    [0, -1, 0, 0], // 3: -Y
    [0, 0, 1, 0],  // 4: +Z
    [0, 0, -1, 0], // 5: -Z
    [0, 0, 0, 1],  // 6: +W
    [0, 0, 0, -1], // 7: -W
  ],
  rings: [
    { vertices: [0, 2, 1, 3], bundle: 0 },  // XY plane
    { vertices: [0, 4, 1, 5], bundle: 1 },  // XZ plane
    { vertices: [0, 6, 1, 7], bundle: 2 },  // XW plane
    { vertices: [2, 4, 3, 5], bundle: 3 },  // YZ plane
    { vertices: [2, 6, 3, 7], bundle: 4 },  // YW plane
    { vertices: [4, 6, 5, 7], bundle: 5 },  // ZW plane
  ],
  bundleColors: [
    "#ff3366", // ring 0
    "#33ff66", // ring 1
    "#3366ff", // ring 2
    "#ffcc00", // ring 3
    "#ff6633", // ring 4
    "#cc33ff", // ring 5
  ],
};

// Build vertex-to-rings mapping: for each vertex, which ring indices contain it
export function buildVertexToRings(polytope) {
  const map = new Array(polytope.vertices.length).fill(null).map(() => []);
  polytope.rings.forEach((ring, ringIdx) => {
    ring.vertices.forEach(vIdx => {
      map[vIdx].push(ringIdx);
    });
  });
  return map;
}
