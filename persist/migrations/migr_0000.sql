CREATE SCHEMA idle_rpg_base
       AUTHORIZATION idle_rpg_user;
create table idle_rpg_base.characters
(
	id serial primary key,
	name text,
	class_name text,
	level integer,
	exp integer,
	hp integer,
	max_hp integer,
	mp integer,
	max_mp integer,
	base_attack integer,
	base_defence integer,
	monsters_killed integer,
	quests_completed integer,
	gold integer,
	health_potions integer,
	mana_potions integer,
	deaths integer,
	weapon_name text,
	weapon_level integer,
	armor_name text,
	armor_level integer,
	dt_created timestamp with time zone default CURRENT_TIMESTAMP,
	dt_updated timestamp with time zone,
	telegram_id integer
);
alter table  idle_rpg_base.characters owner to idle_rpg_user;
create unique index udx_characters_name on idle_rpg_base.characters(name);

create table idle_rpg_base.arch_characters
(
	id integer primary key,
	name text,
	class_name text,
	level integer,
	exp integer,
	hp integer,
	max_hp integer,
	mp integer,
	max_mp integer,
	base_attack integer,
	base_defence integer,
	monsters_killed integer,
	quests_completed integer,
	gold integer,
	health_potions integer,
	mana_potions integer,
	deaths integer,
	weapon_name text,
	weapon_level integer,
	armor_name text,
	armor_level integer,
	dt_created timestamp with time zone default CURRENT_TIMESTAMP,
	dt_updated timestamp with time zone,
	telegram_id integer
);
alter table  idle_rpg_base.arch_characters owner to idle_rpg_user;

create table idle_rpg_base.feedback_messages
(
	id serial primary key,
	telegram_id integer,
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
