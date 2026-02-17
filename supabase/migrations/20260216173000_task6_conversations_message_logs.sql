create extension if not exists pgcrypto with schema extensions;

create table if not exists public.conversations (
  id uuid primary key default extensions.gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'active' check (status in ('active', 'archived')),
  title text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  last_message_at timestamptz
);

alter table public.conversations
  add constraint conversations_id_user_unique unique (id, user_id);

create unique index if not exists conversations_one_active_per_user_idx
  on public.conversations (user_id)
  where status = 'active';

create index if not exists conversations_user_created_idx
  on public.conversations (user_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create trigger conversations_set_updated_at
before update on public.conversations
for each row
execute function public.set_updated_at();

create table if not exists public.message_logs (
  id bigint generated always as identity primary key,
  conversation_id uuid not null,
  user_id uuid not null,
  role text not null check (role in ('user', 'assistant', 'system', 'tool')),
  content text not null check (length(trim(content)) > 0),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  constraint message_logs_conversation_user_fk
    foreign key (conversation_id, user_id)
    references public.conversations (id, user_id)
    on delete cascade
);

create index if not exists message_logs_conversation_created_idx
  on public.message_logs (conversation_id, created_at asc);

create index if not exists message_logs_user_created_idx
  on public.message_logs (user_id, created_at desc);

alter table public.conversations enable row level security;
alter table public.message_logs enable row level security;

drop policy if exists conversations_select_own on public.conversations;
create policy conversations_select_own
  on public.conversations
  for select
  using (auth.uid() = user_id);

drop policy if exists conversations_insert_own on public.conversations;
create policy conversations_insert_own
  on public.conversations
  for insert
  with check (auth.uid() = user_id);

drop policy if exists conversations_update_own on public.conversations;
create policy conversations_update_own
  on public.conversations
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists message_logs_select_own on public.message_logs;
create policy message_logs_select_own
  on public.message_logs
  for select
  using (auth.uid() = user_id);

drop policy if exists message_logs_insert_own on public.message_logs;
create policy message_logs_insert_own
  on public.message_logs
  for insert
  with check (auth.uid() = user_id);
