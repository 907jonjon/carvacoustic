/**
 * Centralized feature flags.
 *
 * Flip these when the corresponding feature is ready for production.
 * No runtime config service yet — just constants.
 */

/** Stripe billing checkout, portal, and export gating. */
export const enableBilling = false;

/** Multi-sheet tiled backing boards for large installations. */
export const enableTiledBacking = false;

/** Organic boundary presets (arch, capsule, oval, wave-top). */
export const enableOrganicBoundaryPresets = false;

/** Freeform SVG boundary import. */
export const enableSvgImport = false;
