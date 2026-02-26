// game.js — Game state management

import { buildVertexToRings } from './polytopes.js';


export class Game {
  constructor(polytope) {
    this.polytope = polytope;
    this.vertexToRings = buildVertexToRings(polytope);
    this.ringStates = new Array(polytope.rings.length).fill(false); // false = OFF
    this.moveCount = 0;
    this.onStateChange = null; // callback
    this.onWin = null; // callback
  }

  // Toggle all rings passing through a vertex
  clickVertex(vertexIndex) {
    const ringIndices = this.vertexToRings[vertexIndex];
    ringIndices.forEach(ri => {
      this.ringStates[ri] = !this.ringStates[ri];
    });
    this.moveCount++;
    if (this.onStateChange) this.onStateChange();
    this.checkWin();
  }

  // Scramble by simulating N random vertex clicks from all-OFF state
  scramble(numClicks) {
    this.reset();
    const numVertices = this.polytope.vertices.length;
    for (let i = 0; i < numClicks; i++) {
      const vi = Math.floor(Math.random() * numVertices);
      const ringIndices = this.vertexToRings[vi];
      ringIndices.forEach(ri => {
        this.ringStates[ri] = !this.ringStates[ri];
      });
    }
    // Ensure at least one ring is ON (avoid trivially solved scramble)
    if (this.ringStates.every(s => !s)) {
      return this.scramble(numClicks);
    }
    this.moveCount = 0;
    if (this.onStateChange) this.onStateChange();
  }

  // Reset all rings to OFF
  reset() {
    this.ringStates.fill(false);
    this.moveCount = 0;
    if (this.onStateChange) this.onStateChange();
  }

  checkWin() {
    const allOff = this.ringStates.every(s => !s);
    const allOn = this.ringStates.every(s => s);
    if (allOff && this.onWin) {
      this.onWin('off');
    } else if (allOn && this.onWin) {
      this.onWin('on');
    }
  }
}
