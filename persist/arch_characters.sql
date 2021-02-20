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
	telegram_id integer,
	dt_last_activity timestamp with time zone
);
alter table  idle_rpg_base.arch_characters owner to idle_rpg_user;