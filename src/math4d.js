// math4d.js — 4D math: rotation matrices and stereographic projection

// Stereographic projection from S³ to R³
// Projects from south pole (0,0,0,-1) onto hyperplane w=0
// Given point (x,y,z,w) on S³: X = x/(1+w), Y = y/(1+w), Z = z/(1+w)
export function stereographicProject(point4d) {
  const [x, y, z, w] = point4d;
  const denom = 1 + w;
  const MAX_RADIUS = 100;
  if (Math.abs(denom) < 1e-10) {
    const len = Math.sqrt(x * x + y * y + z * z);
    if (len < 1e-10) return [MAX_RADIUS, 0, 0];
    const s = MAX_RADIUS / len;
    return [x * s, y * s, z * s];
  }
  const projected = [x / denom, y / denom, z / denom];
  const r2 = projected[0] ** 2 + projected[1] ** 2 + projected[2] ** 2;
  if (r2 > MAX_RADIUS * MAX_RADIUS) {
    const s = MAX_RADIUS / Math.sqrt(r2);
    return [projected[0] * s, projected[1] * s, projected[2] * s];
  }
  return projected;
}

// Apply a 4x4 rotation matrix to a 4D point
export function rotate4D(point, matrix) {
  const result = [0, 0, 0, 0];
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      result[i] += matrix[i][j] * point[j];
    }
  }
  return result;
}

// Build a 4D rotation matrix in a given plane by angle (radians)
// plane is specified by two axis indices (0=x, 1=y, 2=z, 3=w)
export function rotationMatrix4D(axis1, axis2, angle) {
  const m = [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ];
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  m[axis1][axis1] = c;
  m[axis1][axis2] = -s;
  m[axis2][axis1] = s;
  m[axis2][axis2] = c;
  return m;
}

// Multiply two 4x4 matrices
export function multiplyMatrices4D(a, b) {
  const result = Array.from({ length: 4 }, () => [0, 0, 0, 0]);
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      for (let k = 0; k < 4; k++) {
        result[i][j] += a[i][k] * b[k][j];
      }
    }
  }
  return result;
}

// Identity 4x4 matrix
export function identity4D() {
  return [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ];
}

// Interpolate points along a great circle arc on S³ between two points
// Returns an array of 4D points (including start and end)
export function greatCircleArc(p1, p2, numSegments = 32) {
  // Compute the angle between p1 and p2 on S³
  let dot = 0;
  for (let i = 0; i < 4; i++) dot += p1[i] * p2[i];
  dot = Math.max(-1, Math.min(1, dot)); // clamp for numerical safety
  const angle = Math.acos(dot);

  if (angle < 1e-10) {
    return [p1, p2];
  }

  const points = [];
  const sinAngle = Math.sin(angle);
  for (let i = 0; i <= numSegments; i++) {
    const t = i / numSegments;
    const s1 = Math.sin((1 - t) * angle) / sinAngle;
    const s2 = Math.sin(t * angle) / sinAngle;
    const point = [
      s1 * p1[0] + s2 * p2[0],
      s1 * p1[1] + s2 * p2[1],
      s1 * p1[2] + s2 * p2[2],
      s1 * p1[3] + s2 * p2[3],
    ];
    points.push(point);
  }
  return points;
}

// Project a great circle arc from S³ to R³ via stereographic projection
export function projectArc(p1_4d, p2_4d, numSegments = 32) {
  const arc4d = greatCircleArc(p1_4d, p2_4d, numSegments);
  return arc4d.map(p => stereographicProject(p));
}
