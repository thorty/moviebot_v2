create table if not exists public.user_filter_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  source text not null default 'streaming' check (source in ('streaming', 'mediathek')),
  providers text[] not null default '{}'::text[],
  payment_types text[] not null default '{}'::text[],
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create trigger user_filter_preferences_set_updated_at
before update on public.user_filter_preferences
for each row
execute function public.set_updated_at();

alter table public.user_filter_preferences enable row level security;

drop policy if exists user_filter_preferences_select_own on public.user_filter_preferences;
create policy user_filter_preferences_select_own
  on public.user_filter_preferences
  for select
  using (auth.uid() = user_id);

drop policy if exists user_filter_preferences_insert_own on public.user_filter_preferences;
create policy user_filter_preferences_insert_own
  on public.user_filter_preferences
  for insert
  with check (auth.uid() = user_id);

drop policy if exists user_filter_preferences_update_own on public.user_filter_preferences;
create policy user_filter_preferences_update_own
  on public.user_filter_preferences
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
