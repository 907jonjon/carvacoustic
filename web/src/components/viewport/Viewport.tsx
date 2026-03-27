'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { SlatAssembly } from './SlatAssembly';
import type { CanonicalConfig } from '@/types/schema';

interface ViewportProps {
  config: CanonicalConfig;
  showExploded?: boolean;
  showBacking?: boolean;
}

export function Viewport({ config, showExploded = false, showBacking = true }: ViewportProps) {
  const width = config.boundary.width;
  const height = config.boundary.height;

  return (
    <div className="w-full h-full min-h-[400px] bg-gray-900 rounded-lg overflow-hidden">
      <Canvas
        camera={{
          position: [width * 0.8, height * 0.6, width * 0.8],
          fov: 50,
          near: 0.1,
          far: 1000,
        }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 5]} intensity={0.8} castShadow />
        <directionalLight position={[-5, 5, -5]} intensity={0.3} />

        <SlatAssembly
          config={config}
          showExploded={showExploded}
          showBacking={showBacking}
        />

        <Grid
          infiniteGrid
          cellSize={1}
          sectionSize={12}
          fadeDistance={100}
          cellColor="#333333"
          sectionColor="#555555"
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
