// src/components/Scene.jsx — F03 SIGISMUND
// Rendu d'un segment : image (Ken Burns) + overlay + sous-titre.
import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Subtitle } from "./Subtitle";
import { OverlayDispatch } from "./overlays/OverlayDispatch";

export const Scene = ({ segment, timingSeg, style, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Ken Burns : très léger zoom + dérive horizontale ──────────────────────
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateX = interpolate(frame, [0, durationInFrames], [0, -10], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Intensité effective : min(segment, global) ─────────────────────────────
  // Gemini assigne une intensité par image (1-3).
  // overlay_global_intensity dans le style plafonne toutes les intensités.
  const effectiveIntensity = Math.min(
    segment.overlay_intensite ?? 2,
    style.overlay_global_intensity ?? 3
  );

  return (
    <AbsoluteFill>
      {/* Image de fond du segment */}
      {segment.image_file && (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img
            src={staticFile(`images/${segment.image_file}`)}
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
