// src/components/Scene.jsx — F03 SIGISMUND
// Rendu d'un segment : image (Ken Burns) + overlay + sous-titre.
// Support dual format : PNG, JPEG, JPG (fallback automatique).
import React, { useState, useEffect } from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Subtitle } from "./Subtitle";
import { OverlayDispatch } from "./overlays/OverlayDispatch";

// ── Helper : résout le chemin d'image avec fallback d'extension ──
// Essaie .png → .jpeg → .jpg dans public/images/
function resolveImagePath(imageFile) {
  if (!imageFile) return null;
  const baseName = imageFile.replace(/\.(png|jpe?g)$/i, "");
  const candidates = [`${baseName}.png`, `${baseName}.jpeg`, `${baseName}.jpg`];
  for (const c of candidates) {
    try {
      // staticFile throws if file doesn't exist in public/
      const resolved = staticFile(`images/${c}`);
      return resolved;
    } catch (e) {
      // continue to next candidate
    }
  }
  // Fallback : return the original (let Remotion handle the error)
  return staticFile(`images/${imageFile}`);
}

export const Scene = ({ segment, timingSeg, style, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Ken Burns : très léger zoom + dérive horizontale ──────────
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(frame, [0, durationInFrames], [0, -10], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Intensité effective : min(segment, global) ────────────────
  const effectiveIntensity = Math.min(
    segment.overlay_intensite ?? 2,
    style.overlay_global_intensity ?? 3
  );

  // ── Résolution du chemin d'image (dual format) ────────────────
  const imgSrc = resolveImagePath(segment.image_file);

  return (
    <AbsoluteFill>
      {/* Image de fond du segment */}
      {imgSrc && (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={imgSrc}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale}) translateX(${translateX}px)`,
              transformOrigin: "center center",
            }}
          />
        </AbsoluteFill>
      )}

      {/* Overlay atmosphérique */}
      <OverlayDispatch
        type={segment.overlay_type || "defaut"}
        intensite={effectiveIntensity}
        frame={frame}
        fps={fps}
      />

      {/* Sous-titre */}
      <Subtitle
        segment={segment}
        timingSeg={timingSeg}
        style={style}
        durationInFrames={durationInFrames}
      />
    </AbsoluteFill>
  );
};
