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
import {FONT_FAMILY} from './fonts';
import {COLORS} from './theme';

// Schnelle Jump-Cut-Variante: nur die App-UI aus den Figma-Exporten,
// als Karten- und Detail-Ausschnitte in einem festen Bezel-Rahmen.
// Die Rechtecke sind Pixelkoordinaten in den 1080x1080-Quellbildern
// und daher auf die Motive der jeweiligen Woche abgestimmt (hier KW-35).

type Rect = {x: number; y: number; w: number; h: number};
type Shot = {file: string; rect: Rect; dur: number};

const SCREEN_W = 920;
const SCREEN_H = 500;
const FRAME_PAD = 18;

export const RAPID_SHOTS: Shot[] = [
  // 01-Mo: Performance-Card
  {file: 'cuts/01-Mo.jpg', rect: {x: 130, y: 460, w: 820, h: 450}, dur: 10},
  {file: 'cuts/01-Mo.jpg', rect: {x: 305, y: 450, w: 470, h: 258}, dur: 8},
  {file: 'cuts/01-Mo.jpg', rect: {x: 330, y: 635, w: 400, h: 180}, dur: 8},
  // 03-Mi: Kalender-Card
  {file: 'cuts/03-Mi.jpg', rect: {x: 190, y: 295, w: 700, h: 385}, dur: 10},
  {file: 'cuts/03-Mi.jpg', rect: {x: 195, y: 240, w: 520, h: 380}, dur: 8},
  {file: 'cuts/03-Mi.jpg', rect: {x: 210, y: 460, w: 650, h: 360}, dur: 8},
  // 05-Fr: Risk/Reward-Card
  {file: 'cuts/05-Fr.jpg', rect: {x: 160, y: 450, w: 760, h: 418}, dur: 10},
  {file: 'cuts/05-Fr.jpg', rect: {x: 150, y: 690, w: 420, h: 330}, dur: 8},
  {file: 'cuts/05-Fr.jpg', rect: {x: 510, y: 690, w: 415, h: 330}, dur: 8},
];

export const RAPID_OUTRO = 26;

export const rapidDuration = () =>
  RAPID_SHOTS.reduce((sum, s) => sum + s.dur, 0) + RAPID_OUTRO;

const Backdrop: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundColor: COLORS.bgDeep,
      backgroundImage: `radial-gradient(120% 80% at 50% 30%, ${COLORS.bg} 0%, ${COLORS.bgDeep} 70%)`,
    }}
  />
);

const BezelShot: React.FC<{shot: Shot; index: number}> = ({shot, index}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const direction = index % 2 === 0 ? 1 : -1;

  // Der Bezel ist auf 1080x1920 ausgelegt; in breiteren Formaten waechst er
  // mit, bleibt aber innerhalb der Bildraender.
  const bezelW = SCREEN_W + 2 * FRAME_PAD;
  const bezelH = SCREEN_H + 2 * FRAME_PAD;
  const fit = Math.min((width * 0.885) / bezelW, (height * 0.75) / bezelH);

  // Ausschnitt deckend in das Screen-Fenster einpassen, Drift-Zoom obendrauf.
  const cover = Math.max(SCREEN_W / shot.rect.w, SCREEN_H / shot.rect.h);
  const drift = interpolate(
    frame,
    [0, shot.dur],
    direction === 1 ? [1, 1.07] : [1.07, 1],
  );
  const scale = cover * drift;
  const left = SCREEN_W / 2 - (shot.rect.x + shot.rect.w / 2) * scale;
  const top = SCREEN_H / 2 - (shot.rect.y + shot.rect.h / 2) * scale;

  // Punch des gesamten Bezels bei jedem Cut.
  const punch = interpolate(frame, [0, 4], [1.06, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });
  const tilt = interpolate(frame, [0, 5], [direction * 0.9, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: 'clamp',
  });
  const flash = interpolate(frame, [0, 2], [0.22, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div
        style={{
          padding: FRAME_PAD,
          borderRadius: 34,
          background: 'linear-gradient(180deg, #23272f 0%, #14171c 100%)',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          boxShadow:
            '0 50px 140px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          transform: `scale(${punch * fit}) rotate(${tilt}deg)`,
        }}
      >
        <div
          style={{
            width: SCREEN_W,
            height: SCREEN_H,
            borderRadius: 20,
            backgroundColor: '#000000',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Img
            src={staticFile(shot.file)}
            style={{
              position: 'absolute',
              width: 1080 * scale,
              height: 1080 * scale,
              maxWidth: 'none',
              left,
              top,
            }}
          />
          <AbsoluteFill style={{backgroundColor: COLORS.white, opacity: flash}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const RapidOutro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 14, stiffness: 200}});
  const scale = interpolate(pop, [0, 1], [0.82, 1]);
  const lineWidth = interpolate(frame, [4, 14], [0, 420], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 44}}>
      <div
        style={{
          fontFamily: `'${FONT_FAMILY}', 'Liberation Sans', sans-serif`,
          fontWeight: 900,
          fontSize: 138,
          letterSpacing: -4,
          color: COLORS.white,
          transform: `scale(${scale}) skewX(-8deg)`,
        }}
      >
        Trademate
      </div>
      <div style={{width: lineWidth, height: 3, backgroundColor: COLORS.green}} />
    </AbsoluteFill>
  );
};

export const TrademateRapid: React.FC = () => {
  let cursor = 0;
  const starts = RAPID_SHOTS.map((s) => {
    const from = cursor;
    cursor += s.dur;
    return from;
  });

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bgDeep}}>
      <Backdrop />
      {RAPID_SHOTS.map((shot, i) => (
        <Sequence
          key={`${shot.file}-${i}`}
          from={starts[i]}
          durationInFrames={shot.dur}
          name={`Shot ${i + 1}`}
        >
          <BezelShot shot={shot} index={i} />
        </Sequence>
      ))}
      <Sequence from={cursor} durationInFrames={RAPID_OUTRO} name="Outro">
        <RapidOutro />
      </Sequence>
    </AbsoluteFill>
  );
};
