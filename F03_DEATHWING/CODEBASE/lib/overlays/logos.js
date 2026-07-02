/**
 * logos.js — Logo placement overlay
 * Logos are scattered within country bounds using golden-angle distribution.
 * Each logo appears at its word_frame time.
 * Logo shape: square with rounded corners.
 */
'use strict';

function scatterPositions(n, cx, cy, rLon, rLat) {
  const pos = [];
  if (n === 1) { pos.push([cx, cy]); }
  else {
    for (let i = 0; i < n; i++) {
      const a = (2 * Math.PI * i / n) - Math.PI/2;
      const r = n <= 3 ? 0.6 : 0.8;
      pos.push([cx + Math.cos(a)*rLon*r, cy + Math.sin(a)*rLat*r]);
    }
  }
  return pos;
}

function createLogoElement(brand) {
  const el = document.createElement('div');
  el.className = 'brand-marker visible';
  el.style.width = '120px';
  el.style.height = '120px';
  if (brand._logo_abs) {
    const img = document.createElement('img');
    img.src = brand._logo_abs;
    img.style.width = '90%';
    img.style.height = '90%';
    img.style.objectFit = 'contain';
    img.onerror = () => { el.innerHTML = '<div class="fallback-text">' + brand.name + '</div>'; };
    el.appendChild(img);
  } else {
    el.innerHTML = '<div class="fallback-text">' + brand.name + '</div>';
  }
  return el;
}

module.exports = { scatterPositions, createLogoElement };
