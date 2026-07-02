// overlays/OverlayNeonsInt.jsx — Néons fluorescents intérieurs
import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

export function OverlayNeonsInt({ intensite, frame, fps }) {
  const cycle = fps * 3; // période 3s
  const t = frame % cycle;

  // Flicker : court flash d'extinction aléatoire simulé par interpolation
  const flicker1 = interpolate(t, [0, 4, 5, 9, 10, cycle], [1, 1, 0.3, 1, 0.85, 1], { extrapolateRight: "clamp" });
  const flicker2 = interpolate(t, [0, cycle * 0.4, cycle * 0.41, cycle * 0.45, cycle], [1, 1, 0.5, 1, 1], { extrapolateRight: "clamp" });
  const flicker  = Math.min(flicker1, flicker2);

  const baseOpacity = [0, 0.32, 0.48, 0.65][intensite] || 0.48;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Barre néon haut gauche */}
      <div style={{
        position: "absolute",
        top: "4%",
        left: "5%",
        width: "38%",
        height: "6px",
        background: "rgba(180, 240, 255, 0.9)",
        boxShadow: `0 0 12px 4px rgba(140, 220, 255, 0.8), 0 0 40px 10px rgba(100, 200, 255, 0.4)`,
        borderRadius: "3px",
        opacity: baseOpacity * flicker,
      }} />

      {/* Barre néon haut droite */}
      <div style={{
        position: "absolute",
        top: "4%",
        right: "5%",
        width: "30%",
        height: "6px",
        background: "rgba(180, 240, 255, 0.9)",
        boxShadow: `0 0 12px 4px rgba(140, 220, 255, 0.8), 0 0 40px 10px rgba(100, 200, 255, 0.4)`,
        borderRadius: "3px",
        opacity: baseOpacity * flicker * 0.85,
      }} />

      {/* Cône de lumière descendant */}
      <div style={{
        position: "absolute",
        top: "5%",
        left: "15%",
        width: "70%",
        height: "55%",
        background: "linear-gradient(to bottom, rgba(160, 220, 255, 0.12), rgba(160, 220, 255, 0.0))",
        clipPath: "polygon(20% 0%, 80% 0%, 100% 100%, 0% 100%)",
        opacity: baseOpacity * flicker,
      }} />
    </AbsoluteFill>
  );
}
