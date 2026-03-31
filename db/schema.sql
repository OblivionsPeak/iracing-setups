-- iRacing Setup Manager — Supabase Schema
-- Run this in the Supabase SQL editor

-- ── Profiles ─────────────────────────────────────────────────────────────────
create table if not exists profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at   timestamptz default now()
);

-- ── Setups ───────────────────────────────────────────────────────────────────
create table if not exists setups (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  filename       text not null,
  car_name       text not null,
  car_key        text not null,
  car_class      text not null default 'Other',
  track_name     text not null,
  track_key      text not null,
  setup_type     text not null default 'race',
  notes_text     text,
  decoded_params jsonb not null default '[]',
  storage_path   text not null,
  uploaded_at    timestamptz default now(),
  last_used_at   timestamptz
);

create index if not exists setups_user_id_idx     on setups(user_id);
create index if not exists setups_car_key_idx     on setups(car_key);
create index if not exists setups_track_key_idx   on setups(track_key);
create index if not exists setups_car_track_idx   on setups(car_key, track_key);

-- ── Setup params (denormalised for fast comparison queries) ───────────────────
create table if not exists setup_params (
  id        uuid primary key default gen_random_uuid(),
  setup_id  uuid not null references setups(id) on delete cascade,
  user_id   uuid not null,
  tab       text,
  section   text,
  label     text not null,
  value     text,
  unit      text,
  range_min text,
  range_max text
);

create index if not exists setup_params_setup_id_idx on setup_params(setup_id);
create index if not exists setup_params_user_id_idx  on setup_params(user_id);

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table profiles     enable row level security;
alter table setups       enable row level security;
alter table setup_params enable row level security;

-- Profiles: own row only
create policy "profiles_own" on profiles
  for all using (auth.uid() = id);

-- Setups: own rows only
create policy "setups_own" on setups
  for all using (auth.uid() = user_id);

-- Setup params: via parent setup ownership
create policy "setup_params_own" on setup_params
  for all using (auth.uid() = user_id);

-- ── Storage bucket ───────────────────────────────────────────────────────────
-- Create a private bucket named 'setups' in Supabase Storage dashboard.
-- Storage paths follow: {user_id}/{setup_id}.sto
