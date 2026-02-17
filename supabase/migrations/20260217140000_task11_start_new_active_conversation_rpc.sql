create or replace function public.start_new_active_conversation()
returns public.conversations
language plpgsql
security invoker
as $$
declare
  current_user_id uuid := auth.uid();
  new_conversation public.conversations%rowtype;
begin
  if current_user_id is null then
    raise exception 'unauthenticated';
  end if;

  update public.conversations
     set status = 'archived',
         updated_at = timezone('utc', now())
   where user_id = current_user_id
     and status = 'active';

  insert into public.conversations (user_id, status, last_message_at)
  values (current_user_id, 'active', timezone('utc', now()))
  returning * into new_conversation;

  return new_conversation;
end;
$$;

grant execute on function public.start_new_active_conversation() to authenticated;
