// controls.js — Trackball camera, 4D rotation via scroll/pinch, raycaster

import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { rotationMatrix4D, multiplyMatrices4D, identity4D } from './math4d.js';

// Trackball-style rotation (quaternion-based, no gimbal lock)
class Trackball {
  constructor(camera, domElement) {
    this.camera = camera;
    this.domElement = domElement;
    this.rotationSpeed = 2.0;

    this._isDragging = false;
    this._startX = 0;
    this._startY = 0;
    this._startQuaternion = new THREE.Quaternion();
    this._cameraDistance = camera.position.length();

    // Store camera state as quaternion + distance from origin
    this._quaternion = new THREE.Quaternion();
    // Start with a 3D rotation so no vertex sits dead-center
    const initRot = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(Math.PI / 2.75, Math.PI / 4, 0)
    );
    this._quaternion.copy(initRot);
    this._updateCamera();

    this._onMouseDown = this._onMouseDown.bind(this);
    this._onMouseMove = this._onMouseMove.bind(this);
    this._onMouseUp = this._onMouseUp.bind(this);
    this._onTouchStart = this._onTouchStart.bind(this);
    this._onTouchMove = this._onTouchMove.bind(this);
    this._onTouchEnd = this._onTouchEnd.bind(this);

    domElement.addEventListener('mousedown', this._onMouseDown);
    domElement.addEventListener('mousemove', this._onMouseMove);
    domElement.addEventListener('mouseup', this._onMouseUp);
    domElement.addEventListener('touchstart', this._onTouchStart, { passive: true });
    domElement.addEventListener('touchmove', this._onTouchMove, { passive: true });
    domElement.addEventListener('touchend', this._onTouchEnd, { passive: true });

    this.totalDragDistance = 0;
    this.wasClick = false;
  }

  _applyRotation(dx, dy) {
    // dx, dy are normalized screen deltas
    // Horizontal drag → rotate around camera's up vector (screen vertical axis)
    // Vertical drag → rotate around camera's right vector (screen horizontal axis)
    const up = new THREE.Vector3(0, 1, 0).applyQuaternion(this._quaternion);
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this._quaternion);

    const qx = new THREE.Quaternion().setFromAxisAngle(up, -dx * this.rotationSpeed);
    const qy = new THREE.Quaternion().setFromAxisAngle(right, -dy * this.rotationSpeed);

    this._quaternion.premultiply(qx).premultiply(qy);
    this._quaternion.normalize();
    this._updateCamera();
  }

  _onMouseDown(e) {
    if (e.button !== 0) return;
    this._isDragging = true;
    this._prevX = e.clientX;
    this._prevY = e.clientY;
    this.totalDragDistance = 0;
    this.wasClick = false;
  }

  _onMouseMove(e) {
    if (!this._isDragging) return;
    const dx = e.clientX - this._prevX;
    const dy = e.clientY - this._prevY;
    this.totalDragDistance += Math.abs(dx) + Math.abs(dy);

    const rect = this.domElement.getBoundingClientRect();
    const size = Math.min(rect.width, rect.height);
    this._applyRotation(dx / size * 2, dy / size * 2);

    this._prevX = e.clientX;
    this._prevY = e.clientY;
  }

  _onMouseUp(e) {
    if (!this._isDragging) return;
    this._isDragging = false;
    this.wasClick = this.totalDragDistance < 5;
  }

  _onTouchStart(e) {
    if (e.touches.length === 1) {
      const t = e.touches[0];
      this._isDragging = true;
      this._prevX = t.clientX;
      this._prevY = t.clientY;
      this.totalDragDistance = 0;
      this.wasClick = false;
    }
  }

  _onTouchMove(e) {
    if (e.touches.length === 1 && this._isDragging) {
      const t = e.touches[0];
      const dx = t.clientX - this._prevX;
      const dy = t.clientY - this._prevY;
      this.totalDragDistance += Math.abs(dx) + Math.abs(dy);

      const rect = this.domElement.getBoundingClientRect();
      const size = Math.min(rect.width, rect.height);
      this._applyRotation(dx / size * 2, dy / size * 2);

      this._prevX = t.clientX;
      this._prevY = t.clientY;
    }
  }

  _onTouchEnd(e) {
    if (e.touches.length === 0) {
      this._isDragging = false;
      this.wasClick = this.totalDragDistance < 10;
    }
  }

  _updateCamera() {
    const dir = new THREE.Vector3(0, 0, 1).applyQuaternion(this._quaternion);
    this.camera.position.copy(dir.multiplyScalar(this._cameraDistance));
    this.camera.up.set(0, 1, 0).applyQuaternion(this._quaternion);
    this.camera.lookAt(0, 0, 0);
  }

  zoom(delta) {
    this._cameraDistance = Math.max(2, Math.min(20, this._cameraDistance + delta));
    this._updateCamera();
  }

  // Get camera view direction (normalized, pointing from camera to origin)
  getViewDirection() {
    const dir = new THREE.Vector3();
    this.camera.getWorldDirection(dir);
    return dir;
  }
}

