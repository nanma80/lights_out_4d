# Copilot Instructions for Lights Out 4D

## Project Overview
This is a browser-based puzzle game where players interact with a stereographic projection of 4D polytopes. Read `spec.md` at the repo root before making any changes — it is the source of truth for design decisions.

## Key Architecture
- **No build step.** Plain HTML/CSS/JS. Three.js loaded from CDN.
- **Polytopes are data.** Adding a new polytope (24-cell, 600-cell) means adding a new data object in `src/polytopes.js` following the existing format (vertices, rings, bundleColors).
- **Game state lives on rings, not vertices.** Clicking a vertex toggles all rings passing through it.
- **Two separate rotation systems**: 3D camera (trackball, drag) and 4D polytope rotation (scroll/pinch). Don't conflate them.

## Important Constraints
- No gimbal lock on 3D camera — quaternion-based trackball, no OrbitControls.
- Scroll/pinch is reserved for 4D rotation, NOT zoom. Zoom uses UI buttons.
- No auto-rotation. The view stays where the player leaves it.
- All UI elements must be ≥ 44×44px for touch targets.
- Must work on PC browsers, iPhone Safari, and Android Chrome.

## Testing
- Run `python -m http.server 8080` from repo root to test locally.
- Test on mobile via local network IP on same WiFi.
- Deployed to GitHub Pages at https://nanma80.github.io/lights_out_4d
