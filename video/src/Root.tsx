import React from 'react';
import {Composition} from 'remotion';
import {CUT_IMAGES} from './assets.generated';
import {FORMATS} from './formats';
import {loadFonts} from './fonts';
import {TrademateRapid, rapidDuration} from './TrademateRapid';
import {TrademateReel, totalDuration} from './TrademateReel';

loadFonts();

// Pro Komposition eine Variante je Ausgabeformat. Das 9:16-Format behaelt die
// bisherigen IDs "TrademateReel" / "TrademateRapid", damit bestehende
// Render-Befehle unveraendert funktionieren.
const withFormats = (
  baseId: string,
  component: React.FC,
  durationInFrames: number,
) =>
  FORMATS.map((format) => (
    <Composition
      key={`${baseId}-${format.id}`}
      id={format.id === 'Vertical' ? baseId : `${baseId}-${format.id}`}
      component={component}
      durationInFrames={durationInFrames}
      fps={30}
      width={format.width}
      height={format.height}
    />
  ));

export const RemotionRoot: React.FC = () => (
  <>
    {withFormats('TrademateReel', TrademateReel, totalDuration(CUT_IMAGES.length))}
    {withFormats('TrademateRapid', TrademateRapid, rapidDuration())}
  </>
);
