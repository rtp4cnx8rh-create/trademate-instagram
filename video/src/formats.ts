// Ausgabeformate fuer alle Kompositionen: 9:16 (Reels/Stories), 1:1 (Feed),
// 16:9 (YouTube/Web). Die Kurzform steckt in der Composition-ID und im
// Dateinamen der Renders.
export type Format = {
  id: string;
  label: string;
  width: number;
  height: number;
};

export const FORMATS: Format[] = [
  {id: 'Vertical', label: '9x16', width: 1080, height: 1920},
  {id: 'Square', label: '1x1', width: 1080, height: 1080},
  {id: 'Wide', label: '16x9', width: 1920, height: 1080},
];
