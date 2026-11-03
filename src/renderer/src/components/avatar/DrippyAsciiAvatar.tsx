// SPDX-License-Identifier: GPL-3.0-only
import shapes from '../../../../../assets/drippy/shapes.json';
import { useEffect, useState, useRef, type CSSProperties } from 'react';
import { motion } from 'framer-motion';
import { useDragMotion } from './useDragMotion';
import { DrippyGooTrail } from './DrippyGooTrail';
import { CoveringHands } from './DrippyHands';
import { SleepPillow, SleepZs } from './DrippySleep';
import { CoffeeMug } from './DrippyProps';
import { DrippyMusicNotes } from './DrippyMusicNotes';
import '../../../../../assets/drippy/appearance.css';

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

interface DrippyAsciiAvatarProps {
  state?: 'idle' | 'happy' | 'angry' | 'sleepy' | 'confused' | 'dizzy' | 'curious' | 'excited' | 'asleep' | 'sad' | 'scared' | 'dramatic' | 'shy';
  
  startled?: boolean;
  held?: boolean;
  gaze?: number[];
  
  eyesClosed?: boolean;
  size?: 'sm' | 'md' | 'lg' | number;
  className?: string;
  onClick?: () => void;
  
  onDoubleClick?: () => void;
  
  musicPlaying?: boolean;
  
  draggable?: boolean;
  
  bubbleOpacity?: number;
  
  forceCoffee?: boolean;
  
  coffeeFalling?: boolean;
  
}


const MOUTHS = shapes.mouths;

interface EyeParams {
  rx: number;
  ry: number;
  happy: boolean;
  dy: number;
}

function getEyeParams(
  state: string,
  isDragging: boolean,
  blink: boolean,
  side: 'left' | 'right',
  eyesClosed = false,
): EyeParams {
  const base: EyeParams = { rx: 4.6, ry: 5.6, happy: false, dy: 0 };
  if (eyesClosed) return { ...base, ry: 0.6 };
  if (state === 'asleep') return { ...base, rx: 5.2, ry: 0.75, dy: 2.4 };
  if (state === 'dizzy') return { ...base, rx: 5.6, ry: 5.6 };
  if (state === 'angry') return { ...base, ry: 2.8 };
  if (isDragging) return { ...base, rx: 5.4, ry: 7 };
  if (blink) return { ...base, ry: 0.7 };
  switch (state) {
    case 'shy': return { ...base, ry: 2.5, dy: 2 };
    case 'sad': return { ...base, ry: 3.5, dy: 1 };
    case 'scared': return { ...base, rx: 5.5, ry: 7 };
    case 'happy':
    case 'excited':
      return { ...base, happy: true };
    case 'sleepy':
      return { ...base, ry: 2, dy: 1.5 };
    case 'confused':
      return side === 'left'
        ? { ...base, rx: 5, ry: 6.2 }
        : { ...base, rx: 4.3, ry: 4.6 };
    case 'curious':
      return { ...base, rx: 5.6, ry: 6.8, dy: -0.8 };
    default:
      return base;
  }
}

