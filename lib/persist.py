import psycopg2

from .character import Character
from .consts import ITEM_SLOT_WEAPON, ITEM_SLOT_ARMOR, LOG_PERSIST
from .item import Item
from .utility import get_logger


class Persist:
    def __init__(self, config):
        self.logger = get_logger(LOG_PERSIST, config.log_level, is_system=True)
        self.conn = psycopg2.connect(dbname=config.db_name, user=config.db_user,
                                     password=config.db_password, host=config.db_host, port=config.db_port)
        self.cursor = self.conn.cursor()
        self.stop_on_error = config.halt_on_persist_errors
        self.was_error = False
        self.logger.info('Persist ready')

    def renew(self, config):
        self.conn.close()
        self.__init__(config)

    def commit(self):
        try:
            self.conn.commit()
        except psycopg2.Error as err:
            if self.stop_on_error:
                self.logger.critical(err)
                raise
            else:
                self.was_error = True
                self.logger.error(err)

    def rollback(self, suppress_errors: bool = False):
        try:
            self.conn.rollback()
        except psycopg2.Error as err:
            self.logger.critical(str(err))
            if suppress_errors:
                pass
            else:
                raise

    def clear_all(self):
        self.cursor.execute("""truncate table idle_rpg_base.characters;""")
        self.cursor.execute("""truncate table idle_rpg_base.feedback_messages;""")
        self.commit()
        self.logger.warn("Persist cleared")

    def load_all_characters(self, class_list, ai):
        class_by_name = {}
        players = []
        self.logger.info("Character loading started")
        for i in class_list:
            class_by_name.update({i.class_name: i})
        self.cursor.execute("""
            select  id, 
                    name,
                    class_name,
                    level,
                    exp,
                    hp,
                    max_hp,
                    mp,
                    max_mp,
                    base_attack,
                    base_defence,
                    monsters_killed,
                    quests_completed,
                    gold,
                    health_potions,
                    mana_potions,
                    deaths,
                    weapon_name, weapon_level, armor_name, armor_level, telegram_id
                from idle_rpg_base.characters
        """)
        cnt = 0
        for db_id, name, class_name, level, exp, hp, max_hp, mp, max_mp, base_attack, base_defence, monsters_killed,\
            quests_completed, gold, health_potions, mana_potions, deaths, weapon_name, weapon_level, armor_name, \
            armor_level, telegram_id \
                in self.cursor:

            player = Character(name, class_by_name[class_name], telegram_id=telegram_id, is_created=False)
            player.level = level
            player.exp = exp
            player.hp = max_hp
            player.max_hp = max_hp
            player.mp = max_mp
            player.max_mp = max_mp
            player.base_attack = base_attack
            player.base_defence = base_defence
            player.monsters_killed = monsters_killed
            player.quests_complete = quests_completed
            player.gold = gold
            player.health_potions = health_potions
            player.mana_potions = mana_potions
            player.deaths = deaths
            player.ai = ai
            player.need_save = False
            player.set_id(db_id)
            if len(weapon_name) > 0:
                weapon = Item(1, ITEM_SLOT_WEAPON)
                weapon.set_name(weapon_name)
                weapon.level = weapon_level
                weapon.equip(player)
            if len(armor_name) > 0:
                armor = Item(1, ITEM_SLOT_ARMOR)
                armor.set_name(armor_name)
                armor.level = armor_level
                armor.equip(player)
            players.append(player)
            cnt += 1
            if cnt >= 100:
                self.logger.info("Character loading in progress, {0} characters loaded so far".format(len(players)))
                cnt = 0
        self.logger.info("Character loading finished, {0} characters loaded".format(len(players)))
        return players

    def delete_character(self, character):
        character.need_save = True
        self.save_character(character)
        self.cursor.execute("""
        insert into idle_rpg_base.arch_characters (select * from idle_rpg_base.characters t where t.id = %s)
        """, (character.id,))
        self.cursor.execute("""
        delete from idle_rpg_base.characters t where t.id = %s
        """, (character.id,))

    def save_character(self, character):
        if character.need_save or self.was_error:
            try:
                character.need_save = False
                if character.weapon is not None:
                    weapon_name = character.weapon._name
                    weapon_level = character.weapon.level
                else:
                    weapon_name = ''
                    weapon_level = None
                if character.armor is not None:
                    armor_name = character.armor._name
                    armor_level = character.armor.level
                else:
                    armor_name = ''
                    armor_level = None
                if character.id is None:
                    self.cursor.execute("""
                INSERT INTO idle_rpg_base.characters (name, class_name, level, exp, hp, max_hp, mp, max_mp,
                                                        base_attack, base_defence, monsters_killed, quests_completed, 
                                                        gold,
                                                        health_potions, mana_potions, deaths,
                                                        weapon_name, weapon_level, armor_name, armor_level, 
                                                        telegram_id)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, 
                            %s, %s, %s) 
                 returning id;
                 """,
                                        (character.name, character.class_name, character.level, character.exp,
                                         character.hp,
                                         character.max_hp, character.mp, character.max_mp,
                                         character.base_attack, character.base_defence, character.monsters_killed,
                                         character.quests_complete,
                                         character.gold,
                                         character.health_potions, character.mana_potions, character.deaths,
                                         weapon_name, weapon_level, armor_name,
                                         armor_level, character.telegram_id))
                    character.id = self.cursor.fetchone()[0]

                else:
                    self.cursor.execute("""
                        update idle_rpg_base.characters 
                            set name=%s, class_name=%s, level=%s, exp=%s, hp=%s, max_hp=%s, mp=%s, max_mp=%s,
                                base_attack=%s, base_defence=%s, monsters_killed=%s, quests_completed=%s, gold=%s,
                                health_potions=%s, mana_potions=%s, deaths=%s, 
                                weapon_name=%s, weapon_level=%s, armor_name=%s, 
                                armor_level=%s, 
                                dt_updated = current_timestamp
                         where id = %s;
                         """,
                                        (character.name, character.class_name, character.level, character.exp,
                                         character.hp,
                                         character.max_hp, character.mp, character.max_mp,
                                         character.base_attack, character.base_defence, character.monsters_killed,
                                         character.quests_complete,
                                         character.gold,
                                         character.health_potions, character.mana_potions, character.deaths,
                                         weapon_name, weapon_level, armor_name,
                                         armor_level,
                                         character.id))
                if self.was_error:
                    self.was_error = False
                    self.logger.info('Persist restored after error')
            except psycopg2.Error as err:
                if self.stop_on_error:
                    self.logger.critical(err)
                    raise
                else:
                    self.was_error = True
                    character.need_save = True
                    self.logger.error(err)

    def load_messages(self, message_list):
        self.cursor.execute(
            """
            select id, telegram_id, telegram_nickname, message from idle_rpg_base.feedback_messages where not is_read
            """
        )
        for msg_id, telegram_id, telegram_nickname, message in self.cursor:
            message_list.add_message(telegram_id=telegram_id, telegram_nickname=telegram_nickname, message=message,
                                     msg_id=msg_id, suppress_limit_check=True)

    def save_message_reply(self, message_id: int, telegram_id: int, message: str):
        self.cursor.execute(
            """
            insert into idle_rpg_base.feedback_replies
                (feedback_message_id, telegram_id, message)
                values(%s, %s, %s) 
            """, (message_id, telegram_id, message)
        )

    def save_message(self, message, user_id=None):
        if message.id is None:
            self.cursor.execute(
                """
                insert into idle_rpg_base.feedback_messages
                    (telegram_id, telegram_nickname, message)
                    values(%s, %s, %s) returning id
                """, (message.telegram_id, message.telegram_nickname, message.message)
            )
            message.id = self.cursor.fetchone()[0]
        else:
            self.cursor.execute(
                """
                update idle_rpg_base.feedback_messages 
                    set is_read = True, 
                        dt_read=current_timestamp,
                        read_by = %s 
                    where id = %s
                """, (user_id, message.id,)
            )
        self.commit()
