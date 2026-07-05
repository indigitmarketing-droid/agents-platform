import React from "react";
import {
  AbsoluteFill,
  Easing,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/**
 * EasyDent talking-head edit.
 *
 * The source (public/easyDent.mp4) is one continuous, consistent handheld
 * take (720x1280, 24fps, ~21.4s) — no internal hard cuts. So "improving the
 * transitions / making it more homogeneous" means giving the raw clip a
 * finished, cohesive treatment:
 *
 *  - a smooth cinematic fade-in intro and fade-out outro (the in/out transitions)
 *  - a consistent slow push-in so the energy stays even throughout
 *  - a subtle, consistent grade + vignette to unify the frame
 *
 * The original audio and the easyDent watermark are kept intact.
 */
export const EasyDentEdit: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const settle = Math.round(fps * 0.6); // intro "settle" duration
  const fadeIn = Math.round(fps * 0.5);
  const fadeOut = Math.round(fps * 0.5);
  const audioFade = Math.round(fps * 0.3);

  // Consistent slow push-in: settle from 1.05 -> 1.0, then gently push to 1.03.
  // Kept subtle so the bottom-right easyDent watermark is never cropped.
  const scale = interpolate(
    frame,
    [0, settle, durationInFrames],
    [1.05, 1.0, 1.03],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  // Cinematic fade in / fade out — the improved in/out transitions.
  const opacity = interpolate(
    frame,
    [0, fadeIn, durationInFrames - fadeOut, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Match the audio to the visual fades so there are no pops at the edges.
  const volume = (f: number) =>
    interpolate(
      f,
      [0, audioFade, durationInFrames - audioFade, durationInFrames],
      [0, 1, 1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ opacity }}>
        <OffthreadVideo
          src={staticFile("easyDent.mp4")}
          volume={volume}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            scale: String(scale),
            // Subtle consistent grade for a homogeneous look.
            filter: "contrast(1.06) saturate(1.1) brightness(1.02)",
          }}
        />
      </AbsoluteFill>

      {/* Soft vignette to unify the frame and focus attention. */}
      <AbsoluteFill
        style={{
          opacity,
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.28) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
