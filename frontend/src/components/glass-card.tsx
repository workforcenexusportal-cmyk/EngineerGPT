"use client";

import { motion, type MotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  delay?: number;
}

/** THEME: reusable clipped glass HUD panel with a restrained cyan edge glow. */
export function GlassCard({ children, className, hover = true, delay = 0 }: GlassCardProps) {
  const motionProps: MotionProps = {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.35, delay, ease: [0.22, 1, 0.36, 1] },
    ...(hover ? { whileHover: { y: -3 } } : {}),
  };

  return (
    <motion.div {...motionProps} className={cn("glass p-5", hover && "glass-hover", className)}>
      {children}
    </motion.div>
  );
}
