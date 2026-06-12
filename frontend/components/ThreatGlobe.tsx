"use client";
import createGlobe from "cobe";
import { useEffect, useRef } from "react";
import { useSpring } from "framer-motion";

export function ThreatGlobe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerInteracting = useRef<number | null>(null);
  const pointerInteractionMovement = useRef(0);
  const fadeIn = useSpring(0, { stiffness: 80, damping: 20 });

  useEffect(() => {
    let phi = 0;
    let width = 0;
    const onResize = () => {
      if (canvasRef.current) {
        width = canvasRef.current.offsetWidth;
      }
    };
    window.addEventListener("resize", onResize);
    onResize();
    fadeIn.set(1);

    if (!canvasRef.current) return;

    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: width * 2,
      height: width * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 1.0,
      baseColor: [0.15, 0.15, 0.18],
      markerColor: [0.86, 0.15, 0.15], // CRIMSON for threats
      glowColor: [0.05, 0.05, 0.1],
      markers: [
        // India threat hotspots
        { location: [19.076, 72.8777], size: 0.08 }, // Mumbai
        { location: [12.9716, 77.5946], size: 0.08 }, // Bangalore
        { location: [28.7041, 77.1025], size: 0.06 }, // Delhi
        { location: [22.5726, 88.3639], size: 0.05 }, // Kolkata
        { location: [13.0827, 80.2707], size: 0.06 }, // Chennai
        { location: [17.385, 78.4867], size: 0.05 }, // Hyderabad
        { location: [26.9124, 75.7873], size: 0.05 }, // Jaipur
        { location: [23.2599, 77.4126], size: 0.04 }, // Bhopal
        // Global fraud centers
        { location: [40.7128, -74.006], size: 0.05 }, // New York
        { location: [51.5074, -0.1278], size: 0.05 }, // London
        { location: [35.6762, 139.6503], size: 0.04 }, // Tokyo
      ],
    });

    // Animate rotation via update() — cobe v2 API
    let raf = 0;
    const tick = () => {
      if (!pointerInteracting.current) {
        phi += 0.003;
      }
      globe.update({
        phi: phi + pointerInteractionMovement.current,
        width: width * 2,
        height: width * 2,
      });
      raf = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      globe.destroy();
      window.removeEventListener("resize", onResize);
    };
  }, [fadeIn]);

  return (
    <div className="relative mx-auto h-125 w-125 max-w-full opacity-50">
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: "100%",
          contain: "layout paint size",
          cursor: "grab",
        }}
        onPointerDown={(e) => {
          pointerInteracting.current =
            e.clientX - (e.currentTarget.getBoundingClientRect().left ?? 0);
          if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
        }}
        onPointerUp={() => {
          pointerInteracting.current = null;
          if (canvasRef.current) canvasRef.current.style.cursor = "grab";
        }}
        onPointerOut={() => {
          pointerInteracting.current = null;
          if (canvasRef.current) canvasRef.current.style.cursor = "grab";
        }}
        onMouseMove={(e) => {
          if (pointerInteracting.current !== null) {
            const delta = e.clientX - pointerInteracting.current;
            pointerInteractionMovement.current = delta * 0.01;
          }
        }}
      />
    </div>
  );
}
