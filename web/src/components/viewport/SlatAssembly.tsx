'use client';

import { useMemo } from 'react';
import * as THREE from 'three';
import type { CanonicalConfig, SurfaceConfig } from '@/types/schema';
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

  // Use server geometry if available, otherwise fall back to draft
  const hasServerGeometry = partGeometries && partGeometries.length > 0;

  const serverSlats = useMemo(() => {
    if (!hasServerGeometry) return [];
    return partGeometries
      .filter((p) => p.part_type === "slat")
      .map((p) => ({
        geometry: geometryFromPolygon(p.exterior, p.holes, thickness),
        partId: p.part_id,
      }));
  }, [partGeometries, hasServerGeometry, thickness]);

  const serverBacking = useMemo(() => {
    if (!hasServerGeometry) return null;
    const bp = partGeometries.find((p) => p.part_type === "backing");
    if (!bp) return null;
    return geometryFromPolygon(bp.exterior, bp.holes, thickness);
  }, [partGeometries, hasServerGeometry, thickness]);

  const draftSlats = useMemo(() => {
    if (hasServerGeometry) return [];
    return generateDraftGeometries(config);
  }, [config, hasServerGeometry]);

  const slats = hasServerGeometry ? serverSlats : draftSlats.map((s) => ({
    geometry: s.geometry,
    partId: `draft-${s.index}`,
  }));

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
          <meshStandardMaterial
            color={slatColor}
            roughness={0.7}
            metalness={0.1}
            side={THREE.DoubleSide}
            wireframe={!hasServerGeometry}
          />
        </mesh>
      ))}

      {showBacking && config.backing.enabled && (
        hasServerGeometry && serverBacking ? (
          <mesh
            geometry={serverBacking}
            position={[
              0,
              -config.slats.tab_depth,
              ((config.slats.count - 1) * spacing) / 2 - thickness / 2,
            ]}
          >
            <meshStandardMaterial color={backingColor} roughness={0.8} side={THREE.DoubleSide} />
          </mesh>
        ) : (
          <mesh
            position={[
              config.boundary.width / 2,
              -config.slats.tab_depth / 2,
              ((config.slats.count - 1) * spacing) / 2,
            ]}
          >
            <boxGeometry
              args={[
                config.boundary.width,
                config.backing.height,
                (config.slats.count - 1) * spacing + thickness,
              ]}
            />
            <meshStandardMaterial color={backingColor} roughness={0.8} wireframe />
          </mesh>
        )
      )}

      {!hasServerGeometry && (
        <group position={[config.boundary.width / 2, -2, 0]}>
          {/* Draft indicator — rendered as a simple text sprite would be ideal,
              but for now the wireframe material signals "draft" */}
        </group>
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

// ---------------------------------------------------------------------------
// Draft preview (approximate, before Generate is clicked)
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

function generateDraftGeometries(config: CanonicalConfig) {
  const { surface, slats: slatConfig, boundary } = config;
  const width = boundary.width;
  const nSlats = slatConfig.count;
  const thickness = config.fabrication.material.thickness;
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
      depth: thickness,
      bevelEnabled: false,
    });

    geometries.push({ geometry, index: si });
  }

  return geometries;
}
