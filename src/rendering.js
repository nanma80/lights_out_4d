// rendering.js — Three.js scene, ring tubes, vertex spheres

import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { stereographicProject, projectArc } from './math4d.js';

const OFF_COLOR = 0x888888;
const OFF_OPACITY = 0.7;
const VERTEX_COLOR = 0xffffff;
const VERTEX_RADIUS = 0.12;
const RING_TUBE_RADIUS = 0.03;
const ARC_SEGMENTS = 48;
const DEFAULT_CAMERA_DISTANCE = 5;

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
    this.ringMeshes = []; // array of arrays (each ring = array of tube meshes for its edges)
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
    // Clear existing
    this.ringGroup.clear();
    this.vertexGroup.clear();
    this.vertexMeshes = [];
    this.ringMeshes = [];

    const scale = (cameraDistance || DEFAULT_CAMERA_DISTANCE) / DEFAULT_CAMERA_DISTANCE;
    const vertexRadius = VERTEX_RADIUS * scale;
    const tubeRadius = RING_TUBE_RADIUS * scale;

    // Project vertices
    const projected = rotatedVertices4D.map(v => stereographicProject(v));

    // Build vertex spheres
    const sphereGeo = new THREE.SphereGeometry(vertexRadius, 16, 16);
    const vertexMat = new THREE.MeshPhongMaterial({
      color: VERTEX_COLOR,
      emissive: 0x444444,
      emissiveIntensity: 0.5,
    });

    projected.forEach((pos, i) => {
      const mesh = new THREE.Mesh(sphereGeo, vertexMat.clone());
      mesh.position.set(pos[0], pos[1], pos[2]);
      mesh.userData.vertexIndex = i;
      this.vertexGroup.add(mesh);
      this.vertexMeshes.push(mesh);
    });

    // Build ring tubes
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

        // Get projected arc points
        const arcPoints3D = projectArc(
          rotatedVertices4D[i1],
          rotatedVertices4D[i2],
          ARC_SEGMENTS
        );

        const curve = new THREE.CatmullRomCurve3(
          arcPoints3D.map(p => new THREE.Vector3(p[0], p[1], p[2]))
        );

        const tubeGeo = new THREE.TubeGeometry(curve, ARC_SEGMENTS, tubeRadius, 8, false);
        const tubeMat = new THREE.MeshPhongMaterial({
          color: color,
          transparent: !isOn,
          opacity: opacity,
          emissive: isOn ? color : new THREE.Color(0x000000),
          emissiveIntensity: isOn ? 0.5 : 0,
        });

        const mesh = new THREE.Mesh(tubeGeo, tubeMat);
        this.ringGroup.add(mesh);
        edgeMeshes.push(mesh);
      }

      this.ringMeshes.push(edgeMeshes);
    });
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
