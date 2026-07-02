/**
 * subtitles.js — Word-by-word subtitle sync
 * Each word appears synchronized with its word_frame in the render_spec.
 * Style: Impact font, #a3f609, text-shadow for readability.
 */
'use strict';

function updateSubtitles(container, seg, timeS, fps, fontColor) {
  const words = (seg.text || '').split(/\s+/).filter(Boolean);
  if (!words.length) { container.innerHTML = ''; return; }

  if (container.dataset.segId !== String(seg.id)) {
    container.dataset.segId = String(seg.id);
    container.innerHTML = '';
    words.forEach(w => {
      const span = document.createElement('span');
      span.className = 'subtitle-word';
      span.textContent = w;
      span.style.color = fontColor || '#a3f609';
      container.appendChild(span);
    });
  }

  const segDur = seg.end - seg.start;
  const tIn = timeS - seg.start;
  const n = Math.floor((tIn / segDur) * words.length);
  container.querySelectorAll('.subtitle-word').forEach((el, i) => {
    el.classList.toggle('visible', i < n);
  });
}

module.exports = { updateSubtitles };
