'use client';

import { useMemo } from 'react';
import * as THREE from 'three';
import type { CanonicalConfig, SurfaceConfig } from '@/types/schema';

interface SlatAssemblyProps {
  config: CanonicalConfig;
  showExploded: boolean;
  showBacking: boolean;
}

export function SlatAssembly({ config, showExploded, showBacking }: SlatAssemblyProps) {
  const slats = useMemo(() => generateSlatGeometries(config), [config]);

  const explodeOffset = showExploded ? config.slats.spacing * 2 : 0;

  return (
    <group>
      {slats.map((slat, i) => (
        <mesh
          key={`slat-${i}`}
          geometry={slat.geometry}
          position={[
            0,
            0,
            i * config.slats.spacing + (showExploded ? i * explodeOffset : 0),
          ]}
        >
          <meshStandardMaterial
            color="#8B6914"
            roughness={0.7}
            metalness={0.1}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}

      {showBacking && config.backing.enabled && (
        <mesh
          position={[
            config.boundary.width / 2,
            -config.slats.tab_depth / 2,
            ((config.slats.count - 1) * config.slats.spacing) / 2,
          ]}
        >
          <boxGeometry
            args={[
              config.boundary.width,
              config.backing.height,
              (config.slats.count - 1) * config.slats.spacing + config.slats.thickness,
            ]}
          />
          <meshStandardMaterial color="#A0522D" roughness={0.8} />
        </mesh>
      )}
    </group>
  );
}

// ---------------------------------------------------------------------------
// Browser-side height field math (approximate, matches server intent)
// ---------------------------------------------------------------------------

function computeSurfaceHeightRaw(xT: number, slatT: number, surface: SurfaceConfig): number {
  const freq = surface.frequency;
  const phase = surface.phase;

  switch (surface.type) {
    case 'wave':
      return Math.sin(freq * Math.PI * xT + phase) * Math.cos(freq * 0.3 * Math.PI * slatT);
    case 'ripple': {
      const r = Math.sqrt((xT - 0.5) ** 2 + (slatT - 0.5) ** 2);
      return Math.cos(freq * Math.PI * r * 3 + phase) * Math.exp(-r * 2);
    }
    case 'terrain': {
      const z =
        Math.sin(freq * xT * Math.PI) * Math.cos(freq * slatT * Math.PI * 1.3) +
        0.5 * Math.sin(freq * 2 * xT * Math.PI + 1) * Math.cos(freq * 2 * slatT * Math.PI);
      return z / 1.5;
    }
    case 'mountain': {
      const dist = Math.sqrt((xT - 0.5) ** 2 + (slatT - 0.5) ** 2);
      return Math.exp((-dist * dist) / 0.08);
    }
    default:
      return Math.sin(freq * Math.PI * xT + phase);
  }
}

function computeSurfaceHeight(xT: number, slatT: number, surface: SurfaceConfig): number {
  let z = computeSurfaceHeightRaw(xT, slatT, surface);

  if (surface.symmetry === 'x' || surface.symmetry === 'xy') {
    z = (z + computeSurfaceHeightRaw(1 - xT, slatT, surface)) / 2;
  }
  if (surface.symmetry === 'y' || surface.symmetry === 'xy') {
    z = (z + computeSurfaceHeightRaw(xT, 1 - slatT, surface)) / 2;
  }

  return Math.max(0, z * surface.amplitude * surface.max_depth);
}

function generateSlatGeometries(config: CanonicalConfig) {
  const { surface, slats: slatConfig, boundary } = config;
  const width = boundary.width;
  const nSlats = slatConfig.count;
  const pointsPerSlat = 100;

  const xVals = Array.from(
    { length: pointsPerSlat },
    (_, i) => (i / (pointsPerSlat - 1)) * width
  );

  const geometries: { geometry: THREE.ExtrudeGeometry; index: number }[] = [];

  for (let si = 0; si < nSlats; si++) {
    const slatT = nSlats > 1 ? si / (nSlats - 1) : 0.5;

    const profileHeights = xVals.map((x) =>
      computeSurfaceHeight(x / width, slatT, surface)
    );

    const shape = new THREE.Shape();
    shape.moveTo(0, 0);
    shape.lineTo(0, slatConfig.base_height);

    for (let j = 0; j < xVals.length; j++) {
      shape.lineTo(xVals[j], slatConfig.base_height + profileHeights[j]);
    }

    shape.lineTo(width, slatConfig.base_height);
    shape.lineTo(width, 0);
    shape.lineTo(0, 0);

    const geometry = new THREE.ExtrudeGeometry(shape, {
      steps: 1,
      depth: slatConfig.thickness,
      bevelEnabled: false,
    });

    geometries.push({ geometry, index: si });
  }

  return geometries;
}
