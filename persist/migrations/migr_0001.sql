alter table idle_rpg_base.characters add dt_last_activity timestamp with time zone;
alter table idle_rpg_base.arch_characters add dt_last_activity timestamp with time zone;
create table idle_rpg_base.feedback_replies
(
	id serial,
	feedback_message_id integer,
	telegram_id integer,
	dt_sent timestamp with time zone default current_timestamp,
	message text,
	constraint fk_feedback_reply_to_message foreign key(feedback_message_id) references idle_rpg_base.feedback_messages(id)
);
ALTER TABLE idle_rpg_base.feedback_replies
  OWNER TO idle_rpg_user;
create table idle_rpg_base.persist_version
(
	v_name text,
	n_version integer,
	dt_update timestamp with time zone
);
alter table  idle_rpg_base.persist_version owner to idle_rpg_user;
insert into idle_rpg_base.persist_version(v_name, n_version, dt_update) values('idle RPG', 1, current_timestamp);
commit;