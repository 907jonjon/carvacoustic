-- Billing customers (links Supabase user to Stripe customer)
create table if not exists public.billing_customers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  stripe_customer_id text not null unique,
  created_at timestamptz not null default now()
);

alter table public.billing_customers enable row level security;

create policy "Users can read their own billing customer"
  on public.billing_customers for select
  using (auth.uid() = user_id);

-- Subscriptions
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  stripe_subscription_id text not null unique,
  status text not null default 'active',
  plan text not null default 'pro',
  current_period_start timestamptz,
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.subscriptions enable row level security;

create policy "Users can read their own subscription"
  on public.subscriptions for select
  using (auth.uid() = user_id);

-- Usage events (soft metering)
create table if not exists public.usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null,
  metadata jsonb,
  created_at timestamptz not null default now()
);

alter table public.usage_events enable row level security;

create policy "Users can read their own usage"
  on public.usage_events for select
  using (auth.uid() = user_id);

create policy "Users can insert their own usage"
  on public.usage_events for insert
  with check (auth.uid() = user_id);
