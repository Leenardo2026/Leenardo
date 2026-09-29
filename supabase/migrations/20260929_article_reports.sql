-- Migration: Create article_reports table for Leenardo community issue reporting
-- Date: 2026-09-29

create table if not exists public.article_reports (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  article_id text not null,
  target_lang text not null,
  support_lang text not null,
  cefr_level text not null,
  issue_type text not null,
  notes text,
  user_id uuid references auth.users(id) on delete set null,
  user_email text,
  status text not null default 'pending'
);

-- Enable Row Level Security (RLS)
alter table public.article_reports enable row level security;

-- Allow anonymous and authenticated users to submit reports
create policy "Allow anyone to insert article reports"
  on public.article_reports
  for insert
  with check (true);

-- Allow authenticated admins to view reports (or keep restricted by default)
create policy "Allow service_role full access"
  on public.article_reports
  for all
  to service_role
  using (true)
  with check (true);

-- Indexes for performance
create index if not exists idx_article_reports_article_id on public.article_reports(article_id);
create index if not exists idx_article_reports_created_at on public.article_reports(created_at desc);
create index if not exists idx_article_reports_status on public.article_reports(status);
