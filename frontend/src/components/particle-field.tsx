"use client";

import { useMemo } from "react";

interface Particle {
  id: number;
  left: number;
  top: number;
  delay: number;
}

/** THEME: lightweight ambient data points; deterministic to avoid hydration mismatch. */
export function ParticleField({ count = 18 }: { count?: number }) {
  const particles = useMemo<Particle[]>(
    () => Array.from({ length: count }, (_, id) => ({
      id,
      left: (id * 37) % 100,
      top: (id * 61) % 100,
      delay: (id % 6) * 0.7,
    })),
    [count],
  );

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(0,255,245,.07)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,245,.07)_1px,transparent_1px)] [background-size:52px_52px]" />
      {particles.map((particle) => (
        <span
          key={particle.id}
          className="absolute h-1 w-1 bg-cyan/40"
          style={{ left: `${particle.left}%`, top: `${particle.top}%`, animationDelay: `${particle.delay}s` }}
        />
      ))}
    </div>
  );
}
