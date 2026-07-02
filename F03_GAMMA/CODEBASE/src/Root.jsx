// src/Root.jsx — F03 GAMMA (Hybrid Mode)
// Reads hybrid_spec.json, filters engine="gamma" chunks,
// builds a Remotion-compatible timeline for the gamma renderer.
//
// Supports both:
//   - hybrid_spec.json (hybrid mode — filters gamma chunks)
//   - roadmap.json     (standalone CRUSADER mode — uses full timeline)

import React from "react";
import { Composition, staticFile } from "remotion";
import { Main } from "./Main";

// Detect which spec is available
function loadSpec() {
  try {
    const hybrid = require("../public/hybrid_spec.json");
    if (hybrid && hybrid.chunks) return { type: "hybrid", data: hybrid };
  } catch (e) {}
  try {
    const roadmap = require("../public/roadmap.json");
    if (roadmap && roadmap.timeline) return { type: "roadmap", data: roadmap };
  } catch (e) {}
  throw new Error("No hybrid_spec.json or roadmap.json found in public/");
}

function loadTiming() {
  try {
    return require("../public/timing.json");
  } catch (e) {
    return null;
  }
}

export const RemotionRoot = () => {
  const spec = loadSpec();
  const timing = loadTiming();

  let roadmap, fps, totalFrames, width, height;

  if (spec.type === "hybrid") {
    const hybrid = spec.data;
    fps = hybrid.meta.fps || 30;
    width = hybrid.meta.width || 1080;
    height = hybrid.meta.height || 1920;

    // Filter gamma chunks only
    const gammaChunks = hybrid.chunks.filter(c => c.engine === "gamma");

    // Convert to roadmap format for Main.jsx compatibility
    roadmap = {
      style: {
        ...hybrid.gamma_config,
        // Ensure required style fields
        font_primary: hybrid.gamma_config?.font_primary || "Cinzel",
        font_accent: hybrid.gamma_config?.font_accent || "Playfair Display",
        subtitle_size: hybrid.gamma_config?.subtitle_size || 44,
        subtitle_color: hybrid.gamma_config?.subtitle_color || "#FFFFFF",
        accent_color: hybrid.gamma_config?.accent_color || "#A0D2DB",
        background_color: hybrid.gamma_config?.background_color || "#0a0a12",
        grain_intensity: hybrid.gamma_config?.grain_intensity || 0.12,
        vignette: hybrid.gamma_config?.vignette ?? true,
      },
      timeline: gammaChunks.map((chunk, idx) => ({
        id: chunk.id,
        image_file: chunk.image_file || "",
        text_subtitles: chunk.text_subtitles || "",
        start_frame: Math.round(chunk.start * fps),
        end_frame: Math.round(chunk.end * fps),
        start: chunk.start,
        end: chunk.end,
        overlay_type: chunk.overlay_type || "defaut",
        overlay_intensite: chunk.overlay_intensite || 2,
        media_type: chunk.media_type || "image",
        sfx_trigger: idx < 3,
        // Snowfall-specific metadata
        state_name: chunk.state_name || "",
        snowfall_inches: chunk.snowfall_inches || 0,
      })),
    };

    // Total frames = end of last gamma chunk (they render independently)
    // But each gamma chunk is rendered as its own Remotion composition,
    // so totalFrames = frames in THIS chunk only.
    // For the composition, we use the span of all gamma chunks.
    const lastGamma = gammaChunks[gammaChunks.length - 1];
    totalFrames = Math.round(lastGamma.end * fps);

  } else {
    // Standalone CRUSADER mode
    roadmap = spec.data;
    fps = roadmap.meta?.fps || 30;
    width = roadmap.meta?.width || 1920;
    height = roadmap.meta?.height || 1080;
    const lastSeg = roadmap.timeline[roadmap.timeline.length - 1];
    totalFrames = lastSeg.end_frame || Math.round(lastSeg.end * fps);
  }

  return (
    <Composition
      id="CypherGamma"
      component={Main}
      durationInFrames={totalFrames}
      fps={fps}
      width={width}
      height={height}
      defaultProps={{ timing, roadmap }}
    />
  );
};
