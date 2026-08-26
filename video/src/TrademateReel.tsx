import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CUT_IMAGES} from './assets.generated';
import {FONT_FAMILY} from './fonts';
import {COLORS} from './theme';

export const INTRO_BEAT = 18;
export const CUT_DURATION = 14;
export const OUTRO_DURATION = 56;

export const totalDuration = (imageCount: number) =>
  2 * INTRO_BEAT + imageCount * CUT_DURATION + OUTRO_DURATION;

const baseFont: React.CSSProperties = {
  fontFamily: `'${FONT_FAMILY}', 'Liberation Sans', sans-serif`,
};

// Silbergradient wie die Headlines der Post-Templates.
const silverText: React.CSSProperties = {
  backgroundImage: 'linear-gradient(180deg, #ffffff 0%, #d3d7dd 55%, #969da8 100%)',
  WebkitBackgroundClip: 'text',
  backgroundClip: 'text',
  color: 'transparent',
};

const Backdrop: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundColor: COLORS.bgDeep,
      backgroundImage: `radial-gradient(120% 80% at 50% 20%, ${COLORS.bg} 0%, ${COLORS.bgDeep} 70%)`,
    }}
  />
);

const IntroBeat: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 16, stiffness: 190}});
  const scale = interpolate(pop, [0, 1], [0.85, 1]);
  const opacity = interpolate(frame, [0, 3], [0, 1], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div
          style={{
            ...baseFont,
            ...silverText,
            fontWeight: 900,
            fontSize: 128,
            letterSpacing: -3,
            textAlign: 'center',
            lineHeight: 1.05,
            padding: '0 60px',
            transform: `scale(${scale})`,
            opacity,
          }}
        >
          {text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const ImageCut: React.FC<{src: string; index: number}> = ({src, index}) => {
  const frame = useCurrentFrame();
  const direction = index % 2 === 0 ? 1 : -1;

  // Punch-Zoom: harter Einstieg, der in wenigen Frames einrastet und danach driftet.
  const scale =
    direction === 1
      ? interpolate(frame, [0, 5, CUT_DURATION], [1.16, 1.05, 1.01], {
          easing: Easing.out(Easing.cubic),
          extrapolateRight: 'clamp',
        })
      : interpolate(frame, [0, 5, CUT_DURATION], [0.94, 1.01, 1.06], {
          easing: Easing.out(Easing.cubic),
          extrapolateRight: 'clamp',
        });
  const shiftX = interpolate(frame, [0, 6], [direction * 26, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });
  const tilt = interpolate(frame, [0, 7], [direction * 1.4, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });
  const flash = interpolate(frame, [0, 3], [0.3, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bgDeep}}>
      {/* Unschaerfe-Fuellung hinter dem quadratischen Motiv */}
      <Img
        src={staticFile(src)}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: 'scale(1.4)',
          filter: 'blur(48px) brightness(0.5) saturate(1.15)',
        }}
      />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <Img
          src={staticFile(src)}
          style={{
            width: 1000,
            height: 1000,
            borderRadius: 32,
            boxShadow: '0 40px 120px rgba(0, 0, 0, 0.65)',
            transform: `translateX(${shiftX}px) rotate(${tilt}deg) scale(${scale})`,
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill style={{backgroundColor: COLORS.white, opacity: flash}} />
    </AbsoluteFill>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 15, stiffness: 160}});
  const scale = interpolate(pop, [0, 1], [0.8, 1]);
  const lineWidth = interpolate(frame, [6, 20], [0, 460], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaOpacity = interpolate(frame, [12, 24], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaShift = interpolate(frame, [12, 24], [24, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 56}}>
        <div
          style={{
            ...baseFont,
            fontWeight: 900,
            fontSize: 150,
            letterSpacing: -4,
            color: COLORS.white,
            transform: `scale(${scale}) skewX(-8deg)`,
          }}
        >
          Trademate
        </div>
        <div style={{width: lineWidth, height: 3, backgroundColor: COLORS.green}} />
        <div
          style={{
            ...baseFont,
            fontWeight: 700,
            fontSize: 42,
            letterSpacing: 8,
            color: COLORS.silver,
            opacity: ctaOpacity,
            transform: `translateY(${ctaShift}px)`,
          }}
        >
          7 DAYS FREE
        </div>
        <div
          style={{
            ...baseFont,
            fontWeight: 500,
            fontSize: 34,
            letterSpacing: 4,
            color: COLORS.muted,
            opacity: ctaOpacity,
            transform: `translateY(${ctaShift}px)`,
            marginTop: -32,
          }}
        >
          LINK IN BIO
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const TrademateReel: React.FC = () => {
  const cutsStart = 2 * INTRO_BEAT;
  const outroStart = cutsStart + CUT_IMAGES.length * CUT_DURATION;

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bgDeep}}>
      <Sequence durationInFrames={INTRO_BEAT} name="Hook 1">
        <IntroBeat text="YOUR TRADING." />
      </Sequence>
      <Sequence from={INTRO_BEAT} durationInFrames={INTRO_BEAT} name="Hook 2">
        <IntroBeat text="IN NUMBERS." />
      </Sequence>
      {CUT_IMAGES.map((src, i) => (
        <Sequence
          key={src}
          from={cutsStart + i * CUT_DURATION}
          durationInFrames={CUT_DURATION}
          name={`Cut ${i + 1}`}
        >
          <ImageCut src={src} index={i} />
        </Sequence>
      ))}
      <Sequence from={outroStart} durationInFrames={OUTRO_DURATION} name="Outro">
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};
