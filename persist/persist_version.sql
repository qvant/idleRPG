create table idle_rpg_base.persist_version
(
	v_name text,
	n_version integer,
	dt_update timestamp with time zone
);
alter table  idle_rpg_base.persist_version owner to idle_rpg_user;
insert into idle_rpg_base.persist_version(v_name, n_version, dt_update) values('idle RPG', 2, current_timestamp);
commit;