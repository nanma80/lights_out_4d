// game.js — Game state management

import { buildVertexToRings } from './polytopes.js';


export class Game {
  constructor(polytope) {
    this.polytope = polytope;
    this.vertexToRings = buildVertexToRings(polytope);
    this.ringStates = new Array(polytope.rings.length).fill(false);
    this.moveCount = 0;
    this.isChallenge = false;
    this.hasWon = false;
    this.onStateChange = null;
    this.onWin = null;
  }

  clickVertex(vertexIndex) {
    const ringIndices = this.vertexToRings[vertexIndex];
    ringIndices.forEach(ri => {
      this.ringStates[ri] = !this.ringStates[ri];
    });
    this.moveCount++;
    if (this.onStateChange) this.onStateChange();
    if (this.isChallenge && !this.hasWon) this.checkWin();
  }

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
    if (this.ringStates.every(s => !s)) {
      return this.scramble(numClicks);
    }
    this.moveCount = 0;
    this.isChallenge = true;
    this.hasWon = false;
    if (this.onStateChange) this.onStateChange();
  }

  reset() {
    this.ringStates.fill(false);
    this.moveCount = 0;
    this.isChallenge = false;
    this.hasWon = false;
    if (this.onStateChange) this.onStateChange();
  }

  checkWin() {
    const allOff = this.ringStates.every(s => !s);
    const allOn = this.ringStates.every(s => s);
    if (allOff && this.onWin) {
      this.hasWon = true;
      this.onWin('off');
    } else if (allOn && this.onWin) {
      this.hasWon = true;
      this.onWin('on');
    }
  }
}