export function DrippyAsciiAvatar({
  state = 'idle',
  size = 'md',
  className = '',
  onClick,
  onDoubleClick,
  draggable = true,
  bubbleOpacity = 1,
  musicPlaying = false,
  eyesClosed = false,
  startled = false,
  forceCoffee = false,
  coffeeFalling = false,
  held,
  gaze,
}: DrippyAsciiAvatarProps) {
  const [internalDragging, setIsDragging] = useState(false);
  const isDragging = held ?? internalDragging;
  const [isSquished, setIsSquished] = useState(false);
  const [isYawning, setIsYawning] = useState(false);
  useEffect(() => {
    if (state !== 'asleep') {
      setIsYawning(false);
      return;
    }
    setIsYawning(true);
    const t = window.setTimeout(() => setIsYawning(false), 1400);
    return () => window.clearTimeout(t);
  }, [state]);
  const [isWaking, setIsWaking] = useState(false);
  const estadoAnteriorRef = useRef(state);
  useEffect(() => {
    const dormiaAntes = estadoAnteriorRef.current === 'asleep';
    estadoAnteriorRef.current = state;
    if (!dormiaAntes || state === 'asleep' || startled) return;
    setIsWaking(true);
    const t = window.setTimeout(() => setIsWaking(false), 1100);
    return () => window.clearTimeout(t);
  }, [state, startled]);
  const [hasCoffee, setHasCoffee] = useState(false);
  const madrugada = state === 'idle' && !isDragging && !eyesClosed;
  useEffect(() => {
    if (!madrugada) {
      setHasCoffee(false);
      return;
    }
    let alive = true;
    let hideTimer: number;
    const agendar = (): number =>
      window.setTimeout(() => {
        if (!alive) return;
        const hora = new Date().getHours();
        if (hora >= 23 || hora < 3) {
          setHasCoffee(true);
          hideTimer = window.setTimeout(() => {
            setHasCoffee(false);
            proximo = agendar();
          }, 7000);
        } else {
          proximo = agendar();
        }
      }, 180000 + Math.random() * 360000);
    let proximo = agendar();
    return () => {
      alive = false;
      window.clearTimeout(proximo);
      window.clearTimeout(hideTimer);
    };
  }, [madrugada]);
  const [dancingNow, setDancingNow] = useState(false);
  const [lightDance, setLightDance] = useState(false);
  useEffect(() => {
    let onTimer: ReturnType<typeof setTimeout>;
    let offTimer: ReturnType<typeof setTimeout>;
    let idleTimer: ReturnType<typeof setTimeout>;
    let leveTimer: ReturnType<typeof setTimeout>;
    let cancelled = false;

    if (musicPlaying) {
      setLightDance(false);
      const cicloDanca = () => {
        setDancingNow(true);
        onTimer = setTimeout(() => {
          if (cancelled) return;
          setDancingNow(false);
          offTimer = setTimeout(() => {
            if (!cancelled) cicloDanca();
          }, 18000 + Math.random() * 20000);
        }, 4000 + Math.random() * 4000);
      };
      cicloDanca();
    } else {
      setDancingNow(false);
      const agendarLeve = () => {
        idleTimer = setTimeout(() => {
          if (cancelled) return;
          setLightDance(true);
          leveTimer = setTimeout(() => {
            if (!cancelled) setLightDance(false);
          }, 2200 + Math.random() * 1800);
          agendarLeve();
        }, 40000 + Math.random() * 80000);
      };
      agendarLeve();
    }

    return () => {
      cancelled = true;
      clearTimeout(onTimer);
      clearTimeout(offTimer);
      clearTimeout(idleTimer);
      clearTimeout(leveTimer);
    };
  }, [musicPlaying]);

  useEffect(() => {
    if (!isSquished) return;
    const release = () => setIsSquished(false);
    const timer = window.setTimeout(release, 170);
    window.addEventListener('pointerup', release);
    window.addEventListener('pointercancel', release);
    window.addEventListener('blur', release);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('pointerup', release);
      window.removeEventListener('pointercancel', release);
      window.removeEventListener('blur', release);
    };
  }, [isSquished]);
  const [blink, setBlink] = useState({ l: false, r: false });
  const [pupil, setPupil] = useState({ x: 0, y: 0 });
  const [mouth, setMouth] = useState<{ d: string; fillOpacity: number }>(MOUTHS.soft);
  const [microSmile, setMicroSmile] = useState(false);
  const earGlyphs = ['^', '^'] as const;

  const blinkRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pupilRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const moodRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafRef = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const dragMotion = useDragMotion(containerRef);
  const mouseRef = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, []);
  const isTalking = false;
  const eyesCanBlink = !isDragging && !eyesClosed && state !== 'happy' && state !== 'angry' && state !== 'asleep';
  const cochilando = state === 'sleepy';

  useEffect(() => {
    let active = true;
    let reopenTimer: ReturnType<typeof setTimeout>;
    const loop = () => {
      if (!active) return;
      blinkRef.current = setTimeout(() => {
        if (!active) return;
        const wink = !cochilando && Math.random() < 0.25;
        const left = Math.random() < 0.5;
        setBlink(wink ? { l: left, r: !left } : { l: true, r: true });
        reopenTimer = setTimeout(
          () => { if (active) setBlink({ l: false, r: false }); },
          cochilando ? 620 : wink ? 200 : 130,
        );
        loop();
      }, cochilando ? Math.random() * 900 + 650 : Math.random() * 3800 + 2200);
    };
    if (eyesCanBlink) loop();
    else setBlink({ l: false, r: false });
    return () => {
      active = false;
      if (blinkRef.current) clearTimeout(blinkRef.current);
      clearTimeout(reopenTimer);
    };
  }, [eyesCanBlink, cochilando]);

  useEffect(() => {
    let active = true;
    let glanceAwayUntil = 0;
    let nextGlanceAt = performance.now() + 3500 + Math.random() * 4500;

    let previousMouse: { x: number; y: number } | null = null;
    let previousGaze: { x: number; y: number } | null = null;
    const lookAtCursor = () => {
      const el = containerRef.current;
      const m = mouseRef.current;
      if (!el || !m) return null;
      if (previousMouse?.x === m.x && previousMouse?.y === m.y) return previousGaze;
      previousMouse = { ...m };
      const r = el.getBoundingClientRect();
      const dx = m.x - (r.left + r.width / 2);
      const dy = m.y - (r.top + r.height / 2);
      const dist = Math.hypot(dx, dy) || 1;
      const k = Math.min(1, dist / 140);
      previousGaze = { x: (dx / dist) * 2.4 * k, y: (dy / dist) * 1.6 * k };
      return previousGaze;
    };

    const loop = () => {
      if (!active) return;
      let delay = 90;
      const now = performance.now();

      if (state === 'dizzy') {
        const t = now / 180;
        setPupil({ x: Math.cos(t) * 2.6, y: Math.sin(t) * 1.8 });
        delay = 45;
      } else if (isDragging) {
        setPupil({ x: 0, y: 0 });
        delay = 400;
      } else if (now < glanceAwayUntil) {
        delay = 220;
      } else {
        if (now >= nextGlanceAt && state === 'idle') {
          glanceAwayUntil = now + 500 + Math.random() * 500;
          nextGlanceAt = now + 5000 + Math.random() * 6000;
          setPupil({ x: (Math.random() * 2 - 1) * 2.4, y: (Math.random() * 2 - 1) * 1.2 });
          delay = 220;
        } else {
          const p = lookAtCursor();
          if (p) {
            setPupil(prev =>
              Math.abs(prev.x - p.x) > 0.15 || Math.abs(prev.y - p.y) > 0.15 ? p : prev
            );
          }
        }
      }
      pupilRef.current = setTimeout(loop, delay);
    };
    loop();
    return () => {
      active = false;
      if (pupilRef.current) clearTimeout(pupilRef.current);
    };
  }, [state, isDragging, size]);

  useEffect(() => {
    let active = true;
    let smileTimer: ReturnType<typeof setTimeout>;
    const loop = () => {
      if (!active) return;
      moodRef.current = setTimeout(() => {
        if (!active) return;
        setMicroSmile(true);
        smileTimer = setTimeout(() => { if (active) setMicroSmile(false); }, 1600);
        loop();
      }, Math.random() * 8000 + 6000);
    };
    if (state === 'idle' && !isDragging) loop();
    else setMicroSmile(false);
    return () => {
      active = false;
      if (moodRef.current) clearTimeout(moodRef.current);
      clearTimeout(smileTimer);
    };
  }, [state, isDragging]);

  useEffect(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    if (state === 'dizzy') {
      let flip = false;
      setMouth(MOUTHS.wavy);
      const wobble = setInterval(() => {
        flip = !flip;
        setMouth(flip ? MOUTHS.wavy2 : MOUTHS.wavy);
      }, 420);
      return () => clearInterval(wobble);
    }

    if (state === 'angry') {
      setMouth(MOUTHS.frown);
      return;
    }

    if (isDragging) {
      setMouth(MOUTHS.oBig);
      return;
    }

    switch (state) {
      case 'sad': setMouth(MOUTHS.frown); break;
      case 'scared': setMouth(MOUTHS.oBig); break;
      case 'dramatic': setMouth(MOUTHS.wavy); break;
      case 'happy': setMouth(MOUTHS.grin); break;
      case 'excited': setMouth(MOUTHS.grin); break;
      case 'confused': setMouth(MOUTHS.soft); break;
      case 'curious': setMouth(MOUTHS.soft); break;
      case 'asleep': setMouth(isYawning ? MOUTHS.oBig : MOUTHS.oSmall); break;
      default: setMouth(microSmile ? MOUTHS.smile : MOUTHS.soft);
    }
  }, [state, isTalking, isDragging, microSmile, isYawning]);

  const sphereSize = `${typeof size === 'number' ? size : size === 'sm' ? 80 : size === 'lg' ? 180 : 136}px`;

  const moodClass =
    state === 'dizzy'
      ? 'text-lime-400 drop-shadow-[0_0_5px_rgba(163,230,53,0.7)]'
      : state === 'angry'
      ? 'text-red-500 drop-shadow-[0_0_4px_rgba(239,68,68,0.6)]'
      : state === 'happy'
      ? 'text-emerald-400 drop-shadow-[0_0_4px_rgba(52,211,153,0.6)]'
      : state === 'excited'
      ? 'text-fuchsia-400 drop-shadow-[0_0_5px_rgba(232,121,249,0.7)]'
      : state === 'confused'
      ? 'text-blue-400 drop-shadow-[0_0_4px_rgba(96,165,250,0.6)]'
      : state === 'curious'
      ? 'text-cyan-400 drop-shadow-[0_0_4px_rgba(34,211,238,0.6)]'
      : 'text-primary/95 drop-shadow-[0_0_4px_rgba(var(--drippy-glow-rgb),0.6)]';

  const leftEye = getEyeParams(
    state,
    isDragging,
    blink.l,
    'left',
    eyesClosed,
  );
  const rightEye = getEyeParams(
    state,
    isDragging,
    blink.r,
    'right',
    eyesClosed,
  );
  const earsAlert = state === 'happy' || state === 'excited' || isDragging;

  const gazePupil = gaze ? { x: gaze[0] * 2.4, y: gaze[1] * 1.6 } : pupil;

  const renderEye = (cx: number, eye: EyeParams) => (
    <g>
      <motion.path
        d={`M ${cx - 5} 37 Q ${cx} 29 ${cx + 5} 37`}
        stroke={shapes.DrippyAsciiAvatar_0} strokeWidth={shapes.DrippyAsciiAvatar_1} strokeLinecap={shapes.DrippyAsciiAvatar_2 as 'round'} fill={shapes.DrippyAsciiAvatar_3}
        initial={false}
        animate={{ opacity: eye.happy ? 1 : 0 }}
        transition={{ duration: 0.15 }}
      />
      <motion.g initial={false} animate={{ opacity: eye.happy ? 0 : 1 }} transition={{ duration: 0.15 }}>
        <motion.ellipse
          fill={shapes.DrippyAsciiAvatar_4}
          initial={false}
          animate={{ rx: eye.rx, ry: eye.ry, cx: cx + gazePupil.x, cy: 34 + eye.dy + gazePupil.y * 0.8 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
        />
        <motion.circle
          r={shapes.DrippyAsciiAvatar_5} fill={shapes.DrippyAsciiAvatar_6}
          initial={false}
          animate={{
            cx: cx + gazePupil.x + 1.6,
            cy: 31.8 + eye.dy + gazePupil.y * 0.8,
            opacity: eye.ry > 3 ? 0.85 : 0
          }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
        />
      </motion.g>
    </g>
  );

  const renderEar = (cx: number, glyph: string, delay: number) => (
    <motion.g
      initial={false}
      animate={earsAlert ? { rotate: [0, -6, 6, 0], y: -1 } : { rotate: 0, y: 0 }}
      transition={earsAlert ? { duration: 0.6, repeat: Infinity, repeatDelay: 1.2, delay } : { duration: 0.3 }}
      style={{ originX: `${cx}px`, originY: '18px' }}
    >
      <text
        x={cx} y={shapes.DrippyAsciiAvatar_7} textAnchor="middle"
        fill={shapes.DrippyAsciiAvatar_8} fontSize={shapes.DrippyAsciiAvatar_9} fontWeight={shapes.DrippyAsciiAvatar_10}
        fontFamily={shapes.DrippyAsciiAvatar_11}
      >{glyph}</text>
    </motion.g>
  );

  return (
    <motion.div
      ref={containerRef}
      drag={draggable}
      dragMomentum={false}
      onDragStart={draggable ? () => setIsDragging(true) : undefined}
      onDragEnd={draggable ? () => setIsDragging(false) : undefined}
      whileDrag={
        draggable
          ? {
              scale: 1.15,
              rotate: [-4, 4],
              transition: {
                rotate: { duration: 0.5, repeat: Infinity, repeatType: 'mirror', ease: 'easeInOut' },
                scale: { duration: 0.15 },
              },
            }
          : undefined
      }
      animate={isSquished ? { scale: 0.93, scaleY: 0.88 } : { scale: 1, scaleY: 1 }}
      transition={{ type: 'spring', stiffness: 520, damping: 13, mass: 0.5 }}
      onPointerDown={() => { setIsSquished(true); }}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      className={cn(
        'drippy-avatar-container font-mono select-none transition-colors duration-300',
        onClick || onDoubleClick ? 'cursor-pointer' : '',
        className
      )}
      style={{
        '--avatar-size': sphereSize
      } as CSSProperties}
    >
      <DrippyGooTrail motion={dragMotion} opacity={bubbleOpacity} />
      <SleepPillow asleep={state === 'asleep'} waking={isWaking} startled={startled} />

      {}
      <motion.div
        className="drippy-sleep-body"
        animate={
          startled
            ? { y: [7, -24, 4, -2, 0], rotate: [-11, 14, -5, 2, 0], scale: [1, 1.2, 0.94, 1.04, 1] }
            : state === 'asleep'
            ? { y: [7, 8.5, 7], rotate: [-11, -12.5, -11], scale: [1, 1.025, 1] }
            : isWaking
            ? // Espreguiça: estica pra cima, desendireita e assenta.
              { y: [7, -7, 0], rotate: [-11, 3, 0], scale: [1, 1.09, 1] }
            : cochilando
            ? // Cabeceada de quem cochila sem querer: a cabeça vai pendendo
              { y: [0, 8, 16, 15, 1, 0], rotate: [0, 4, 13, 12, -2, 0], scale: [1, 1, 1.01, 1.01, 0.99, 1] }
            : dancingNow
            ? // Dança: pulinho no tempo + gingado pro lado. A rotação leva o
              { y: [0, -3.5, 0], rotate: [-2.8, 2.8, -2.8], scale: [1, 1.018, 1] }
            : lightDance
            ? // Gingado leve de idle (sem música real tocando), mesma ideia,
              { y: [0, -2.5, 0], rotate: [-2, 2, -2], scale: [1, 1.015, 1] }
            : { y: 0, rotate: 0, scale: 1 }
        }
        transition={
            startled
            ? { duration: 0.95, times: [0, 0.24, 0.46, 0.72, 1], ease: 'easeOut' }
            : isWaking
            ? { duration: 1, ease: [0.34, 1.3, 0.64, 1] }
            : cochilando
            ? { duration: 5.2, times: [0, 0.42, 0.6, 0.72, 0.86, 1], repeat: Infinity, ease: 'easeInOut' }
            : dancingNow
            ? {
                y: { duration: 1.05, repeat: Infinity, ease: 'easeInOut' },
                scale: { duration: 1.05, repeat: Infinity, ease: 'easeInOut' },
                rotate: { duration: 2.1, repeat: Infinity, ease: 'easeInOut' },
              }
            : lightDance
            ? {
                y: { duration: 0.9, repeat: Infinity, ease: 'easeInOut' },
                scale: { duration: 0.9, repeat: Infinity, ease: 'easeInOut' },
                rotate: { duration: 1.8, repeat: Infinity, ease: 'easeInOut' },
              }
            : state === 'asleep'
            ? {
                scale: { duration: 4.2, repeat: Infinity, ease: 'easeInOut' },
                y: { type: 'spring', stiffness: 90, damping: 15 },
                rotate: { type: 'spring', stiffness: 90, damping: 15 },
              }
            : { type: 'spring', stiffness: 260, damping: 20 }
        }
      >
      {}
      <div
        className="drippy-goo-body"
        style={{
          transform: `rotate(${dragMotion.angle}deg) scale(${1 + 0.3 * dragMotion.intensity}, ${1 - 0.19 * dragMotion.intensity}) rotate(${-dragMotion.angle}deg)`,
        }}
      >
        <motion.div
          animate={{ opacity: bubbleOpacity }}
          className={cn('drippy-avatar-ring', isTalking && 'drippy-avatar-ring--talking')}
        />
        <motion.div
          animate={{ opacity: bubbleOpacity }}
          className="drippy-avatar-core"
        />

      <div className="drippy-avatar-face">
        <motion.div
          className={cn('drippy-face-bob w-full h-full transition-colors duration-300', moodClass)}
          animate={
            state === 'angry'
              ? { x: [0, -1.5, 1.5, -1.5, 0] }
              : state === 'dizzy'
              ? { rotate: [-7, 6, -8, 5, -7], x: [-2, 2, -3, 2, -2], y: [0, -2, 1, -1.5, 0] }
              : state === 'sleepy'
              ? { y: [0, 1.5, 0] }
              : state === 'excited'
              ? { y: [0, -6, 0, -3, 0] }
              : state === 'curious'
              ? { rotate: [0, -5, -5, 0], y: [0, -1.5, -1.5, 0] }
              : state === 'confused'
              ? { rotate: [0, 4, -3, 2, 0], x: [0, 1.2, -1.2, 0.6, 0] }
              : { x: 0, y: 0, rotate: 0 }
          }
          transition={
            state === 'angry'
              ? { duration: 0.4, repeat: Infinity }
              : state === 'dizzy'
              ? { duration: 1.4, repeat: Infinity, ease: 'easeInOut' }
              : state === 'sleepy'
              ? { duration: 2.4, repeat: Infinity, ease: 'easeInOut' }
              : state === 'excited'
              ? { duration: 0.6, repeat: Infinity, ease: 'easeInOut' }
              : state === 'curious'
              ? { duration: 2.3, repeat: Infinity, ease: 'easeInOut', repeatDelay: 0.7 }
              : state === 'confused'
              ? { duration: 1.8, repeat: Infinity, ease: 'easeInOut', repeatDelay: 0.5 }
              : { duration: 0.2 }
          }
        >
          <svg viewBox={shapes.DrippyAsciiAvatar_12} className="w-full h-full" aria-hidden="true">
            {renderEar(30, earGlyphs[0], 0)}
            {renderEar(70, earGlyphs[1], 0.15)}

            {renderEye(30, leftEye)}
            {renderEye(70, rightEye)}



            {(state === 'happy' || state === 'excited') && (
              <g>
                {[
                  { x: 14, y: 16, delay: 0 },
                  { x: 88, y: 20, delay: 0.35 },
                  { x: 8, y: 42, delay: 0.7 },
                ].map((s, i) => (
                  <motion.text
                    key={i}
                    x={s.x} y={s.y} fill={shapes.DrippyAsciiAvatar_13} fontSize={shapes.DrippyAsciiAvatar_14} fontWeight={shapes.DrippyAsciiAvatar_15}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: [0, 1, 0], scale: [0.5, 1, 0.5] }}
                    transition={{ duration: state === 'excited' ? 0.8 : 1.4, repeat: Infinity, delay: s.delay, ease: 'easeInOut' }}
                    style={{ transformOrigin: `${s.x}px ${s.y}px` }}
                  >✦</motion.text>
                ))}
              </g>
            )}

            {}
            {state === 'curious' && (
              <motion.text
                x={shapes.DrippyAsciiAvatar_16} y={shapes.DrippyAsciiAvatar_17} fill={shapes.DrippyAsciiAvatar_18} fontSize={shapes.DrippyAsciiAvatar_19} fontWeight={shapes.DrippyAsciiAvatar_20}
                fontFamily={shapes.DrippyAsciiAvatar_21}
                initial={{ opacity: 0, y: 26, rotate: -8 }}
                animate={{ opacity: [0, 1, 1, 0], y: [26, 15, 10], rotate: [-8, 8, -5], scale: [0.8, 1.08, 1] }}
                transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut' }}
              >?</motion.text>
            )}

            <motion.path
              stroke={shapes.DrippyAsciiAvatar_22}
              strokeWidth={shapes.DrippyAsciiAvatar_23}
              strokeLinecap={shapes.DrippyAsciiAvatar_24 as 'round'}
              strokeLinejoin="round"
              fill={shapes.DrippyAsciiAvatar_25}
              initial={false}
              animate={{ d: mouth.d, fillOpacity: mouth.fillOpacity, x: 0 }}
              transition={{ duration: isTalking ? 0.09 : 0.22, ease: 'easeOut' }}
            />


            <CoveringHands active={eyesClosed} />
          </svg>
        </motion.div>
        </div>
      </div>
      </motion.div>

      {}
      <SleepZs asleep={state === 'asleep' && !isYawning} waking={isWaking} startled={startled} moodClass={moodClass} />
      <CoffeeMug active={(hasCoffee || forceCoffee)} falling={coffeeFalling} moodClass={moodClass} />
      {}
      <DrippyMusicNotes active={dancingNow} moodClass={moodClass} />
    </motion.div>
  );
}
