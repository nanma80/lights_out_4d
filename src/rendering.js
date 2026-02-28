// rendering.js — Three.js scene, ring tubes, vertex spheres

import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { stereographicProject, projectArc } from './math4d.js?v=10';

const OFF_COLOR = 0x888888;
const OFF_OPACITY = 0.7;
const VERTEX_COLOR = 0xffffff;
const VERTEX_RADIUS = 0.12;
const RING_TUBE_RADIUS = 0.03;
const ARC_SEGMENTS = 48;
const RADIAL_SEGMENTS = 8;
const DEFAULT_CAMERA_DISTANCE = 5;

// Build tube geometry data (positions + normals) without creating a THREE.BufferGeometry.
// Returns { positions: Float32Array, normals: Float32Array, uvs: Float32Array, indices: Uint16Array }
function buildTubeData(curvePoints, radius, tubularSegments, radialSegments) {
  const numVerts = (tubularSegments + 1) * (radialSegments + 1);
  const positions = new Float32Array(numVerts * 3);
  const normals = new Float32Array(numVerts * 3);
  const uvs = new Float32Array(numVerts * 2);

  // Compute Frenet-like frames along the curve
  const tangents = [];
  for (let i = 0; i <= tubularSegments; i++) {
    let next, prev;
    if (i === 0) {
      prev = curvePoints[0];
      next = curvePoints[1];
    } else if (i === tubularSegments) {
      prev = curvePoints[tubularSegments - 1];
      next = curvePoints[tubularSegments];
    } else {
      prev = curvePoints[i - 1];
      next = curvePoints[i + 1];
    }
    const tx = next[0] - prev[0], ty = next[1] - prev[1], tz = next[2] - prev[2];
    const tLen = Math.sqrt(tx * tx + ty * ty + tz * tz) || 1;
    tangents.push([tx / tLen, ty / tLen, tz / tLen]);
  }

  // Build initial normal/binormal using minimum rotation
  let normal = [0, 0, 0];
  const t0 = tangents[0];
  const smallest = Math.abs(t0[0]) <= Math.abs(t0[1]) && Math.abs(t0[0]) <= Math.abs(t0[2]) ? 0
    : Math.abs(t0[1]) <= Math.abs(t0[2]) ? 1 : 2;
  normal[smallest] = 1;
  // n = normalize(normal - dot(normal,t)*t)
  const d = normal[0] * t0[0] + normal[1] * t0[1] + normal[2] * t0[2];
  normal[0] -= d * t0[0]; normal[1] -= d * t0[1]; normal[2] -= d * t0[2];
  let nLen = Math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) || 1;
  normal[0] /= nLen; normal[1] /= nLen; normal[2] /= nLen;

  let binormal = [
    t0[1] * normal[2] - t0[2] * normal[1],
    t0[2] * normal[0] - t0[0] * normal[2],
    t0[0] * normal[1] - t0[1] * normal[0],
  ];

  let idx = 0, uvIdx = 0;
  for (let i = 0; i <= tubularSegments; i++) {
    const P = curvePoints[Math.min(i, curvePoints.length - 1)];

    // Propagate frame via parallel transport
    if (i > 0) {
      const t1 = tangents[i - 1], t2 = tangents[i];
      const crossX = t1[1] * t2[2] - t1[2] * t2[1];
      const crossY = t1[2] * t2[0] - t1[0] * t2[2];
      const crossZ = t1[0] * t2[1] - t1[1] * t2[0];
      const crossLen = Math.sqrt(crossX ** 2 + crossY ** 2 + crossZ ** 2);
      if (crossLen > 1e-10) {
        const dot12 = t1[0] * t2[0] + t1[1] * t2[1] + t1[2] * t2[2];
        const angle = Math.acos(Math.max(-1, Math.min(1, dot12)));
        const ax = crossX / crossLen, ay = crossY / crossLen, az = crossZ / crossLen;
        const c = Math.cos(angle), s = Math.sin(angle), oc = 1 - c;
        // Rodrigues' rotation of normal
        const nx = normal[0], ny = normal[1], nz = normal[2];
        normal[0] = (c + ax * ax * oc) * nx + (ax * ay * oc - az * s) * ny + (ax * az * oc + ay * s) * nz;
        normal[1] = (ay * ax * oc + az * s) * nx + (c + ay * ay * oc) * ny + (ay * az * oc - ax * s) * nz;
        normal[2] = (az * ax * oc - ay * s) * nx + (az * ay * oc + ax * s) * ny + (c + az * az * oc) * nz;
      }
      const t = tangents[i];
      binormal = [
        t[1] * normal[2] - t[2] * normal[1],
        t[2] * normal[0] - t[0] * normal[2],
        t[0] * normal[1] - t[1] * normal[0],
      ];
    }

    for (let j = 0; j <= radialSegments; j++) {
      const v = (j / radialSegments) * Math.PI * 2;
      const sinV = Math.sin(v), cosV = -Math.cos(v);
      const nx = cosV * normal[0] + sinV * binormal[0];
      const ny = cosV * normal[1] + sinV * binormal[1];
      const nz = cosV * normal[2] + sinV * binormal[2];
      positions[idx] = P[0] + radius * nx;
      positions[idx + 1] = P[1] + radius * ny;
      positions[idx + 2] = P[2] + radius * nz;
      normals[idx] = nx;
      normals[idx + 1] = ny;
      normals[idx + 2] = nz;
      idx += 3;
      uvs[uvIdx] = i / tubularSegments;
      uvs[uvIdx + 1] = j / radialSegments;
      uvIdx += 2;
    }
  }

  // Build indices
  const numIndices = tubularSegments * radialSegments * 6;
  const indices = new Uint16Array(numIndices);
  let ii = 0;
  for (let i = 0; i < tubularSegments; i++) {
    for (let j = 0; j < radialSegments; j++) {
      const a = i * (radialSegments + 1) + j;
      const b = a + radialSegments + 1;
      indices[ii++] = a; indices[ii++] = b; indices[ii++] = a + 1;
      indices[ii++] = b; indices[ii++] = b + 1; indices[ii++] = a + 1;
    }
  }

  return { positions, normals, uvs, indices };
}