// 4D rotation controller — scroll/pinch drives rotation in (viewDir, W) plane
class Rotation4D {
  constructor() {
    // Start from a symmetrical 4D viewpoint: rotate cell center (1,1,1,1)/2 onto the W axis
    this.matrix = identity4D();
    // Sequential rotations: XW, YW, ZW to map (1,1,1,1)/2 → (0,0,0,1)
    const initXW = rotationMatrix4D(0, 3, Math.PI / 4);
    const initYW = rotationMatrix4D(1, 3, Math.atan(1 / Math.sqrt(2)));
    const initZW = rotationMatrix4D(2, 3, Math.PI / 6);
    this.matrix = multiplyMatrices4D(initZW, multiplyMatrices4D(initYW, multiplyMatrices4D(initXW, this.matrix)));
    this.rotationSpeed = 0.05;
    this.onChange = null;
  }

  // Rotate in the plane spanned by a 3D view direction and the W axis
  // viewDir is a THREE.Vector3 (normalized)
  rotate(viewDir, scrollDelta) {
    const angle = scrollDelta * this.rotationSpeed;

    // The view direction in 3D corresponds to (vx, vy, vz, 0) in 4D
    // We want to rotate in the plane spanned by this direction and W axis (0,0,0,1)
    // Decompose the rotation: find which combination of XW, YW, ZW planes to use
    const vx = viewDir.x;
    const vy = viewDir.y;
    const vz = viewDir.z;

    // Apply small rotations in XW, YW, ZW planes weighted by view direction components
    let result = this.matrix;

    if (Math.abs(vx) > 1e-6) {
      const m = rotationMatrix4D(0, 3, angle * vx); // XW plane
      result = multiplyMatrices4D(m, result);
    }
    if (Math.abs(vy) > 1e-6) {
      const m = rotationMatrix4D(1, 3, angle * vy); // YW plane
      result = multiplyMatrices4D(m, result);
    }
    if (Math.abs(vz) > 1e-6) {
      const m = rotationMatrix4D(2, 3, angle * vz); // ZW plane
      result = multiplyMatrices4D(m, result);
    }

    this.matrix = result;
    if (this.onChange) this.onChange();
  }

  reset() {
    this.matrix = [
      [1, 0, 0, 0],
      [0, 1, 0, 0],
      [0, 0, 1, 0],
      [0, 0, 0, 1],
    ];
    if (this.onChange) this.onChange();
  }
}

// Raycaster for vertex clicking
class ClickHandler {
  constructor(camera, domElement, vertexMeshes, onVertexClick) {
    this.camera = camera;
    this.domElement = domElement;
    this.raycaster = new THREE.Raycaster();
    this.vertexMeshes = vertexMeshes;
    this.onVertexClick = onVertexClick;
  }

  updateMeshes(meshes) {
    this.vertexMeshes = meshes;
  }

  testClick(clientX, clientY) {
    const rect = this.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1
    );

    this.raycaster.set(this.camera.position, new THREE.Vector3());
    this.raycaster.setFromCamera(mouse, this.camera);

    const intersects = this.raycaster.intersectObjects(this.vertexMeshes);
    if (intersects.length > 0) {
      const mesh = intersects[0].object;
      const vi = mesh.userData.vertexIndex;
      if (vi !== undefined && this.onVertexClick) {
        this.onVertexClick(vi);
      }
    }
  }
}

export { Trackball, Rotation4D, ClickHandler };
