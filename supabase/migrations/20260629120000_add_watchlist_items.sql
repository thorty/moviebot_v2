create table if not exists public.watchlist_items (
  id uuid primary key default extensions.gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (length(trim(title)) > 0),
  title_key text not null check (length(trim(title_key)) > 0),
  media_type text not null check (media_type in ('movie', 'documentary', 'series')),
  description text not null default '',
  cover_url text,
  rating numeric(3, 1) check (rating is null or (rating >= 0 and rating <= 10)),
  rating_source text,
  streaming_providers text[] not null default '{}'::text[],
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists watchlist_items_user_title_media_unique
  on public.watchlist_items (user_id, title_key, media_type);

create index if not exists watchlist_items_user_created_idx
  on public.watchlist_items (user_id, created_at desc);

drop trigger if exists watchlist_items_set_updated_at on public.watchlist_items;
create trigger watchlist_items_set_updated_at
before update on public.watchlist_items
for each row
execute function public.set_updated_at();

alter table public.watchlist_items enable row level security;

drop policy if exists watchlist_items_select_own on public.watchlist_items;
create policy watchlist_items_select_own
  on public.watchlist_items
  for select
  using (auth.uid() = user_id);

drop policy if exists watchlist_items_insert_own on public.watchlist_items;
create policy watchlist_items_insert_own
  on public.watchlist_items
  for insert
  with check (auth.uid() = user_id);

drop policy if exists watchlist_items_update_own on public.watchlist_items;
create policy watchlist_items_update_own
  on public.watchlist_items
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists watchlist_items_delete_own on public.watchlist_items;
create policy watchlist_items_delete_own
  on public.watchlist_items
  for delete
  using (auth.uid() = user_id);
