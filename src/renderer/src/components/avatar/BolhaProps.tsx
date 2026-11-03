// SPDX-License-Identifier: GPL-3.0-only
import shapes from '../../../../../assets/bolha/shapes.json';
import { motion, AnimatePresence } from 'framer-motion';
import { useId } from 'react';

const LAYER_STYLE = {
  position: 'absolute',
  inset: '-100%',
  width: '300%',
  height: '300%',
  pointerEvents: 'none',
  overflow: 'visible',
  zIndex: 4,
} as const;


export function CoffeeMug({ active, falling, moodClass }: { active: boolean; falling?: boolean; moodClass: string }) {
  const uid = useId().replace(/:/g, '');
  const gradId = `mug-${uid}`;

  return (
    <svg viewBox={shapes.BolhaProps_0} aria-hidden="true" className={moodClass} style={LAYER_STYLE}>
      <defs>
        <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset={shapes.BolhaProps_1} stopColor={shapes.BolhaProps_2} />
          <stop offset={shapes.BolhaProps_3} stopColor={shapes.BolhaProps_4} />
        </linearGradient>
      </defs>
      <AnimatePresence>
        {active && (
          <motion.g
            key="cafe"
            initial={{ opacity: 0, y: 14, scale: 0.96 }}
            animate={falling
              ? { opacity: [1, 1, 0], y: [0, 30, 106], rotate: [0, 12, 42], scale: [1, 1, 0.92] }
              : { opacity: 1, y: 0, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={falling
              ? { duration: 0.62, ease: [0.22, 1, 0.36, 1] }
              : { duration: 0.55, ease: 'easeOut' }}
          >
            {}
            {[
              { x: 104, delay: 0, dur: 2.4 },
              { x: 110, delay: 0.9, dur: 2.9 },
            ].map((s, i) => (
              <motion.path
                key={i}
                d={`M ${s.x} 62 q -4 -7 0 -13 q 4 -6 0 -12`}
                fill={shapes.BolhaProps_5}
                stroke={shapes.BolhaProps_6}
                strokeWidth={shapes.BolhaProps_7}
                strokeLinecap={shapes.BolhaProps_8 as 'round'}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: [0, 0.7, 0], y: [6, -10, -26] }}
                transition={{ duration: s.dur, delay: s.delay, repeat: Infinity, ease: 'easeOut' }}
              />
            ))}

            {}
            <path d={shapes.BolhaProps_9} fill={`url(#${gradId})`} />
            {}
            <path
              d={shapes.BolhaProps_10}
              fill={shapes.BolhaProps_11}
              stroke={shapes.BolhaProps_12}
              strokeWidth={shapes.BolhaProps_13}
              strokeLinecap={shapes.BolhaProps_14 as 'round'}
            />
            {}
            <ellipse cx={shapes.BolhaProps_15} cy={shapes.BolhaProps_16} rx={shapes.BolhaProps_17} ry={shapes.BolhaProps_18} fill={shapes.BolhaProps_19} />

          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}
