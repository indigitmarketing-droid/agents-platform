import React from "react";
import {
  AbsoluteFill,
  Easing,
  OffthreadVideo,
  Series,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/**
 * Ad montage of three ElevenLabs lip-sync scenes.
 *
 * The three source clips are the SAME visual take with three different
 * voiceovers, delivered as vertical content pillar-boxed in 1280x720. They are
 * pre-cropped to 494x720 (scene1/2/3.mp4) and covered into a 720x1280 frame.
 *
 * Because they are spoken clips, a cross-dissolve would overlap two voices, so
 * scenes are butt-joined (clean, sequential audio) and each cut is smoothed by
 * a short "zoom-punch" + micro-blur — a uniform transition that masks the lip
 * jump without overlapping audio. A consistent grade + vignette + intro/outro
 * fades tie the whole ad together.
 */

const SCENES = [
  { src: "scene1.mp4", durationInFrames: 144 },
  { src: "scene2.mp4", durationInFrames: 144 },
  { src: "scene3.mp4", durationInFrames: 137 },
];

const Scene: React.FC<{ src: string; durationInFrames: number }> = ({
  src,
  durationInFrames,
}) => {
  const frame = useCurrentFrame(); // local to this Series.Sequence

  // Zoom-punch that settles, then a slow drift for life — masks the cut.
  const scale = interpolate(
    frame,
    [0, 8, durationInFrames],
    [1.06, 1.0, 1.02],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  // Quick blur on entry, part of the punch transition.
  const blur = interpolate(frame, [0, 7], [7, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade the audio in/out a few frames at the seams for click-free joins.
  const volume = (f: number) =>
    Math.min(
      interpolate(f, [0, 3], [0, 1], { extrapolateRight: "clamp" }),
      interpolate(f, [durationInFrames - 3, durationInFrames], [1, 0], {
        extrapolateLeft: "clamp",
      }),
    );

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "black" }}>
      <OffthreadVideo
        src={staticFile(src)}
        volume={volume}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          scale: String(scale),
          filter: `blur(${blur}px) contrast(1.06) saturate(1.08) brightness(1.02)`,
        }}
      />
    </AbsoluteFill>
  );
};

export const AdMontage: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Cinematic intro / outro for the whole ad.
  const opacity = interpolate(
    frame,
    [0, 10, durationInFrames - 10, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ opacity }}>
        <Series>
          {SCENES.map((s) => (
            <Series.Sequence key={s.src} durationInFrames={s.durationInFrames}>
              <Scene src={s.src} durationInFrames={s.durationInFrames} />
            </Series.Sequence>
          ))}
        </Series>

        {/* Soft vignette to unify all scenes. */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.28) 100%)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
