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
} as const;


export function SleepPillow({ asleep, waking, startled }: { asleep: boolean; waking: boolean; startled: boolean }) {
  const uid = useId().replace(/:/g, '');
  const gradId = `pillow-${uid}`;

  return (
    <svg viewBox={shapes.BolhaSleep_0} aria-hidden="true" style={{ ...LAYER_STYLE, zIndex: 0 }}>
      <defs>
        <linearGradient id={gradId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset={shapes.BolhaSleep_1} stopColor={shapes.BolhaSleep_2} />
          <stop offset={shapes.BolhaSleep_3} stopColor={shapes.BolhaSleep_4} />
        </linearGradient>
      </defs>
      <AnimatePresence>
        {(asleep || startled || waking) && (
          <motion.g
            key="pillow"
            initial={{ opacity: 0, x: -70, y: 10, scaleX: 0.82 }}
            animate={
              startled
                ? // Susto: o travesseiro é chutado pro lado, girando.
                  { opacity: [1, 1, 0], x: [0, 54, 118], y: [0, -42, 16], rotate: [0, 155, 330], scaleX: [1, 0.9, 0.75] }
                : { opacity: 1, x: 0, y: 0, rotate: 0, scaleX: 1 }
            }
            exit={{ opacity: 0, x: -60, y: 10, transition: { duration: 0.5, ease: 'easeIn' } }}
            transition={
              startled
                ? { duration: 0.85, ease: 'easeOut' }
                : { type: 'spring', stiffness: 120, damping: 16 }
            }
            style={{ originX: '50px', originY: '96px' }}
          >
            {}
            <ellipse cx={shapes.BolhaSleep_5} cy={shapes.BolhaSleep_6} rx={shapes.BolhaSleep_7} ry={shapes.BolhaSleep_8} fill={shapes.BolhaSleep_9} style={{ filter: 'blur(5px)' }} />

            {}
            <path
              d={shapes.BolhaSleep_10}
              fill={`url(#${gradId})`}
            />
            {}
            <path
              d={shapes.BolhaSleep_11}
              fill={shapes.BolhaSleep_12}
              stroke={shapes.BolhaSleep_13}
              strokeWidth={shapes.BolhaSleep_14}
              strokeLinecap={shapes.BolhaSleep_15 as 'round'}
            />
            {}
            <path
              d={shapes.BolhaSleep_16}
              fill={shapes.BolhaSleep_17}
              stroke={shapes.BolhaSleep_18}
              strokeWidth={shapes.BolhaSleep_19}
              strokeLinecap={shapes.BolhaSleep_20 as 'round'}
            />
          </motion.g>
        )}
      </AnimatePresence>
    </svg>
  );
}


const ZS = [
  { delay: 0, size: 13, dx: 26, dur: 3.2 },
  { delay: 1.1, size: 10, dx: 38, dur: 3.6 },
  { delay: 2.2, size: 16, dx: 18, dur: 4 },
];


export function SleepZs({ asleep, waking, startled, moodClass }: { asleep: boolean; waking: boolean; startled: boolean; moodClass: string }) {
  return (
    <svg viewBox={shapes.BolhaSleep_21} aria-hidden="true" className={moodClass} style={{ ...LAYER_STYLE, zIndex: 4 }}>
      <AnimatePresence>
        {(asleep || waking) && !startled &&
          ZS.map((z, i) => (
            <motion.text
              key={i}
              x={shapes.BolhaSleep_22}
              y={shapes.BolhaSleep_23}
              fill={shapes.BolhaSleep_24}
              fontSize={z.size}
              fontWeight={shapes.BolhaSleep_25}
              fontFamily={shapes.BolhaSleep_26}
              initial={{ opacity: 0, x: 0, y: 0, rotate: -6 }}
              animate={
                waking
                  ? { opacity: 0, y: -96, transition: { duration: 0.7, ease: 'easeOut' } }
                  : { opacity: [0, 0.95, 0.95, 0], x: [0, z.dx * 0.5, z.dx], y: [0, -34, -76], rotate: [-6, 8, -4] }
              }
              exit={{ opacity: 0, transition: { duration: 0.45 } }}
              transition={{ duration: z.dur, delay: z.delay, repeat: Infinity, repeatDelay: 1.4, ease: 'easeOut' }}
            >
              z
            </motion.text>
          ))}

        {}
        {startled &&
          ZS.map((z, i) => (
            <motion.text
              key={`bang-${i}`}
              x={shapes.BolhaSleep_27}
              y={shapes.BolhaSleep_28}
              fill={shapes.BolhaSleep_29}
              fontSize={z.size}
              fontWeight={shapes.BolhaSleep_30}
              fontFamily={shapes.BolhaSleep_31}
              initial={{ opacity: 0.9, x: z.dx * 0.6, y: -30 }}
              animate={{ opacity: 0, x: (i - 1) * 60, y: -70 - i * 12, rotate: (i - 1) * 60 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            >
              z
            </motion.text>
          ))}
      </AnimatePresence>
    </svg>
  );
}
