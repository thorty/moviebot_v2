alter table public.user_filter_preferences
  add column if not exists include_mediatheken boolean not null default false;

update public.user_filter_preferences
set include_mediatheken = true,
    payment_types = case
      when payment_types = '{}'::text[] then array['free']::text[]
      else payment_types
    end
where source = 'mediathek';
