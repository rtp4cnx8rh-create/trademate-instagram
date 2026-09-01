import React from 'react';
import {Composition} from 'remotion';
import {CUT_IMAGES} from './assets.generated';
import {loadFonts} from './fonts';
import {TrademateRapid, rapidDuration} from './TrademateRapid';
import {TrademateReel, totalDuration} from './TrademateReel';

loadFonts();

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="TrademateReel"
      component={TrademateReel}
      durationInFrames={totalDuration(CUT_IMAGES.length)}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="TrademateRapid"
      component={TrademateRapid}
      durationInFrames={rapidDuration()}
      fps={30}
      width={1080}
      height={1920}
    />
  </>
);
