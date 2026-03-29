'use client';

import { useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { SlatAssembly } from './SlatAssembly';
import type { CanonicalConfig } from '@/types/schema';

interface ViewportProps {
  config: CanonicalConfig;
  showExploded?: boolean;
  showBacking?: boolean;
  theme?: 'dark' | 'light';
  slatColor?: string;
  backingColor?: string;
}

function ClearColor({ color }: { color: string }) {
  const { gl } = useThree();
  useEffect(() => {
    gl.setClearColor(color);
  }, [gl, color]);
  return null;
}

export function Viewport({
  config,
  showExploded = false,
  showBacking = true,
  theme = 'dark',
  slatColor,
  backingColor,
}: ViewportProps) {
  const width = config.boundary.width;
  const height = config.boundary.height;

  const isDark = theme === 'dark';
  const bgClass = isDark ? 'bg-gray-900' : 'bg-gray-100';
  const clearColor = isDark ? '#111827' : '#f3f4f6';
  const cellColor = isDark ? '#333333' : '#cccccc';
  const sectionColor = isDark ? '#555555' : '#999999';
  const ambientIntensity = isDark ? 0.4 : 0.6;
  const mainLightIntensity = isDark ? 0.8 : 1.0;
  const fillLightIntensity = isDark ? 0.3 : 0.4;

  return (
    <div className={`w-full h-full min-h-[400px] ${bgClass} rounded-lg overflow-hidden`}>
      <Canvas
        camera={{
          position: [width * 0.8, height * 0.6, width * 0.8],
          fov: 50,
          near: 0.1,
          far: 1000,
        }}
      >
        <ClearColor color={clearColor} />
        <ambientLight intensity={ambientIntensity} />
        <directionalLight position={[10, 10, 5]} intensity={mainLightIntensity} castShadow />
        <directionalLight position={[-5, 5, -5]} intensity={fillLightIntensity} />

        <SlatAssembly
          config={config}
          showExploded={showExploded}
          showBacking={showBacking}
          slatColor={slatColor}
          backingColor={backingColor}
        />

        <Grid
          infiniteGrid
          cellSize={1}
          sectionSize={12}
          fadeDistance={100}
          cellColor={cellColor}
          sectionColor={sectionColor}
        />

        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.05}
          minDistance={5}
          maxDistance={200}
        />
      </Canvas>
    </div>
  );
}
