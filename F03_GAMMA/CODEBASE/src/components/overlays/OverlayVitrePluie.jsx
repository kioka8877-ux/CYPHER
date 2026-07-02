// overlays/OverlayVitrePluie.jsx — Pluie clippée dans la zone fenêtre
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

const DROPS = Array.from({ length: 28 }, (_, i) => ({
  id: i,
  x:     (i * 41 + 5) % 95,
  delay: (i * 19) % 100,
  speed: 0.5 + (i % 4) * 0.15,
  opacity: 0.35 + (i % 3) * 0.15,
  width: 1 + (i % 2) * 0.5,
  height: 8 + (i % 5) * 4,
}));

export function OverlayVitrePluie({ intensite, frame, fps }) {
  const baseOpacity = [0, 0.55, 0.8, 1.0][intensite] || 0.8;
  const cycleFps = fps * 1.3;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Zone fenêtre — pluie clippée ici */}
      <div style={{
        position: "absolute",
        top: "17%",
        left: "5%",
        width: "90%",
        height: "39%",
        overflow: "hidden",
        borderRadius: "2px",
      }}>
        {/* Fond de ciel gris extérieur */}
        <div style={{
          position: "absolute", inset: 0,
          background: "linear-gradient(to bottom, rgba(80, 95, 115, 0.22), rgba(60, 75, 95, 0.1))",
          opacity: baseOpacity,
        }} />

        {/* Gouttes clippées */}
        {DROPS.map(drop => {
          const t = ((frame * drop.speed + drop.delay) % cycleFps) / cycleFps;
          const y = interpolate(t, [0, 1], [-5, 108]);
          return (
            <div key={drop.id} style={{
              position: "absolute",
              left: `${drop.x}%`,
              top: `${y}%`,
              width: `${drop.width}px`,
              height: `${drop.height}px`,
              background: "rgba(180, 210, 240, 0.75)",
              borderRadius: "1px",
              transform: "rotate(-10deg)",
              opacity: drop.opacity * baseOpacity,
            }} />
          );
        })}

        {/* Condensation sur les bords */}
        <div style={{
          position: "absolute", inset: 0,
          background: "linear-gradient(to bottom, rgba(200, 220, 240, 0.08) 0%, transparent 30%, transparent 70%, rgba(200, 220, 240, 0.08) 100%)",
          opacity: baseOpacity,
        }} />
      </div>
    </AbsoluteFill>
  );
}
