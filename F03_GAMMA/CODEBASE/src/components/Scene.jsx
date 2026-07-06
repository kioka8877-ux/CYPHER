// src/components/Scene.jsx — F03 SIGISMUND (v2 — capsule + title + sinusoidal)
// Rendu d'un segment : image en capsule + overlay + sous-titre + titre état.
import React, { useState, useEffect } from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Subtitle } from "./Subtitle";
import { OverlayDispatch } from "./overlays/OverlayDispatch";

function resolveImagePath(imageFile) {
  if (!imageFile) return null;
  const baseName = imageFile.replace(/\.(png|jpe?g)$/i, "");
  const candidates = [`${baseName}.png`, `${baseName}.jpeg`, `${baseName}.jpg`];
  for (const c of candidates) {
    try {
      const resolved = staticFile(`images/${c}`);
      return resolved;
    } catch (e) {}
  }
  return staticFile(`images/${imageFile}`);
}

export const Scene = ({ segment, timingSeg, style, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // ── Sinusoidal movement (only when multiple visuals in chunk) ──
  const camAmplitude = style.camera_amplitude || 200;
  const visualCount = segment.image_file ? 1 : 0;
  const sinY = visualCount > 1
    ? Math.sin(frame / fps * Math.PI * 0.5) * Math.min(camAmplitude * 0.05, 15)
    : 0;

  // ── Ken Burns zoom ──
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const translateX = interpolate(frame, [0, durationInFrames], [0, -10], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // ── Capsule params from config ──
  const worldScale = style.world_scale || 0.85;
  const worldOpacity = style.world_opacity || 1.0;
  const capsuleW = width * worldScale;
  const capsuleH = height * worldScale;
  const capsuleX = (width - capsuleW) / 2;
  const capsuleY = (height - capsuleH) / 2 + sinY; // sinusoidal offset
  const cornerRadius = 12;

  // ── Title params ──
  const titleVisible = style.world_title_visible !== false;
  const titleFont = style.world_title_font || style.font_primary || "Arial Black";
  const titleSize = style.world_title_size || 32;
  const titleColor = style.world_title_color || "#FFFFFF";
  const titleSpeed = style.world_title_speed || 12;
  const titleGap = style.world_title_gap || 20;
  const titleText = segment.state_name || "";

  // Title animation (drop-in for even index, slide for odd)
  const titleProgress = interpolate(frame, [0, titleSpeed], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const titleEased = titleProgress * titleProgress * (3 - 2 * titleProgress);

  // ── Overlay intensity ──
  const effectiveIntensity = Math.min(
    segment.overlay_intensite ?? 2,
    style.overlay_global_intensity ?? 3
  );

  const imgSrc = resolveImagePath(segment.image_file);

  return (
    <AbsoluteFill>
      {/* ── Capsule: image inside rounded border with shadow ── */}
      {imgSrc && (
        <div
          style={{
            position: "absolute",
            left: capsuleX,
            top: capsuleY,
            width: capsuleW,
            height: capsuleH,
            borderRadius: cornerRadius,
            overflow: "hidden",
            border: "2px solid rgba(197,164,78,0.3)",
            boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
            opacity: worldOpacity,
          }}
        >
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
          {/* Overlay inside capsule */}
          <OverlayDispatch
            type={segment.overlay_type || "defaut"}
            intensite={effectiveIntensity}
            frame={frame}
            fps={fps}
          />
        </div>
      )}

      {/* ── Title (outside capsule, above or right) ── */}
      {titleVisible && titleText && (
        <div
          style={{
            position: "absolute",
            left: capsuleX + capsuleW / 2,
            top: capsuleY - titleGap - titleSize,
            transform: `translateX(-50%) translateY(${(1 - titleEased) * -30}px)`,
            opacity: titleEased,
            fontFamily: `'${titleFont}', Georgia, serif`,
            fontSize: titleSize,
            fontWeight: "bold",
            color: titleColor,
            textShadow: "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
            pointerEvents: "none",
            zIndex: 10,
            whiteSpace: "nowrap",
            textAlign: "center",
          }}
        >
          {titleText}
        </div>
      )}

      {/* ── Subtitle ── */}
      <Subtitle
        segment={segment}
        timingSeg={timingSeg}
        style={style}
        durationInFrames={durationInFrames}
      />
    </AbsoluteFill>
  );
};
