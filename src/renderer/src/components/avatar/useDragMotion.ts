import { useEffect, useRef, useState } from 'react';

export interface DragMotion {
  
  intensity: number;
  
  angle: number;
  
  trail: Array<{ dx: number; dy: number }>;
}

const ZERO: DragMotion = { intensity: 0, angle: 0, trail: [] };


const TRAIL_SAMPLES = 14;


const MAX_SPEED = 34;

const SETTLE_MS = 700;

export function useDragMotion(ref: React.RefObject<HTMLElement>): DragMotion {
  const [motion, setMotion] = useState<DragMotion>(ZERO);
  const motionRef = useRef<DragMotion>(ZERO);

  useEffect(() => {
    let rafId = 0;
    let stopTimer = 0;
    let running = false;
    let last: { x: number; y: number } | null = null;
    let history: Array<{ x: number; y: number }> = [];

    const measure = () => {
      const el = ref.current;
      if (!el) {
        rafId = requestAnimationFrame(measure);
        return;
      }
      const rect = el.getBoundingClientRect();
      const now = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };

      history.unshift(now);
      if (history.length > TRAIL_SAMPLES) history.length = TRAIL_SAMPLES;
      const porUnidade = rect.width > 0 ? rect.width / 100 : 1;

      if (last) {
        const dx = now.x - last.x;
        const dy = now.y - last.y;
        const speed = Math.hypot(dx, dy);
        const target = Math.min(1, speed / MAX_SPEED);
        const prev = motionRef.current;
        const smoothed = target > prev.intensity
          ? prev.intensity + (target - prev.intensity) * 0.55
          : prev.intensity + (target - prev.intensity) * 0.12;
        const angle = speed > 0.6 ? (Math.atan2(dy, dx) * 180) / Math.PI : prev.angle;

        if (Math.abs(smoothed - prev.intensity) > 0.004 || angle !== prev.angle) {
          const trail = history.slice(1).map((p) => ({
            dx: (p.x - now.x) / porUnidade,
            dy: (p.y - now.y) / porUnidade,
          }));
          const next = { intensity: smoothed, angle, trail };
          motionRef.current = next;
          setMotion(next);
        }
      }

      last = now;
      rafId = requestAnimationFrame(measure);
    };

    const start = (event: PointerEvent) => {
      if (event.button !== 0 || !(event.target instanceof Node) || !ref.current?.contains(event.target)) return;
      window.clearTimeout(stopTimer);
      if (running) return;
      running = true;
      last = null;
      history = [];
      rafId = requestAnimationFrame(measure);
    };

    const stopSoon = () => {
      if (!running) return;
      window.clearTimeout(stopTimer);
      stopTimer = window.setTimeout(() => {
        running = false;
        cancelAnimationFrame(rafId);
        motionRef.current = ZERO;
        setMotion(ZERO);
      }, SETTLE_MS);
    };
    window.addEventListener('pointerdown', start);
    window.addEventListener('pointerup', stopSoon);
    window.addEventListener('pointercancel', stopSoon);

    return () => {
      window.removeEventListener('pointerdown', start);
      window.removeEventListener('pointerup', stopSoon);
      window.removeEventListener('pointercancel', stopSoon);
      window.clearTimeout(stopTimer);
      cancelAnimationFrame(rafId);
    };
  }, [ref]);

  return motion;
}
