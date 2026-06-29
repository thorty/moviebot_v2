alter table public.watchlist_items
  add column if not exists cover_url text;
