// main.js — Entry point, wires everything together

import { POLYTOPE_16CELL } from './polytopes.js';
import { rotate4D } from './math4d.js';
import { Renderer } from './rendering.js';
import { Trackball, Rotation4D, ClickHandler } from './controls.js';
import { Game } from './game.js';

const container = document.getElementById('canvas-container');
const moveCountEl = document.getElementById('move-count');
const scrambleBtn = document.getElementById('btn-scramble');
const resetBtn = document.getElementById('btn-reset');
const zoomInBtn = document.getElementById('btn-zoom-in');
const zoomOutBtn = document.getElementById('btn-zoom-out');
const winOverlay = document.getElementById('win-overlay');
const winMessage = document.getElementById('win-message');
const winMoves = document.getElementById('win-moves');
const winScrambleBtn = document.getElementById('win-scramble');

// State
let currentPolytope = POLYTOPE_16CELL;
let renderer, trackball, rotation4d, clickHandler, game;
let rotatedVertices = [];

function getRotatedVertices() {
  return currentPolytope.vertices.map(v => rotate4D(v, rotation4d.matrix));
}

function rebuildScene() {
  rotatedVertices = getRotatedVertices();
  renderer.buildPolytope(currentPolytope, rotatedVertices, game.ringStates);
  clickHandler.updateMeshes(renderer.vertexMeshes);
}

function updateVisuals() {
  renderer.updateRingStates(currentPolytope, game.ringStates);
  moveCountEl.textContent = game.moveCount;

  // Sync background color with ring state
  const allOff = game.ringStates.every(s => !s);
  const allOn = game.ringStates.every(s => s);
  if (allOff) {
    renderer.setBackgroundColor(0x0a0a3a);
  } else if (allOn) {
    renderer.setBackgroundColor(0x3a2a0a);
  } else {
    renderer.resetBackground();
  }
}

function showWin(type) {
  if (type === 'off') {
    winMessage.textContent = 'Lights Out! 🎉';
    renderer.setBackgroundColor(0x0a0a3a);
  } else {
    winMessage.textContent = 'All Lit Up! ✨';
    document.getElementById('win-subtitle').textContent = 'Now try turning them all off!';
    renderer.setBackgroundColor(0x3a2a0a);
  }
  winMoves.textContent = `Moves: ${game.moveCount}`;
  winOverlay.classList.add('visible');
}

function hideWin() {
  winOverlay.classList.remove('visible');
  renderer.resetBackground();
}

function init() {
  renderer = new Renderer(container);
  trackball = new Trackball(renderer.camera, renderer.domElement);
  rotation4d = new Rotation4D();
  game = new Game(currentPolytope);

  clickHandler = new ClickHandler(
    renderer.camera,
    renderer.domElement,
    [],
    (vertexIndex) => {
      hideWin();
      game.clickVertex(vertexIndex);
      updateVisuals();
    }
  );

  game.onStateChange = updateVisuals;
  game.onWin = showWin;

  rotation4d.onChange = () => {
    rebuildScene();
  };

  // Mouse click detection (after drag check)
  renderer.domElement.addEventListener('mouseup', (e) => {
    if (trackball.wasClick) {
      clickHandler.testClick(e.clientX, e.clientY);
    }
  });

  // Touch tap detection
  let touchStartPos = null;
  renderer.domElement.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      touchStartPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
  }, { passive: true });

  renderer.domElement.addEventListener('touchend', (e) => {
    if (trackball.wasClick && touchStartPos) {
      clickHandler.testClick(touchStartPos.x, touchStartPos.y);
    }
    touchStartPos = null;
  }, { passive: true });

  // Scroll → 4D rotation
  renderer.domElement.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    const viewDir = trackball.getViewDirection();
    rotation4d.rotate(viewDir, delta);
  }, { passive: false });

  // Pinch → 4D rotation
  let lastPinchDist = null;
  let wasPinching = false;

  renderer.domElement.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
      // Starting a pinch — disable trackball drag
      trackball._isDragging = false;
      wasPinching = true;
    }
  }, { passive: true });

  renderer.domElement.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      wasPinching = true;
      trackball._isDragging = false;
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (lastPinchDist !== null) {
        const delta = (dist - lastPinchDist) * 0.02;
        const viewDir = trackball.getViewDirection();
        rotation4d.rotate(viewDir, delta);
      }
      lastPinchDist = dist;
    }
  }, { passive: false });

  renderer.domElement.addEventListener('touchend', (e) => {
    if (e.touches.length < 2) {
      lastPinchDist = null;
    }
    if (e.touches.length <= 1 && wasPinching) {
      // Transitioning out of pinch — reset trackball state to prevent jump
      wasPinching = false;
      trackball._isDragging = false;
      if (e.touches.length === 1) {
        // One finger remains — reset trackball's prev position
        trackball._prevX = e.touches[0].clientX;
        trackball._prevY = e.touches[0].clientY;
      }
    }
  });

  // UI buttons
  scrambleBtn.addEventListener('click', () => {
    hideWin();
    game.scramble(4);
  });

  resetBtn.addEventListener('click', () => {
    hideWin();
    game.reset();
  });

  zoomInBtn.addEventListener('click', () => trackball.zoom(-0.5));
  zoomOutBtn.addEventListener('click', () => trackball.zoom(0.5));

  winScrambleBtn.addEventListener('click', () => {
    hideWin();
    game.scramble(4);
  });

  winOverlay.addEventListener('click', (e) => {
    if (e.target === winOverlay) hideWin();
  });

  // Initial state
  rebuildScene();
  game.scramble(4);

  // Animation loop
  function animate() {
    requestAnimationFrame(animate);
    renderer.render();
  }
  animate();
}

init();
