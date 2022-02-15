alter table idle_rpg_base.v alter column telegram_id type bigint;
update idle_rpg_base.persist_version set n_version=3, dt_update = current_timestamp where v_name = 'idle RPG' ;
commit;