'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import type { Database } from '@/types/database';
import { useTheme } from '@/components/theme/ThemeProvider';

type Mode = 'light' | 'dark';
type Project = Database['public']['Tables']['projects']['Row'];

const STATUS_LIGHT: Record<string, { dot: string; text: string; bg: string }> = {
  draft:    { dot: '#6b7280', text: '#374151', bg: 'rgba(229,231,235,0.92)' },
  ready:    { dot: '#16a34a', text: '#14532d', bg: 'rgba(220,252,231,0.92)' },
  exported: { dot: '#b8660e', text: '#7c2d12', bg: 'rgba(255,237,213,0.92)' },
};
const STATUS_DARK: Record<string, { dot: string; text: string; bg: string }> = {
  draft:    { dot: '#6b7280', text: '#9ca3af', bg: 'rgba(31,41,55,0.85)' },
  ready:    { dot: '#22c55e', text: '#86efac', bg: 'rgba(5,46,22,0.85)' },
  exported: { dot: '#d4831a', text: '#fbbf24', bg: 'rgba(28,16,0,0.92)' },
};

function deriveStatus(project: Project): string {
  if (project.latest_version_id) return 'ready';
  return 'draft';
}

function timeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function StatsStrip({ projects }: { projects: Project[] }) {
  const stats = [
    { label: 'Total', value: projects.length, color: 'var(--text2)' },
    { label: 'Draft', value: projects.filter((p) => deriveStatus(p) === 'draft').length, color: '#6b7280' },
    { label: 'Ready', value: projects.filter((p) => deriveStatus(p) === 'ready').length, color: '#16a34a' },
    { label: 'Exported', value: projects.filter((p) => deriveStatus(p) === 'exported').length, color: 'var(--accent)' },
  ];
  return (
    <div style={{ display: 'flex', gap: 22 }}>
      {stats.map(({ label, value, color }) => (
        <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span style={{ fontSize: 20, fontWeight: 600, lineHeight: 1, color }}>{value}</span>
          <span style={{ fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--text4)', marginTop: 3 }}>{label}</span>
        </div>
      ))}
    </div>
  );
}

function PatternThumbnail({ mode: m }: { mode: Mode }) {
  const c = m === 'dark' ? '#8b6914' : '#a07010';
  const bg = c + (m === 'dark' ? '1a' : '14');
  return (
    <svg viewBox="0 0 132 100" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block', width: '100%', background: bg }}>
      {Array.from({ length: 7 }, (_, i) => {
        const y = 12 + i * 12;
        const a = 5 + (i % 3) * 4;
        return <path key={i} d={`M4 ${y} Q36 ${y - a} 68 ${y} Q100 ${y + a} 132 ${y}`} fill="none" stroke={c} strokeWidth="1.3" strokeLinecap="round" opacity={0.38 + i * 0.09} />;
      })}
    </svg>
  );
}

function ProjectCard({ project, mode }: { project: Project; mode: Mode }) {
  const statusMap = mode === 'dark' ? STATUS_DARK : STATUS_LIGHT;
  const status = deriveStatus(project);
  const s = statusMap[status] ?? statusMap.draft;
  const config = project.draft_config as unknown as Record<string, unknown> | null;
  const boundary = config?.boundary as { width?: number; height?: number } | undefined;
  const w = boundary?.width ?? 0;
  const h = boundary?.height ?? 0;
  const projectMode = (config?.project as { mode?: string })?.mode ?? project.mode;
  const modeLabel = projectMode?.replace(/_/g, ' ') ?? '';
  const ago = timeAgo(new Date(project.updated_at));

  return (
    <Link href={`/app/projects/${project.id}/edit`} className="ca-card" style={{ display: 'block', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden', cursor: 'pointer', transition: 'border-color 0.18s, transform 0.18s, box-shadow 0.18s, background 0.25s', textDecoration: 'none', color: 'inherit' }}>
      <div style={{ position: 'relative', background: 'var(--bg3)', overflow: 'hidden' }}>
        <PatternThumbnail mode={mode} />
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', backgroundImage: 'linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
        <div style={{ position: 'absolute', top: 8, right: 8, display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 9px', borderRadius: 50, fontSize: 8, letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 600, background: s.bg, color: s.text }}><div style={{ width: 5, height: 5, borderRadius: '50%', background: s.dot }} />{status.charAt(0).toUpperCase() + status.slice(1)}</div>
      </div>
      <div style={{ padding: 13 }}>
        <div className="font-display" style={{ color: 'var(--text1)', fontSize: 11.5, fontWeight: 500, lineHeight: 1.35, marginBottom: 9 }}>{project.name}</div>
        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '9px 0' }} />
        <div style={{ display: 'flex', gap: 7, marginBottom: 4 }}><span style={{ color: 'var(--text3)', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', width: 38, flexShrink: 0 }}>Size</span><span style={{ color: 'var(--text2)', fontSize: 9, lineHeight: 1.3 }}>{w}&times;{h} {project.units}</span></div>
        <div style={{ display: 'flex', gap: 7, marginBottom: 4 }}><span style={{ color: 'var(--text3)', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', width: 38, flexShrink: 0 }}>Mode</span><span style={{ color: 'var(--text2)', fontSize: 9, lineHeight: 1.3 }}>{modeLabel}</span></div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 7 }}><span style={{ color: 'var(--text4)', fontSize: 8 }}>{ago}</span><span className="ca-card-open" style={{ color: 'var(--accent)', fontSize: 9, opacity: 0, transition: 'opacity 0.15s' }}>Open →</span></div>
      </div>
    </Link>
  );
}

export function DashboardBody({ projects, error }: { projects: Project[]; error?: string }) {
  const { mode } = useTheme();
  const [activeFilter, setActiveFilter] = useState('all');
  const filtered = activeFilter === 'all' ? projects : projects.filter((p) => deriveStatus(p) === activeFilter);
  const filters = ['all', 'draft', 'ready', 'exported'];

  return (
    <div style={{ flex: 1 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '36px 28px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 28 }}>
          <div>
            <h1 className="font-display" style={{ fontSize: 30, fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1 }}>Projects</h1>
            <p style={{ color: 'var(--text3)', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', marginTop: 5 }}>Your saved panel designs</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            {projects.length > 0 && <StatsStrip projects={projects} />}
            <Link href="/app/projects/new" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 14px', background: 'var(--accent)', color: 'var(--btn-fg)', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', borderRadius: 7, textDecoration: 'none', transition: 'background 0.15s' }}>+ New Project</Link>
          </div>
        </div>

        {error && <div style={{ marginBottom: 20, padding: '8px 14px', borderRadius: 8, border: '1px solid var(--accent)', color: 'var(--accent)', fontSize: 11 }}>Could not load projects: {error}</div>}

        {projects.length > 0 && (
          <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
            {filters.map((f) => (
              <button key={f} onClick={() => setActiveFilter(f)} style={{ padding: '4px 12px', borderRadius: 50, border: `1px solid ${f === activeFilter ? 'var(--accent)' : 'var(--border)'}`, background: f === activeFilter ? 'var(--accent-dim)' : 'transparent', color: f === activeFilter ? 'var(--accent)' : 'var(--text3)', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s' }}>{f.charAt(0).toUpperCase() + f.slice(1)}</button>
            ))}
          </div>
        )}

        {!error && projects.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '80px 20px', textAlign: 'center' }}>
            <div style={{ width: 38, height: 38, borderRadius: '50%', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text4)', fontSize: 20 }}>+</div>
            <h2 className="font-display" style={{ fontSize: 20, margin: '20px 0 8px' }}>No projects yet</h2>
            <p style={{ color: 'var(--text3)', fontSize: 11, maxWidth: 280, lineHeight: 1.6, marginBottom: 24 }}>Create your first decorative panel design.</p>
            <Link href="/app/projects/new" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 14px', background: 'var(--accent)', color: 'var(--btn-fg)', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', borderRadius: 7, textDecoration: 'none' }}>+ New Project</Link>
          </div>
        )}

        {!error && filtered.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
            {filtered.map((project) => <ProjectCard key={project.id} project={project} mode={mode} />)}
            <Link href="/app/projects/new" className="ca-new-card" style={{ background: 'transparent', border: '1px dashed var(--border)', borderRadius: 12, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 9, minHeight: 200, textDecoration: 'none', transition: 'border-color 0.18s, background 0.18s' }}>
              <div style={{ width: 38, height: 38, borderRadius: '50%', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text4)', fontSize: 20 }}>+</div>
              <span style={{ color: 'var(--text4)', fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase' }}>New project</span>
            </Link>
          </div>
        )}
      </div>

      <footer style={{ maxWidth: 1100, margin: '0 auto', padding: '24px 28px', borderTop: '1px solid var(--border)', marginTop: 24 }}>
        <p style={{ color: 'var(--text4)', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase' }}>© 2026 CarvAcoustic · Design to Fabrication</p>
      </footer>
    </div>
  );
}
