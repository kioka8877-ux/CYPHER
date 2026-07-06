// src/components/Subtitle.jsx — F03 SIGISMUND
// Rendu des sous-titres. Mots forts (is_strong) en couleur accent uniquement.
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

// Distance de glissement slide-in (en px)
const SLIDE_PX = 30;

export const Subtitle = ({ segment, timingSeg, style, durationInFrames, capsuleBottom }) => {
  const frame = useCurrentFrame();

  // Lecture des paramètres d'animation depuis le roadmap.json
  const animEnabled = style.subtitle_anim !== false;
  const FADE_FRAMES = style.subtitle_anim_speed ?? 5;

  // ── Fondu in/out ───────────────────────────────────────────────────────────
  const opacity = animEnabled
    ? interpolate(
        frame,
        [0, FADE_FRAMES, durationInFrames - FADE_FRAMES, durationInFrames],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 1;

  // ── Slide-in gauche → droite ───────────────────────────────────────────────
  const slideX = animEnabled
    ? interpolate(
        frame,
        [0, FADE_FRAMES],
        [-SLIDE_PX, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 0;

  // ── Position verticale ─────────────────────────────────────────────────────
  const posStyle = {};
  if (capsuleBottom !== undefined) {
    posStyle.top = `${capsuleBottom + 12}px`;
  } else {
    switch (style.subtitle_position) {
      case "top":
        posStyle.top = "8%";
        break;
      case "center":
        posStyle.top = "50%";
        posStyle.transform = `translateY(-50%) translateX(${slideX}px)`;
        break;
      default: // bottom
        posStyle.bottom = "8%";
    }
  }

  // ── Rendu des mots (mots forts = couleur accent, sinon couleur normale) ────
  const words = timingSeg?.words || [];

  const renderWords = () => {
    if (!words.length) {
      return (
        <span
          style={{
            fontFamily: `'${style.font_primary}', Georgia, serif`,
            color: style.subtitle_color,
          }}
        >
          {segment.text_subtitles}
        </span>
      );
    }

    return words.map((w, i) => (
      <React.Fragment key={i}>
        <span
          style={{
            fontFamily: `'${style.font_primary}', Georgia, serif`,
            color: w.is_strong ? style.accent_color : style.subtitle_color,
          }}
        >
          {w.word}
        </span>
        {" "}
      </React.Fragment>
    ));
  };

  // Pour top et bottom, le transform contient uniquement le slide.
  // Pour center, il est déjà intégré dans posStyle.transform ci-dessus.
  const transformVal = style.subtitle_position === "center"
    ? posStyle.transform
    : `translateX(${slideX}px)`;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        padding: "0 64px",
        textAlign: "center",
        opacity,
        transform: transformVal,
        ...posStyle,
      }}
    >
      <div
        style={{
          fontSize: parseInt(style.subtitle_size, 10),
          lineHeight: 1.25,
          textShadow: "0 2px 12px rgba(0,0,0,0.85), 0 0 4px rgba(0,0,0,0.5)",
          wordBreak: "break-word",
        }}
      >
        {renderWords()}
      </div>
    </div>
  );
};
