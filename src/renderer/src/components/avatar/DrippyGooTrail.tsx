// SPDX-License-Identifier: GPL-3.0-only
import shapes from '../../../../../assets/drippy/shapes.json';
import { useId } from 'react';
import type { DragMotion } from './useDragMotion';

interface DrippyGooTrailProps {
  motion: DragMotion;
  
  opacity: number;
}


const DROPS = [
  { sample: 3, radius: 24 },
  { sample: 7, radius: 16 },
  { sample: 11, radius: 10 },
];


const TRAIL_GAIN = 2.6;


const RAIO_CORPO = 45;
const FOLGA_FUSAO = 11;

function limitar(dx: number, dy: number, raioGota: number) {
  const teto = RAIO_CORPO + raioGota + FOLGA_FUSAO;
  const d = Math.hypot(dx, dy);
  if (d <= teto) return { dx, dy };
  const k = teto / d;
  return { dx: dx * k, dy: dy * k };
}

export function DrippyGooTrail({ motion, opacity }: DrippyGooTrailProps) {
  const uid = useId().replace(/:/g, '');
  const gooId = `drippy-goo-${uid}`;
  const fillId = `drippy-goo-fill-${uid}`;
  const glowId = `drippy-goo-glow-${uid}`;

  const { intensity, angle, trail } = motion;
  if (intensity < 0.05) return null;

  const rad = (angle * Math.PI) / 180;
  const gotas = DROPS.map((drop) => {
    const passado = trail[drop.sample];
    const r = drop.radius * (0.45 + 0.55 * intensity);
    if (passado) {
      const { dx, dy } = limitar(passado.dx * TRAIL_GAIN * intensity, passado.dy * TRAIL_GAIN * intensity, r);
      return { cx: 50 + dx, cy: 50 + dy, r };
    }
    const bruto = (drop.sample / 11) * 128 * intensity;
    const { dx, dy } = limitar(-Math.cos(rad) * bruto, -Math.sin(rad) * bruto, r);
    return { cx: 50 + dx, cy: 50 + dy, r };
  });

  return (
    <svg
      viewBox={shapes.DrippyGooTrail_0}
      aria-hidden="true"
      style={{
        position: 'absolute',
        inset: '-100%',
        width: '300%',
        height: '300%',
        zIndex: 0,
        pointerEvents: 'none',
        opacity,
        overflow: 'hidden',
      }}
    >
      <defs>
        <filter id={gooId} x={shapes.DrippyGooTrail_1} y={shapes.DrippyGooTrail_2} width="200%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="9" result="blur" />
          {}
          <feColorMatrix
            in="blur"
            mode="matrix"
            values={shapes.DrippyGooTrail_3}
          />
        </filter>
        <radialGradient id={fillId} cx={shapes.DrippyGooTrail_4} cy={shapes.DrippyGooTrail_5} r={shapes.DrippyGooTrail_6}>
          <stop offset={shapes.DrippyGooTrail_7} stopColor={shapes.DrippyGooTrail_8} />
          <stop offset={shapes.DrippyGooTrail_9} stopColor={shapes.DrippyGooTrail_10} />
          <stop offset={shapes.DrippyGooTrail_11} stopColor={shapes.DrippyGooTrail_12} />
        </radialGradient>
        {}
        <linearGradient id={glowId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset={shapes.DrippyGooTrail_13} stopColor={shapes.DrippyGooTrail_14} />
          <stop offset={shapes.DrippyGooTrail_15} stopColor={shapes.DrippyGooTrail_16} />
        </linearGradient>
      </defs>

      {}
      <g filter={`url(#${gooId})`}>
        {}
        <circle cx={shapes.DrippyGooTrail_17} cy={shapes.DrippyGooTrail_18} r={shapes.DrippyGooTrail_19} fill={`url(#${glowId})`} opacity={0.5} />
        {gotas.map((g, i) => (
          <circle key={`glow-${i}`} cx={g.cx} cy={g.cy} r={g.r + 4} fill={`url(#${glowId})`} opacity={0.5} />
        ))}

        {}
        <circle cx={shapes.DrippyGooTrail_20} cy={shapes.DrippyGooTrail_21} r={shapes.DrippyGooTrail_22} fill={`url(#${fillId})`} />
        {gotas.map((g, i) => (
          <circle key={i} cx={g.cx} cy={g.cy} r={g.r} fill={`url(#${fillId})`} />
        ))}
      </g>
    </svg>
  );
}
