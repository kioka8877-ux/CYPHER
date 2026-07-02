/**
 * BetaSubtitle.jsx — Sous-titres mot par mot synchronisés timing.json
 *
 * Chaque mot apparaît exactement quand il est prononcé (start_frame du mot).
 * Animation : fade-in + léger scale-up sur N frames.
 * Mots forts (is_strong) en couleur accent.
 *
 * Paramètres depuis roadmap.style :
 *   subtitle_font          – police (défaut font_primary)
 *   subtitle_size          – taille px (défaut 44)
 *   subtitle_color         – couleur texte (défaut "#FFFFFF")
 *   subtitle_position      – "top" / "center" / "bottom" (défaut "bottom")
 *   subtitle_align         – "left" / "center" / "right" (défaut "center")
 *   subtitle_word_fade     – frames de transition par mot (défaut 3 ≈ 100ms)
 *   accent_color           – couleur mots forts (défaut "#FFD700")
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const BetaSubtitle = ({ timeline, style, timing }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  /* —— Trouver le segment actif —— */
  let segIdx = 0;
  for (let i = timeline.length - 1; i >= 0; i--) {
    if (frame >= timeline[i].start_frame) {
      segIdx = i;
      break;
    }
  }

  const seg = timeline[segIdx];
  const text = seg.text_subtitles;
  if (!text) return null;

  /* —— Paramètres de style —— */
  const font = style.subtitle_font ?? style.font_primary ?? "Cinzel";
  const size = parseInt(style.subtitle_size, 10) || 44;
  const color = style.subtitle_color ?? "#FFFFFF";
  const accentColor = style.accent_color ?? "#FFD700";
  const position = style.subtitle_position ?? "bottom";
  const align = style.subtitle_align ?? "center";
  const wordFadeFrames = style.subtitle_word_fade ?? 3;

  /* —— Durée locale du segment —— */
  const nextSeg = timeline[segIdx + 1] || null;
  const segEnd = nextSeg ? nextSeg.start_frame : durationInFrames;
  const segDuration = segEnd - seg.start_frame;
  const localFrame = frame - seg.start_frame;

  /* —— Fade out en fin de segment (5 dernières frames) —— */
  const fadeOutFrames = 5;
  const segOpacity = interpolate(
    localFrame,
    [segDuration - fadeOutFrames, segDuration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  /* —— Position verticale —— */
  const posStyle = {};
  switch (position) {
    case "top":
      posStyle.top = "8%";
      break;
    case "center":
      posStyle.top = "50%";
      posStyle.transform = "translateY(-50%)";
      break;
    default:
      posStyle.bottom = "8%";
  }

  /* —— Mots depuis timing.json —— */
  const timingSeg = timing?.segments?.[segIdx];
  const words = timingSeg?.words || [];

  /* —— Rendu mot par mot —— */
  const renderText = () => {
    if (!words.length) {
      // Fallback : texte brut si pas de word-level timing
      return (
        <span style={{ fontFamily: `'${font}', Georgia, serif`, color }}>
          {text}
        </span>
      );
    }

    return words.map((w, i) => {
      const wordLocalFrame = frame - w.start_frame;

      // Opacité : invisible avant start_frame, fade-in sur wordFadeFrames
      const wordOpacity = interpolate(
        wordLocalFrame,
        [0, wordFadeFrames],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );

      // Scale : léger zoom 0.9 → 1.0
      const wordScale = interpolate(
        wordLocalFrame,
        [0, wordFadeFrames],
        [0.92, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );

      return (
        <React.Fragment key={i}>
          <span
            style={{
              fontFamily: `'${font}', Georgia, serif`,
              color: w.is_strong ? accentColor : color,
              opacity: wordOpacity,
              transform: `scale(${wordScale})`,
              display: "inline",
            }}
          >
            {w.word}
          </span>{" "}
        </React.Fragment>
      );
    });
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        padding: "0 64px",
        textAlign: align,
        opacity: segOpacity,
        ...posStyle,
      }}
    >
      <div
        style={{
          fontSize: size,
          lineHeight: 1.25,
          textShadow:
            "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
          wordBreak: "break-word",
        }}
      >
        {renderText()}
      </div>
    </div>
  );
};
