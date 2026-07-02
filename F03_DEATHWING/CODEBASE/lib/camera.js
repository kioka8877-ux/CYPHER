/**
 * camera.js — Camera interpolation for CYPHER DEATHWING
 * Uses jumpTo() with manual ease-in-out-cubic interpolation.
 * flyTo() is FORBIDDEN in CI (non-deterministic timing).
 */
'use strict';

function easeInOutCubic(t) {
  return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3) / 2;
}

function lerp(a, b, t) { return a + (b-a) * t; }

function getCameraState(from, to, t, duration) {
  const p = Math.min(t / duration, 1.0);
  const e = easeInOutCubic(p);
  return {
    center: [lerp(from.lon, to.lon, e), lerp(from.lat, to.lat, e)],
    zoom: lerp(from.zoom, to.zoom, e),
    pitch: lerp(from.pitch || 0, to.pitch || 25, e),
    bearing: 0
  };
}

function applyCameraState(map, state) {
  map.jumpTo(state);
}

module.exports = { easeInOutCubic, lerp, getCameraState, applyCameraState };
