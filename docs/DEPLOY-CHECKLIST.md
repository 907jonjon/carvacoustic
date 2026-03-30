# CarvAcoustic Deployment Checklist

## What's deployed where

| Service | Host | URL |
|---------|------|-----|
| Web app | Vercel | https://carvacoustic.com (or your Vercel URL) |
| Geometry service | Fly.io | https://carvacoustic-geometry.fly.dev |
| Database + Auth | Supabase Cloud | Your Supabase project URL |

## Step 1: Verify Fly.io geometry service

```bash
curl https://carvacoustic-geometry.fly.dev/health
```

Expected: `{"status":"ok","service":"carvacoustic-geometry","version":"0.1.0"}`

If it fails:
```bash
cd geometry
fly status
fly logs --app carvacoustic-geometry
```

If the app has never been deployed or was destroyed:
```bash
cd geometry
fly launch --name carvacoustic-geometry --region iad --no-deploy
fly secrets set API_KEY=your-shared-secret-here
fly secrets set ALLOWED_ORIGIN=https://carvacoustic.com
fly deploy
```

## Step 2: Verify Fly.io secrets are set

```bash
fly secrets list --app carvacoustic-geometry
```

You need at minimum:
- `API_KEY` — shared secret that the web app sends as `X-API-Key`
- `ALLOWED_ORIGIN` — your Vercel production URL (e.g. `https://carvacoustic.com`)

## Step 3: Verify Vercel environment variables

In Vercel dashboard → Settings → Environment Variables, confirm:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-project.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `GEOMETRY_SERVICE_URL` | `https://carvacoustic-geometry.fly.dev` |
| `GEOMETRY_SERVICE_API_KEY` | Same value as `API_KEY` on Fly.io |

**Critical:** `GEOMETRY_SERVICE_API_KEY` on Vercel must exactly match `API_KEY` on Fly.io.

## Step 4: Verify Supabase

1. In Supabase dashboard → SQL Editor, run:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public' ORDER BY table_name;
   ```

   You should see: `assets`, `billing_customers`, `design_versions`, `export_bundles`,
   `material_presets`, `projects`, `profiles`, `subscriptions`, `templates`,
   `tool_presets`, `usage_events`

2. Verify Auth → URL Configuration:
   - Site URL: your Vercel production URL
   - Redirect URLs: `https://your-vercel-url.com/auth/callback`

## Step 5: Test generate directly against Fly.io

Replace `YOUR_API_KEY` with your actual key:

```bash
curl -s -X POST https://carvacoustic-geometry.fly.dev/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"config":{"schema_version":"2.0.0","project":{"name":"Test","mode":"wall_art","units":"in"},"boundary":{"type":"rectangle","width":24,"height":18,"corner_radius":0,"asset_id":null,"safe_margin":1.0},"surface":{"type":"wave","max_depth":3.0,"min_depth":0.0,"amplitude":0.7,"frequency":3.0,"phase":0.0,"flow_direction":"x","symmetry":"none","smoothness":0.5,"seed":42,"noise_amount":0.2},"slats":{"count":15,"spacing":0.75,"thickness":0.75,"base_height":1.5,"tab_width":0.5,"tab_depth":0.75,"tab_count":3,"tab_clearance":0.01,"distribution_mode":"fit_to_boundary"},"backing":{"enabled":true,"width":24,"height":3.0,"slot_width":0.76,"slot_depth":0.75,"mounting_holes":true},"fabrication":{"material":{"thickness":0.75,"sheet_width":96,"sheet_height":48,"min_bridge":0.3,"grain_direction":"x"},"tool":{"tool_diameter":0.25,"kerf_allowance":0.008,"min_inside_radius":0.125,"dogbone_style":"none","clearance":0.125,"border_gap":0.75}},"layout":{"enabled":true,"copies":1,"rotation_mode":"90_only","preserve_grain":false},"labeling":{"enabled":true,"prefix":"S","position":"centroid"},"export":{"formats":["dxf","svg","pdf","json"],"units":"in"},"reserved_acoustic":{"enabled":false,"room_use":null,"target_issue":null,"room_dimensions":null,"surface_summary":null,"installation_constraints":null,"attachments":[]}}}' | python3 -m json.tool | head -30
```

Expected: JSON with `"status": "ok"`, `svg_preview`, `part_count`, etc.

## Step 6: Test export directly against Fly.io

```bash
curl -s -X POST https://carvacoustic-geometry.fly.dev/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"config":{...same config as step 5...}}' \
  --output test-export.zip
```

Then verify:
```bash
unzip -l test-export.zip
```

Expected files: `manifest.json`, `project-config.json`, `sheet-01.dxf`, `sheet-01.svg`, `reference.pdf`, `README.txt`

## Step 7: Test the full web flow

1. Visit your Vercel URL
2. Log in / sign up
3. Create a new project (wall art, 24" x 18")
4. Open the editor
5. Click "Prepare Review" — should show SVG preview and part count
6. Click "Download Cut Files" — should download a ZIP

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Geometry service offline" | Web can't reach Fly.io | Check `GEOMETRY_SERVICE_URL` on Vercel |
| 401 from geometry | API key mismatch | Match `GEOMETRY_SERVICE_API_KEY` (Vercel) with `API_KEY` (Fly.io) |
| 429 rate limit | Billing gate enabled | Set `enableBilling = false` in `web/src/lib/flags.ts` |
| CORS error in browser | Missing origin | Set `ALLOWED_ORIGIN` on Fly.io to your Vercel URL |
| Fly.io 503 | Machine sleeping | First request wakes it — wait 10-15 seconds, retry |
| Supabase auth fails | Wrong redirect URL | Update Auth → URL Configuration in Supabase dashboard |
