-- ==============================================================================
-- Applied manually in Supabase SQL Editor on 2026-10-04/05. Documents LIVE state. Do not re-run blindly.
-- ==============================================================================

-- 1. Admin helper function (SECURITY DEFINER, search_path='')
create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = ''
as $$
  select auth.uid() in (
    '75cc9fce-340b-4a7e-9619-2cbc1998b834'::uuid,
    '567f4229-de4a-4bbd-b862-07f79e08742b'::uuid
  );
$$;

revoke execute on function public.is_admin() from public;
revoke execute on function public.is_admin() from anon;
grant execute on function public.is_admin() to authenticated;

-- 2. Admin policies on articles table (SELECT, INSERT, UPDATE to authenticated with is_admin(); no DELETE)
create policy "Admin read all articles"
  on public.articles
  for select
  to authenticated
  using (public.is_admin());

create policy "Admin insert articles"
  on public.articles
  for insert
  to authenticated
  with check (public.is_admin());

create policy "Admin update articles"
  on public.articles
  for update
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

-- 3. Draft writer policy
create policy "Draft writer insert drafts"
  on public.articles
  for insert
  to authenticated
  with check (
    auth.uid() = '3671fb4d-d462-4d0f-8e36-e76c76b4429a'::uuid
    and status = 'draft'
  );

-- 4. Public read policy for published articles
create policy "Public read published articles"
  on public.articles
  for select
  to public
  using (
    status = 'published'
    and hidden = false
    and published_at <= now()
  );
