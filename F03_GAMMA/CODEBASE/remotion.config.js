// remotion.config.js — F03 GAMMA (Hybrid Mode)
// Resolution is driven by hybrid_spec.json meta.width/height.
// This config sets defaults; Root.jsx overrides via Composition props.
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setConcurrency(1);
