-- Feedback submissions from the editor
create table if not exists public.feedback_submissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  category text not null,
  message text not null,
  project_id uuid references public.projects(id) on delete set null,
  config_snapshot jsonb,
  created_at timestamptz not null default now()
);

alter table public.feedback_submissions enable row level security;

create policy "Users can insert their own feedback"
  on public.feedback_submissions for insert
  with check (auth.uid() = user_id);

create policy "Users can read their own feedback"
  on public.feedback_submissions for select
  using (auth.uid() = user_id);
