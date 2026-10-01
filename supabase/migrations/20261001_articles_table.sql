-- ==============================================================================
-- Migration: Create Articles Table & Row Level Security (RLS)
-- Date: 2026-10-01
-- Target: Leenardo Multilingual Graded Content Platform
-- ==============================================================================

-- 1. Create articles table
create table if not exists public.articles (
  id text primary key,                               -- Slug / permanent unique ID (e.g. 'tarih-truva-ve-tahta-at')
  topic text not null,                               -- Editorial topic / headline
  category text not null,                            -- Category slug (e.g. 'tarih', 'sanat', 'bilim')
  category_translations jsonb default '{}'::jsonb,   -- Localized category labels for UI
  title_tr text,
  title_en text,
  title_translations jsonb default '{}'::jsonb,      -- Localized title translations
  teaser jsonb,
  teaser_translations jsonb default '{}'::jsonb,     -- Localized card teasers
  visual jsonb default '{}'::jsonb,                  -- Featured image metadata, alt, source, attribution
  read_time text default '3 min read',
  languages jsonb not null,                          -- Full graded text (tr, en, es, de, fr -> A1..C1 with tokens & quizzes)
  summary jsonb,                                     -- Pre-computed lightweight summary for instant homepage feeds
  status text not null default 'published',          -- 'published', 'draft', 'archived'
  hidden boolean not null default false,
  published_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 2. Indexes for fast retrieval
create index if not exists idx_articles_status_published on public.articles(status, published_at desc) where hidden = false;
create index if not exists idx_articles_category on public.articles(category);

-- 3. Enable Row Level Security (RLS)
alter table public.articles enable row level security;

-- 4. RLS Policy: Public read access for published stories
drop policy if exists "Public read published articles" on public.articles;
create policy "Public read published articles"
  on public.articles
  for select
  using (status = 'published' and hidden = false);

-- 5. RLS Policy: Service role full access for backend scripts / publishers
drop policy if exists "Allow service_role full access" on public.articles;
create policy "Allow service_role full access"
  on public.articles
  for all
  to service_role
  using (true)
  with check (true);

-- 6. RLS Policy: Allow initial setup seeding (can be dropped after migration)
drop policy if exists "Allow initial seed insert" on public.articles;
create policy "Allow initial seed insert"
  on public.articles
  for insert
  with check (true);

-- 7. Automatic updated_at trigger
create or replace function public.handle_articles_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_articles_updated_at on public.articles;
create trigger set_articles_updated_at
  before update on public.articles
  for each row
  execute function public.handle_articles_updated_at();
