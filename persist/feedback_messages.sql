create table idle_rpg_base.feedback_messages
(
	id serial primary key,
	telegram_id bigint,
	telegram_nickname text,
	dt_sent timestamp with time zone default CURRENT_TIMESTAMP,
	is_read	boolean default false,
	dt_read timestamp with time zone,
	message text,
	read_by integer
);
ALTER TABLE idle_rpg_base.feedback_messages
  OWNER TO idle_rpg_user;
CREATE INDEX idx_feedback_messages_read
  ON idle_rpg_base.feedback_messages(is_read)
  where (not is_read)
  ;