"use client";
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
} from "framer-motion";
import { ReactNode, useRef } from "react";

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  tiltAmount?: number;
  variants?: any;
}

export function TiltCard({
  children,
  className,
  tiltAmount = 5,
  variants,
}: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const rotateX = useSpring(
    useTransform(mouseY, [-0.5, 0.5], [tiltAmount, -tiltAmount]),
    { stiffness: 150, damping: 20 }
  );
  const rotateY = useSpring(
    useTransform(mouseX, [-0.5, 0.5], [-tiltAmount, tiltAmount]),
    { stiffness: 150, damping: 20 }
  );

  const lightX = useTransform(mouseX, [-0.5, 0.5], ["0%", "100%"]);
  const lightY = useTransform(mouseY, [-0.5, 0.5], ["0%", "100%"]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  // Compose the radial gradient background as a single MotionValue<string>
  const lightGradient = useTransform(
    [lightX, lightY] as never,
    ([x, y]: [string, string]) =>
      `radial-gradient(circle at ${x} ${y}, rgba(220, 38, 38, 0.25) 0%, transparent 60%)`
  );

  return (
    <motion.div
      ref={ref}
      variants={variants}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: "preserve-3d",
        transformPerspective: 1000,
      }}
      className={`relative ${className ?? ""}`}
    >
      <motion.div
        className="pointer-events-none absolute inset-0 rounded-2xl"
        style={{ background: lightGradient } as unknown as React.CSSProperties}
      />
      {children}
    </motion.div>
  );
}
