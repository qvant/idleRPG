import psycopg2
from .character import Character
from .item import Item
from .utility import get_logger
from .consts import ITEM_SLOT_WEAPON, ITEM_SLOT_ARMOR, LOG_PERSIST


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
        self.conn.commit()

    def clear_all(self):
        self.cursor.execute("""truncate table idle_rpg_base.characters;""")
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
                    gold,
                    health_potions,
                    mana_potions,
                    deaths,
                    weapon_name, weapon_level, armor_name, armor_level
                from idle_rpg_base.characters
        """)
        cnt = 0
        for id, name, class_name, level, exp, hp, max_hp, mp, max_mp, base_attack, base_defence, monsters_killed,\
            gold, health_potions, mana_potions, deaths, weapon_name, weapon_level, armor_name, armor_level \
                in self.cursor:

            player = Character(name, class_by_name[class_name])
            player.level = level
            player.exp = exp
            player.hp = hp
            player.max_hp = max_hp
            player.mp = mp
            player.max_mp = max_mp
            player.base_attack = base_attack
            player.base_defence = base_defence
            player.monsters_killed = monsters_killed
            player.gold = gold
            player.health_potions = health_potions
            player.mana_potions = mana_potions
            player.deaths = deaths
            player.ai = ai
            player.need_save = False
            player.set_id(id)
            if len(weapon_name) > 0:
                weapon = Item(1, ITEM_SLOT_WEAPON)
                weapon.name = weapon_name
                weapon.level = weapon_level
                player.weapon = weapon
            if len(armor_name) > 0:
                armor = Item(1, ITEM_SLOT_ARMOR)
                armor.name = armor_name
                armor.level = armor_level
                player.armor = armor
            players.append(player)
            cnt += 1
            if cnt >= 100:
                self.logger.info("Character loading in progress, {0} characters loaded so far".format(len(players)))
                cnt = 0
        self.logger.info("Character loading finished, {0} characters loaded".format(len(players)))
        return players

    def save_character(self, character):
        if character.need_save or self.was_error:
            try:
                character.need_save = False
                if character.weapon is not None:
                    weapon_name = character.weapon.name
                    weapon_level = character.weapon.level
                else:
                    weapon_name = ''
                    weapon_level = None
                if character.armor is not None:
                    armor_name = character.armor.name
                    armor_level = character.armor.level
                else:
                    armor_name = ''
                    armor_level = None
                if character.id is None:
                    self.cursor.execute("""
                INSERT INTO idle_rpg_base.characters (name, class_name, level, exp, hp, max_hp, mp, max_mp,
                                                        base_attack, base_defence, monsters_killed, gold,
                                                        health_potions, mana_potions, deaths,
                                                        weapon_name, weapon_level, armor_name, armor_level)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, 
                            %s);
                 """,
                                        (character.name, character.class_name, character.level, character.exp, character.hp,
                                         character.max_hp, character.mp, character.max_mp,
                                         character.base_attack, character.base_defence, character.monsters_killed,
                                         character.gold,
                                         character.health_potions, character.mana_potions, character.deaths,
                                         weapon_name, weapon_level, armor_name,
                                         armor_level))
                    self.cursor.execute("""select id from idle_rpg_base.characters where name = %s;""", (character.name, ))
                    character.id, = self.cursor.fetchone()

                else:
                    self.cursor.execute("""
                        update idle_rpg_base.characters 
                            set name=%s, class_name=%s, level=%s, exp=%s, hp=%s, max_hp=%s, mp=%s, max_mp=%s,
                                base_attack=%s, base_defence=%s, monsters_killed=%s, gold=%s,
                                health_potions=%s, mana_potions=%s, deaths=%s, 
                                weapon_name=%s, weapon_level=%s, armor_name=%s, 
                                armor_level=%s, 
                                dt_updated = current_timestamp
                         where id = %s;
                         """,
                                        (character.name, character.class_name, character.level, character.exp, character.hp,
                                         character.max_hp, character.mp, character.max_mp,
                                         character.base_attack, character.base_defence, character.monsters_killed,
                                         character.gold,
                                         character.health_potions, character.mana_potions, character.deaths,
                                         weapon_name, weapon_level, armor_name,
                                         armor_level,
                                         character.id))
                if self.was_error:
                    self.was_error = False
                    self.logger.info('Persist restored after error')
            except psycopg2.DatabaseError as err:
                if self.stop_on_error:
                    self.logger.critical(err)
                    raise
                else:
                    self.was_error = True
                    character.need_save = True
                    self.logger.error(err)
