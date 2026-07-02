// overlays/OverlayVentExt.jsx — Particules de vent extérieur
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

const PARTICLES = Array.from({ length: 14 }, (_, i) => ({
  id: i,
  y:     (i * 29 + 8) % 95,
  delay: (i * 23) % 100,
  speed: 0.4 + (i % 5) * 0.15,
  opacity: 0.2 + (i % 4) * 0.1,
  size: 2 + (i % 3),
  length: 12 + (i % 5) * 6,
}));

export function OverlayVentExt({ intensite, frame, fps }) {
  const baseOpacity = [0, 0.5, 0.8, 1.0][intensite] || 0.8;
  const cycleFps = fps * 1.8;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {PARTICLES.map(p => {
        const t = ((frame * p.speed + p.delay) % cycleFps) / cycleFps;
        const x = interpolate(t, [0, 1], [-5, 108]);
        return (
          <div key={p.id} style={{
            position: "absolute",
            left: `${x}%`,
            top: `${p.y}%`,
            width: `${p.length}px`,
            height: `${p.size}px`,
            background: "rgba(200, 220, 240, 0.6)",
            borderRadius: "2px",
            transform: "rotate(-8deg)",
            opacity: p.opacity * baseOpacity,
          }} />
        );
      })}
    </AbsoluteFill>
  );
}
