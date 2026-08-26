import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

export const FONT_FAMILY = 'Inter';

export const loadFonts = () =>
  Promise.all(
    (['500', '700', '900'] as const).map((weight) =>
      loadFont({
        family: FONT_FAMILY,
        url: staticFile(`fonts/inter-latin-${weight}-normal.woff2`),
        weight,
      }),
    ),
  );
