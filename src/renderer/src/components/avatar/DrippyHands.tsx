// SPDX-License-Identifier: GPL-3.0-only
import shapes from '../../../../../assets/drippy/shapes.json';
import { motion } from 'framer-motion';

interface PawProps {
  x: number;
  y: number;
  rotate?: number;
  scale?: number;
  
  flip?: boolean;
}

export function Paw({ x, y, rotate = 0, scale = 1, flip = false }: PawProps) {
  const sx = flip ? -scale : scale;
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${sx} ${scale})`} fill={shapes.DrippyHands_0}>
      {}
      <ellipse cx={shapes.DrippyHands_1} cy={shapes.DrippyHands_2} rx={shapes.DrippyHands_3} ry={shapes.DrippyHands_4} />
      {}
      <rect x={-4.3} y={-6.4} width={2.3} height={5.4} rx={shapes.DrippyHands_5} transform="rotate(-13 -3.15 -3.7)" />
      <rect x={-1.25} y={-7.2} width={2.5} height={6.2} rx={shapes.DrippyHands_6} />
      <rect x={shapes.DrippyHands_7} y={-6.4} width={2.3} height={5.4} rx={shapes.DrippyHands_8} transform="rotate(13 3.05 -3.7)" />
      {}
      <rect x={-6.9} y={-1.5} width={2.7} height={4.6} rx={shapes.DrippyHands_9} transform="rotate(-58 -5.55 0.8)" />
    </g>
  );
}


export function CoveringHands({ active }: { active: boolean }) {
  if (!active) return null;
  return (
    <g>
      {[30, 70].map((cx, i) => (
        <motion.g
          key={cx}
          initial={{ opacity: 0, y: 26 }}
          animate={{
            opacity: 1,
            y: 0,
            rotate: i === 0 ? [-12, -12, -8, -12] : [12, 12, 17, 12],
            x: i === 0 ? [-1, -1, -3, -1] : [1, 1, 3, 1],
          }}
          exit={{ opacity: 0, y: 26 }}
          transition={{
            opacity: { duration: 0.18 },
            y: { type: 'spring', stiffness: 300, damping: 18 },
            rotate: { duration: 4.8, times: [0, 0.58, 0.72, 1], repeat: Infinity, repeatDelay: 2.2 },
            x: { duration: 4.8, times: [0, 0.58, 0.72, 1], repeat: Infinity, repeatDelay: 2.2 },
          }}
          style={{ originX: `${cx}px`, originY: '40px' }}
        >
          <Paw x={cx} y={shapes.DrippyHands_10} scale={1.68} flip={i === 1} rotate={i === 0 ? -10 : 10} />
        </motion.g>
      ))}
    </g>
  );
}
