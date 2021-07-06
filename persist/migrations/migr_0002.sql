alter table idle_rpg_base.characters alter column telegram_id type bigint;
alter table idle_rpg_base.feedback_messages alter column telegram_id type bigint;
alter table idle_rpg_base.feedback_replies alter column telegram_id type bigint;
update idle_rpg_bot.persist_version set n_version=2, dt_update = current_timestamp where v_name = 'idle RPG' ;
commit;