export class Renderer {
  constructor(container) {
    this.scene = new THREE.Scene();
    this.defaultBgColor = new THREE.Color(0x0a0a0a);
    this.scene.background = this.defaultBgColor.clone();

    this.camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    this.camera.position.set(0, 0, 5);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(this.renderer.domElement);

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 5, 5);
    this.scene.add(dirLight);

    this.vertexMeshes = [];
    this.ringMeshes = [];
    this._vertexPool = [];
    this._edgePool = [];
    this.ringGroup = new THREE.Group();
    this.vertexGroup = new THREE.Group();
    this.scene.add(this.ringGroup);
    this.scene.add(this.vertexGroup);

    this.container = container;
    this._handleResize = this._handleResize.bind(this);
    window.addEventListener('resize', this._handleResize);
  }

  get domElement() {
    return this.renderer.domElement;
  }

  _handleResize() {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  // Build meshes for a polytope with given 4D rotation applied
  buildPolytope(polytope, rotatedVertices4D, ringStates, cameraDistance) {
    const scale = (cameraDistance || DEFAULT_CAMERA_DISTANCE) / DEFAULT_CAMERA_DISTANCE;
    const vertexScale = (polytope.name === '600-cell' || polytope.name === 'bicont') ? 0.83 : 1;
    const tubeScale = (polytope.name === '600-cell' || polytope.name === 'bicont') ? 0.75 : 1;
    const vertexRadius = VERTEX_RADIUS * scale * vertexScale;
    const tubeRadius = RING_TUBE_RADIUS * scale * tubeScale;

    // Project vertices
    const projected = rotatedVertices4D.map(v => stereographicProject(v));

    // Count total edges needed
    let totalEdges = 0;
    polytope.rings.forEach(ring => { totalEdges += ring.vertices.length; });

    // Grow vertex pool if needed
    while (this._vertexPool.length < projected.length) {
      const geo = new THREE.SphereGeometry(vertexRadius, 16, 16);
      const mat = new THREE.MeshPhongMaterial({
        color: VERTEX_COLOR,
        emissive: 0x444444,
        emissiveIntensity: 0.5,
      });
      const mesh = new THREE.Mesh(geo, mat);
      this.vertexGroup.add(mesh);
      this._vertexPool.push(mesh);
    }

    // Update vertex positions and visibility
    for (let i = 0; i < this._vertexPool.length; i++) {
      const mesh = this._vertexPool[i];
      if (i < projected.length) {
        mesh.position.set(projected[i][0], projected[i][1], projected[i][2]);
        mesh.scale.setScalar(vertexRadius / VERTEX_RADIUS);
        mesh.userData.vertexIndex = i;
        mesh.visible = true;
      } else {
        mesh.visible = false;
      }
    }
    this.vertexMeshes = this._vertexPool.slice(0, projected.length);

    // Grow edge pool if needed
    while (this._edgePool.length < totalEdges) {
      const geo = new THREE.BufferGeometry();
      const mat = new THREE.MeshPhongMaterial();
      const mesh = new THREE.Mesh(geo, mat);
      this.ringGroup.add(mesh);
      this._edgePool.push(mesh);
    }

    // Update ring tubes
    let edgeIdx = 0;
    this.ringMeshes = [];
    polytope.rings.forEach((ring, ringIdx) => {
      const isOn = ringStates[ringIdx];
      const color = isOn
        ? new THREE.Color(polytope.bundleColors[ring.bundle])
        : new THREE.Color(OFF_COLOR);
      const opacity = isOn ? 1.0 : OFF_OPACITY;

      const edgeMeshes = [];
      const verts = ring.vertices;

      for (let e = 0; e < verts.length; e++) {
        const i1 = verts[e];
        const i2 = verts[(e + 1) % verts.length];

        const arcPoints3D = projectArc(
          rotatedVertices4D[i1],
          rotatedVertices4D[i2],
          ARC_SEGMENTS
        );

        // Sample the CatmullRom curve to get evenly-spaced points
        const curve = new THREE.CatmullRomCurve3(
          arcPoints3D.map(p => new THREE.Vector3(p[0], p[1], p[2]))
        );
        const curvePoints = [];
        for (let s = 0; s <= ARC_SEGMENTS; s++) {
          const pt = curve.getPoint(s / ARC_SEGMENTS);
          curvePoints.push([pt.x, pt.y, pt.z]);
        }

        // Generate tube data without creating any Three.js geometry object
        const tubeData = buildTubeData(curvePoints, tubeRadius, ARC_SEGMENTS, RADIAL_SEGMENTS);
        const mesh = this._edgePool[edgeIdx];
        const poolGeo = mesh.geometry;

        if (!poolGeo.attributes.position) {
          poolGeo.setAttribute('position', new THREE.BufferAttribute(tubeData.positions, 3));
          poolGeo.setAttribute('normal', new THREE.BufferAttribute(tubeData.normals, 3));
          poolGeo.setAttribute('uv', new THREE.BufferAttribute(tubeData.uvs, 2));
          poolGeo.setIndex(new THREE.BufferAttribute(tubeData.indices, 1));
        } else {
          poolGeo.attributes.position.array.set(tubeData.positions);
          poolGeo.attributes.position.needsUpdate = true;
          poolGeo.attributes.normal.array.set(tubeData.normals);
          poolGeo.attributes.normal.needsUpdate = true;
        }
        poolGeo.computeBoundingSphere();

        // Update material
        mesh.material.color.set(color);
        mesh.material.transparent = !isOn;
        mesh.material.opacity = opacity;
        mesh.material.emissive.set(isOn ? color : new THREE.Color(0x000000));
        mesh.material.emissiveIntensity = isOn ? 0.5 : 0;
        mesh.material.needsUpdate = true;
        mesh.visible = true;

        edgeMeshes.push(mesh);
        edgeIdx++;
      }

      this.ringMeshes.push(edgeMeshes);
    });

    // Hide excess edge meshes
    for (let i = edgeIdx; i < this._edgePool.length; i++) {
      this._edgePool[i].visible = false;
    }
  }

  // Update ring visuals without rebuilding geometry
  updateRingStates(polytope, ringStates) {
    polytope.rings.forEach((ring, ringIdx) => {
      const isOn = ringStates[ringIdx];
      const color = isOn
        ? new THREE.Color(polytope.bundleColors[ring.bundle])
        : new THREE.Color(OFF_COLOR);
      const opacity = isOn ? 1.0 : OFF_OPACITY;

      if (this.ringMeshes[ringIdx]) {
        this.ringMeshes[ringIdx].forEach(mesh => {
          mesh.material.color.copy(color);
          mesh.material.transparent = !isOn;
          mesh.material.opacity = opacity;
          mesh.material.emissive.copy(isOn ? color : new THREE.Color(0x000000));
          mesh.material.emissiveIntensity = isOn ? 0.5 : 0;
          mesh.material.needsUpdate = true;
        });
      }
    });
  }

  setBackgroundColor(hex) {
    this.scene.background = new THREE.Color(hex);
  }

  resetBackground() {
    this.scene.background = this.defaultBgColor.clone();
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }
}
