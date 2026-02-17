create or replace function public.get_or_create_active_conversation()
returns public.conversations
language plpgsql
security invoker
as $$
declare
  current_user_id uuid := auth.uid();
  active_conversation public.conversations%rowtype;
begin
  if current_user_id is null then
    raise exception 'unauthenticated';
  end if;

  loop
    select *
      into active_conversation
      from public.conversations
     where user_id = current_user_id
       and status = 'active'
     order by created_at desc
     limit 1;

    if found then
      return active_conversation;
    end if;

    begin
      insert into public.conversations (user_id, status, last_message_at)
      values (current_user_id, 'active', timezone('utc', now()))
      returning * into active_conversation;

      return active_conversation;
    exception
      when unique_violation then
        -- Concurrent request inserted an active conversation first.
        -- Retry read path in loop.
    end;
  end loop;
end;
$$;

grant execute on function public.get_or_create_active_conversation() to authenticated;
