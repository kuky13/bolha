// SPDX-License-Identifier: GPL-3.0-only
import shapes from '../../../../../assets/drippy/shapes.json';
import { motion } from 'framer-motion';

const NOTAS = [
  { x: 22, glyph: '♪', delay: 0, drift: -22, size: 13, dur: 3 },
  { x: 78, glyph: '♫', delay: 0.8, drift: 26, size: 16, dur: 3.4 },
  { x: 40, glyph: '♬', delay: 1.7, drift: -12, size: 11, dur: 2.8 },
];

export function DrippyMusicNotes({ active, moodClass }: { active: boolean; moodClass: string }) {
  if (!active) return null;

  return (
    <svg
      key="drippy-music-notes-active"
      viewBox={shapes.DrippyMusicNotes_0}
      aria-hidden="true"
      className={moodClass}
      style={{
        position: 'absolute',
        inset: '-100%',
        width: '300%',
        height: '300%',
        pointerEvents: 'none',
        overflow: 'visible',
        zIndex: 4,
      }}
    >
      {NOTAS.map((n, i) => (
        <motion.text
          key={i}
          x={n.x}
          y={shapes.DrippyMusicNotes_1}
          fill={shapes.DrippyMusicNotes_2}
          fontSize={n.size}
          fontWeight={shapes.DrippyMusicNotes_3}
          fontFamily={shapes.DrippyMusicNotes_4}
          initial={{ opacity: 0, y: 0, x: 0 }}
          animate={{ opacity: [0, 0.95, 0.95, 0], y: [0, -44, -92], x: [0, n.drift * 0.5, n.drift], rotate: [-10, 10, -6] }}
          transition={{ duration: n.dur, delay: n.delay, repeat: Infinity, repeatDelay: 0.5, ease: 'easeOut' }}
        >
          {n.glyph}
        </motion.text>
      ))}
    </svg>
  );
}
