create table idle_rpg_base.feedback_replies
(
	id serial,
	feedback_message_id integer,
	telegram_id bigint,
	dt_sent timestamp with time zone default current_timestamp,
	message text,
	constraint fk_feedback_reply_to_message foreign key(feedback_message_id) references idle_rpg_base.feedback_messages(id)
);
ALTER TABLE idle_rpg_base.feedback_replies
  OWNER TO idle_rpg_user;