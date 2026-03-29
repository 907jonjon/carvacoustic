/**
 * Supabase database type definitions.
 * Generated from the migration schema in supabase/migrations/001_initial.sql.
 * Run `npx supabase gen types typescript` to regenerate after schema changes.
 */

import type { CanonicalConfig, ProjectMode, Units } from "./schema";

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string | null;
          display_name: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email?: string | null;
          display_name?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string | null;
          display_name?: string | null;
          updated_at?: string;
        };
      };
      projects: {
        Row: {
          id: string;
          owner_id: string;
          name: string;
          mode: ProjectMode;
          units: Units;
          draft_config: CanonicalConfig;
          latest_version_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          owner_id: string;
          name: string;
          mode: ProjectMode;
          units?: Units;
          draft_config: CanonicalConfig;
          latest_version_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          name?: string;
          mode?: ProjectMode;
          units?: Units;
          draft_config?: CanonicalConfig;
          latest_version_id?: string | null;
          updated_at?: string;
        };
      };
      project_versions: {
        Row: {
          id: string;
          project_id: string;
          version_number: number;
          config: CanonicalConfig;
          notes: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          project_id: string;
          version_number: number;
          config: CanonicalConfig;
          notes?: string | null;
          created_at?: string;
        };
        Update: never;
      };
      material_presets: {
        Row: {
          id: string;
          owner_id: string | null;
          name: string;
          thickness: number;
          sheet_width: number;
          sheet_height: number;
          min_bridge: number;
          grain_direction: "x" | "y";
          is_default: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          owner_id?: string | null;
          name: string;
          thickness: number;
          sheet_width: number;
          sheet_height: number;
          min_bridge: number;
          grain_direction?: "x" | "y";
          is_default?: boolean;
          created_at?: string;
        };
        Update: {
          name?: string;
          thickness?: number;
          sheet_width?: number;
          sheet_height?: number;
          min_bridge?: number;
          grain_direction?: "x" | "y";
          is_default?: boolean;
        };
      };
      tool_presets: {
        Row: {
          id: string;
          owner_id: string | null;
          name: string;
          tool_diameter: number;
          kerf_allowance: number;
          min_inside_radius: number;
          dogbone_style: "classic" | "none";
          clearance: number;
          border_gap: number;
          is_default: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          owner_id?: string | null;
          name: string;
          tool_diameter: number;
          kerf_allowance?: number;
          min_inside_radius: number;
          dogbone_style?: "classic" | "none";
          clearance: number;
          border_gap: number;
          is_default?: boolean;
          created_at?: string;
        };
        Update: {
          name?: string;
          tool_diameter?: number;
          kerf_allowance?: number;
          min_inside_radius?: number;
          dogbone_style?: "classic" | "none";
          clearance?: number;
          border_gap?: number;
          is_default?: boolean;
        };
      };
      assets: {
        Row: {
          id: string;
          owner_id: string;
          name: string;
          type: string;
          storage_path: string;
          file_size: number | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          owner_id: string;
          name: string;
          type?: string;
          storage_path: string;
          file_size?: number | null;
          created_at?: string;
        };
        Update: {
          name?: string;
          type?: string;
          storage_path?: string;
          file_size?: number | null;
        };
      };
      export_bundles: {
        Row: {
          id: string;
          project_id: string;
          version_id: string | null;
          storage_path: string;
          manifest: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          project_id: string;
          version_id?: string | null;
          storage_path: string;
          manifest?: Json | null;
          created_at?: string;
        };
        Update: never;
      };
      feedback_submissions: {
        Row: {
          id: string;
          user_id: string | null;
          category: string;
          message: string;
          project_id: string | null;
          config_snapshot: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id?: string | null;
          category: string;
          message: string;
          project_id?: string | null;
          config_snapshot?: Json | null;
          created_at?: string;
        };
        Update: {
          category?: string;
          message?: string;
          project_id?: string | null;
          config_snapshot?: Json | null;
        };
      };
      billing_customers: {
        Row: {
          id: string;
          user_id: string;
          stripe_customer_id: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          stripe_customer_id: string;
          created_at?: string;
        };
        Update: {
          stripe_customer_id?: string;
        };
      };
      subscriptions: {
        Row: {
          id: string;
          user_id: string;
          stripe_subscription_id: string;
          status: string;
          plan: string;
          current_period_start: string | null;
          current_period_end: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          stripe_subscription_id: string;
          status?: string;
          plan?: string;
          current_period_start?: string | null;
          current_period_end?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          status?: string;
          plan?: string;
          current_period_start?: string | null;
          current_period_end?: string | null;
          updated_at?: string;
        };
      };
      usage_events: {
        Row: {
          id: string;
          user_id: string;
          event_type: string;
          metadata: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          event_type: string;
          metadata?: Json | null;
          created_at?: string;
        };
        Update: never;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}
