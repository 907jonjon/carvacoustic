'use client';

import { useMemo } from 'react';
import * as THREE from 'three';
import type { CanonicalConfig } from '@/types/schema';
import type { PartGeometry } from '@/components/editor/SvgPreview';

interface SlatAssemblyProps {
  config: CanonicalConfig;
  showExploded: boolean;
  showBacking: boolean;
  slatColor?: string;
  backingColor?: string;
  partGeometries?: PartGeometry[];
}

export function SlatAssembly({
  config,
  showExploded,
  showBacking,
  slatColor = "#8B6914",
  backingColor = "#A0522D",
  partGeometries,
}: SlatAssemblyProps) {
  // Normalize spacing the same way the server does (models.py normalize_config)
  const mode = config.slats.distribution_mode ?? "fit_to_boundary";
  const spacing =
    mode === "fit_to_boundary"
      ? (config.boundary.height - 2 * config.boundary.safe_margin) /
        Math.max(config.slats.count - 1, 1)
      : config.slats.spacing;

  // Sync thickness from material (same as normalize_config)
  const thickness = config.fabrication.material.thickness;

  const explodeOffset = showExploded ? spacing * 2 : 0;

  const hasGeometry = partGeometries && partGeometries.length > 0;

  const slats = useMemo(() => {
    if (!hasGeometry) return [];
    return partGeometries
      .filter((p) => p.part_type === "slat")
      .map((p) => ({
        geometry: geometryFromPolygon(p.exterior, p.holes, thickness),
        partId: p.part_id,
      }));
  }, [partGeometries, hasGeometry, thickness]);

  const backingGeom = useMemo(() => {
    if (!hasGeometry) return null;
    const bp = partGeometries.find((p) => p.part_type === "backing");
    if (!bp) return null;
    return geometryFromPolygon(bp.exterior, bp.holes, thickness);
  }, [partGeometries, hasGeometry, thickness]);

  if (!hasGeometry) {
    return <group />;
  }

  return (
    <group>
      {slats.map((slat, i) => (
        <mesh
          key={slat.partId}
          geometry={slat.geometry}
          position={[
            0,
            0,
            i * spacing + (showExploded ? i * explodeOffset : 0),
          ]}
        >
          <meshPhysicalMaterial
            color={slatColor}
            roughness={0.7}
            metalness={0.1}
            transparent
            opacity={0.85}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}

      {showBacking && config.backing.enabled && backingGeom && (
        <mesh
          geometry={backingGeom}
          position={[
            0,
            -config.slats.tab_depth,
            ((config.slats.count - 1) * spacing) / 2 - thickness / 2,
          ]}
        >
          <meshPhysicalMaterial
            color={backingColor}
            roughness={0.8}
            transparent
            opacity={0.85}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </group>
  );
}

// ---------------------------------------------------------------------------
// Build Three.js geometry from server-provided polygon coordinates
// ---------------------------------------------------------------------------

function geometryFromPolygon(
  exterior: [number, number][],
  holes: [number, number][][],
  thickness: number,
): THREE.ExtrudeGeometry {
  const shape = new THREE.Shape();
  if (exterior.length === 0) return new THREE.ExtrudeGeometry(shape, { depth: thickness });

  shape.moveTo(exterior[0][0], exterior[0][1]);
  for (let i = 1; i < exterior.length; i++) {
    shape.lineTo(exterior[i][0], exterior[i][1]);
  }

  for (const hole of holes) {
    if (hole.length === 0) continue;
    const holePath = new THREE.Path();
    holePath.moveTo(hole[0][0], hole[0][1]);
    for (let i = 1; i < hole.length; i++) {
      holePath.lineTo(hole[i][0], hole[i][1]);
    }
    shape.holes.push(holePath);
  }

  return new THREE.ExtrudeGeometry(shape, {
    steps: 1,
    depth: thickness,
    bevelEnabled: false,
  });
}
