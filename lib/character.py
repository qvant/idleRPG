from .consts import *
from .item import Item
from .utility import check_chance, get_logger
import copy
import math


class Character:
    def __init__(self, name, char_class, telegram_id=None):
        self.id = None
        self.telegram_id = telegram_id
        self.name = name
        self.class_name = ''
        self.char_class = char_class
        self.level = 1
        self.exp = 1
        self.hp = 0
        self.max_hp = 0
        self.mp = 0
        self.max_mp = 0
        self.base_attack = 0
        self.base_defence = 0
        self.spells = []
        self.action = ACTION_NONE
        self.town_distance = 0
        self.quest_progress = 0.00
        self.quests_complete = 0
        self.monsters_killed = 0
        self.gold = 0
        self.health_potions = 0
        self.mana_potions = 0
        self.ai = None
        self.quest = None
        self.enemy = None
        self.dead = False
        self.wait_counter = 0
        self.deaths = 0
        self.armor = None
        self.weapon = None
        self.char_class.init_character(character=self)
        self.need_save = False
        self.logger.info('Character {} {} created'.format(self.name, self.class_name))

    @classmethod
    def set_logger(cls, config):
        cls.logger = get_logger(LOG_CHARACTER, config.log_level)

    @property
    def attack(self):
        if self.weapon is not None:
            item_bonus = self.weapon.level
        else:
            item_bonus = 0
        return self.base_attack + item_bonus

    @property
    def defence(self):
        if self.armor is not None:
            item_bonus = self.armor.level
        else:
            item_bonus = 0
        return self.base_defence + item_bonus

    def set_action(self, action):
        if action not in ACTIONS:
            raise ValueError("Action {) is not exists".format(action))
        self.action = action

    def set_ai(self, ai):
        self.ai = ai

    def set_enemy(self, enemy):
        self.enemy = copy.deepcopy(enemy)

    def set_id(self, id):
        if self.id is None:
            self.id = id
        else:
            raise ValueError("Character {0} already has an id {1}, when attempted to set id = {2}".format(self, self.id, id))

    @property
    def ready(self):
        return self.wait_counter == 0

    @property
    def hp_percent(self):
        return round(self.hp / self.max_hp * 100, 2)

    @property
    def mp_percent(self):
        if self.max_mp == 0:
            return 100
        return round(self.mp / self.max_mp * 100, 2)

    def wait(self):
        self.wait_counter = max(self.wait_counter - 1, 0)

    def resurrect(self):
        self.hp = self.max_mp
        self.mp = self.max_mp
        self.set_action(ACTION_NONE)
        self.enemy = None
        self.dead = False
        self.need_save = True
        self.logger.info("{0} raised from dead".format(self.name))

    def die(self):
        self.hp = 0
        self.mp = 0
        self.town_distance = 0
        self.quest_progress = 0
        self.set_action(ACTION_DEAD)
        self.dead = True
        self.deaths += 1
        self.need_save = True
        self.wait_counter += RESURRECT_TIMER
        self.logger.info("{0} die horrible".format(self.name))

    def drink_health_potion(self):
        if self.health_potions > 0:
            self.health_potions -= 1
            self.hp = self.max_hp
            self.need_save = True
            self.logger.debug("{0} drink health potion".format(self.name), LOG_DEBUG)
        else:
            self.logger.debug("{0} have no health potions".format(self.name), LOG_DEBUG)

    def drink_mana_potion(self):
        if self.mana_potions > 0:
            self.mana_potions -= 1
            self.mp = self.max_mp
            self.need_save = True
            self.logger.debug("{0} drink mana potion".format(self.name), LOG_DEBUG)
        else:
            self.logger.debug("{0} have no mana potions".format(self.name), LOG_DEBUG)

    def fight(self):
        if self.enemy is not None:
            if self.ai.retreat_hp_threshold >= self.hp_percent or self.enemy.attack >= self.hp:
                self.drink_health_potion()
            # check if it is time to run away
            if self.ai.retreat_hp_threshold >= self.hp_percent or self.enemy.attack >= self.hp:
                # success
                if check_chance(0.5):
                    self.logger.info("{0} run away from {1}".format(self.name, self.enemy.name))
                    self.give_exp(round(self.enemy.exp * EXP_FOR_RETREAT_RATIO))
                    self.set_action(ACTION_RETREAT)
                    self.enemy = None
                else:
                    # no penalty for fail
                    pass
                    self.logger.info("{0} tried to run from {1}, but failed".format(self.name, self.enemy.name))
        if self.enemy is not None:
            # decise if need to cast
            made_cast = False
            if len(self.spells) > 0:
                # if it takes to many hit to kill, try spell
                if self.enemy.hp > (self.attack - self.enemy.defence) * self.ai.max_attack_instead_spell:
                    spell = None
                    best_hits = None
                    for sp in self.spells:
                        if sp.cost > self.mp and self.mp_percent < 50:
                            self.drink_mana_potion()
                        if sp.cost <= self.mp:
                            hits = max(self.enemy.hp / sp.damage, 1)
                            if best_hits is None:
                                best_hits = hits
                                spell = sp
                            elif best_hits <= hits:
                                if sp.cost < spell.cost:
                                    best_hits = hits
                                    spell = sp
                    if spell is not None:
                        made_cast = True
                        self.enemy.hp -= spell.roll_damage()
                        self.mp -= spell.cost
                        self.logger.debug("{0} casted {1}".format(self.name, spell.name), LOG_DEBUG)
            self.hp -= max(self.enemy.attack - self.defence, 1)
            if not made_cast:
                self.enemy.hp -= max(self.attack - self.enemy.defence, 0)
            if self.hp <= 0:
                self.die()
            if self.enemy.hp <= 0:
                self.give_exp(self.enemy.exp)
                self.give_gold(self.enemy.gold)
                self.monsters_killed += 1
                self.logger.info("{0} killed {1}".format(self.name, self.enemy.name))
                self.set_enemy(None)

    def set_quest(self, quest):
        self.quest = quest

    def move(self, distance=1):
        self.town_distance += distance
        if self.town_distance < 0:
            self.town_distance = 0

    def do_quest(self):
        self.move()
        self.quest_progress += 1 / (10 + 3 * self.level)
        self.quest_progress = round(self.quest_progress, 2)
        if self.quest_progress >= 100:
            self.quest_progress = 0
            self.give_exp(self.level * 100)
            self.give_gold(self.level * 100)
            self.logger.info("{0} completed quest {1}".format(self.name, self.quest))
            self.set_quest(None)
            self.set_action(ACTION_NONE)
            self.quests_complete += 1

    def give_gold(self, gold):
        self.gold += gold
        self.need_save = True

    def give_exp(self, exp):
        self.exp += exp
        if self.exp >= self.level * 1000 * (1 + self.level - 1) and not self.dead:
            self.level_up()
        self.need_save = True

    def level_up(self):
        self.char_class.level_up(character=self)
        self.rest()
        self.exp = 0
        self.level += 1
        self.logger.info("{0} reached level {1}".format(self.name, self.level))

    def do_shopping(self):
        gold_hp_potion = math.trunc(self.gold / 100 * self.ai.health_potion_gold_percent)
        gold_mp_potion = math.trunc(self.gold / 100 * self.ai.mana_potion_gold_percent)
        while gold_hp_potion > 0 and self.health_potions < self.level:
            if self.gold >= HEALTH_POTION_PRICE:
                self.gold -= HEALTH_POTION_PRICE
                gold_hp_potion -= HEALTH_POTION_PRICE
                self.health_potions += 1
                self.logger.debug("{0} bought health potion".format(self.name), LOG_TRACE)
            else:
                break
        while gold_mp_potion > 0 and self.mana_potions < self.level * 2:
            if self.gold >= MANA_POTION_PRICE:
                self.gold -= MANA_POTION_PRICE
                gold_mp_potion -= MANA_POTION_PRICE
                self.mana_potions += 1
                self.logger.debug("{0} bought mana potion".format(self.name), LOG_TRACE)
            else:
                break
        armor = Item(self.level, ITEM_SLOT_ARMOR)
        if armor.price <= self.gold:
            if self.armor is None or self.armor.level < armor.level:
                self.gold -= armor.price
                self.armor = armor
        weapon = Item(self.level, ITEM_SLOT_WEAPON)
        if weapon.price <= self.gold:
            if self.weapon is None or self.weapon.level < weapon.level:
                self.gold -= weapon.price
                self.weapon = weapon
        self.set_action(ACTION_NONE)
        self.need_save = True

    def rest(self):
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.set_action(ACTION_NONE)
        self.need_save = True

    def __str__(self):
        res = "{0} is level {8} {1}. HP: {2} MP: {3}, EXP: {7}. He is {4} now. He's in {5} miles from town and complete quest \"{9}\" on {6}".\
            format(self.name, self.class_name, self.hp, self.mp,  ACTION_NAMES[self.action], self.town_distance, self.quest_progress, self.exp, self.level, self.quest)
        if self.enemy is not None and not self.dead:
            res += chr(10) + "In fight with: {0}".format(self.enemy)
        if self.dead:
            res += chr(10) + "Waiting for resurrection, {0} turns left".format(self.wait_counter)
        return res