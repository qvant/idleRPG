import copy
import math

from .consts import *
from .item import Item
from .messages import *
from .utility import check_chance, get_logger


class Character:
    def __init__(self, name, char_class, telegram_id=None, is_created=True):
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
        self.locale = 'en'
        self.armor = None
        self.weapon = None
        self.char_class.init_character(character=self)
        self.need_save = False
        self.history = []
        self.effects = []
        if is_created:
            self.logger.info('Character {} {} created'.format(self.name, self.class_name))
        else:
            self.logger.info('Character {} {} loaded from db'.format(self.name, self.class_name))

    @classmethod
    def set_logger(cls, config):
        cls.logger = get_logger(LOG_CHARACTER, config.log_level)

    @classmethod
    def set_translator(cls, trans):
        cls.trans = trans

    @classmethod
    def set_history_length(cls, config):
        cls.history_length = config.char_history_len

    @property
    def attack(self):
        if self.weapon is not None:
            item_bonus = self.weapon.level
        else:
            item_bonus = 0
        effect_bonus = 0
        for i in self.effects:
            effect_bonus += i.attack
        return self.base_attack + item_bonus + effect_bonus

    @property
    def defence(self):
        if self.armor is not None:
            item_bonus = self.armor.level
        else:
            item_bonus = 0
        effect_bonus = 0
        for i in self.effects:
            effect_bonus += i.defence
        return self.base_defence + item_bonus + effect_bonus

    def apply_effects(self):
        for i in self.effects:
            i.tick(self)
            if i.duration <= 0:
                self.effects.remove(i)
        if self.hp <= 0 and not self.dead:
            self.die()

    def set_locale(self, locale):
        self.locale = locale

    def save_history(self, message):
        while len(self.history) >= self.history_length:
            del self.history[0]
        self.history.append(message)
        self.logger.info(message)

    def set_action(self, action):
        if action not in ACTIONS:
            raise ValueError("Action {) is not exists".format(action))
        self.action = action

    def set_ai(self, ai):
        self.ai = ai

    def set_enemy(self, enemy):
        self.enemy = copy.deepcopy(enemy)

    def set_id(self, db_id):
        if self.id is None:
            self.id = db_id
        else:
            raise ValueError("Character {0} already has an id {1}, when attempted to set id = {2}".
                             format(self, self.id, db_id))

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
        self.save_history("{0} raised from dead".format(self.name))

    def die(self):
        self.hp = 0
        self.mp = 0
        self.town_distance = 0
        self.quest_progress = 0
        self.set_action(ACTION_DEAD)
        self.dead = True
        self.effects = []
        self.deaths += 1
        self.need_save = True
        self.wait_counter += RESURRECT_TIMER
        if self.enemy is not None:
            self.save_history("{0} die horrible from the hands of {1}".format(self.name, self.enemy))
        else:
            self.save_history("{0} die horrible".format(self.name))
        self.set_enemy(None)

    def drink_health_potion(self):
        if self.health_potions > 0:
            self.save_history("{0}, while having only {1} hp, feel himself in danger and drink health potion".
                              format(self.name, self.hp))
            self.health_potions -= 1
            self.hp = self.max_hp
            self.need_save = True

    def drink_mana_potion(self):
        if self.mana_potions > 0:
            self.save_history("{0}, while having only {1} mp, drink mana potion".format(self.name, self.mp))
            self.mana_potions -= 1
            self.mp = self.max_mp
            self.need_save = True

    def fight(self):
        if self.enemy is not None:
            if self.ai.retreat_hp_threshold >= self.hp_percent or self.enemy.attack >= self.hp:
                self.drink_health_potion()
            # check if it is time to run away
            if self.ai.retreat_hp_threshold >= self.hp_percent or self.enemy.attack >= self.hp \
                    or self.attack <= self.enemy.defence:
                # success
                if check_chance(0.5):
                    self.save_history("{0} while having only {2} hp, cowardly run away from {1}".
                                      format(self.name, self.enemy.name, self.hp))
                    self.give_exp(round(self.enemy.exp * EXP_FOR_RETREAT_RATIO))
                    self.set_action(ACTION_RETREAT)
                    self.enemy = None
                else:
                    # no penalty for fail
                    pass
                    self.save_history("{0}, while having only {2} hp, tried to run from {1}, but failed".
                                      format(self.name, self.enemy.name, self.hp))
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
                            if sp.is_positive:
                                already_has_buff = False
                                for cur_effect in self.effects:
                                    if sp.effect is not None:
                                        if cur_effect.name == sp.effect.name:
                                            already_has_buff = True
                                if not already_has_buff:
                                    if sp.effect.attack > 0:
                                        spell = sp
                                        # cast buff if avaliable
                                        break
                                    if sp.effect.defence > 0 and self.defence < self.enemy.attack:
                                        spell = sp
                                        # cast buff if avaliable and enemy can hurt us
                                        break
                                    if sp.effect.heal_per_turn > 0 and self.hp_percent <= \
                                            self.ai.max_hp_percent_to_heal:
                                        spell = sp
                                        # cast buff if avaliable and enemy can hurt us
                                        break
                            else:
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
                        if not spell.is_positive:
                            dmg = spell.roll_damage()
                            self.enemy.hp -= dmg
                            self.mp -= spell.cost
                            self.save_history("{0} casted {1} into {2} and inflicted {3} damage".
                                              format(self.name, spell.name, self.enemy.name, dmg))
                        else:
                            self.mp -= spell.cost
                            if spell.effect is not None:
                                spell.effect.apply(self)
                            self.save_history("During fight with {2}, {0} casted {1} on himself".
                                              format(self.name, spell.name, self.enemy.name))
            self.hp -= max(self.enemy.attack - self.defence, 1)
            if self.hp <= 0:
                self.die()
            else:
                if not made_cast:
                    self.enemy.hp -= max(self.attack - self.enemy.defence, 0)
                if self.enemy.hp <= 0:
                    self.give_exp(self.enemy.exp)
                    self.give_gold(self.enemy.gold)
                    self.monsters_killed += 1
                    self.save_history("{0} killed {1} and received {2} gold and {3} exp".format(self.name, self.enemy.name,
                                                                                                self.enemy.gold,
                                                                                                self.enemy.exp))
                    self.set_enemy(None)

    def set_quest(self, quest):
        self.quest = quest
        self.save_history("{0} accepted quest \"{1}\"".format(self.name, self.quest))

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
            self.give_exp(self.level * 300)
            self.give_gold(self.level * 100)
            self.save_history("{0} completed quest \"{1}\"".format(self.name, self.quest))
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
        self.save_history("{0} reached level {1}".format(self.name, self.level))

    def do_shopping(self):
        gold_hp_potion = math.trunc(self.gold / 100 * self.ai.health_potion_gold_percent)
        if self.max_mp > 0:
            gold_mp_potion = math.trunc(self.gold / 100 * self.ai.mana_potion_gold_percent)
        else:
            gold_mp_potion = 0
        potion_number = min(math.trunc(gold_hp_potion / HEALTH_POTION_PRICE), self.level - self.health_potions)
        if potion_number > 0:
            self.gold -= HEALTH_POTION_PRICE * potion_number
            self.health_potions += potion_number
            self.save_history("{0} bought {1} health potions".format(self.name, potion_number))
        potion_number = min(math.trunc(gold_mp_potion / MANA_POTION_PRICE), self.level * 2 - self.mana_potions)
        if potion_number > 0:
            self.gold -= MANA_POTION_PRICE * potion_number
            self.mana_potions += potion_number
            self.save_history("{0} bought {1} mana potions".format(self.name, potion_number))
        armor = Item(self.level, ITEM_SLOT_ARMOR)
        if armor.price <= self.gold:
            if self.armor is None or self.armor.level < armor.level:
                self.gold -= armor.price
                armor.equip(self)
                self.save_history("{0} bought {1} for {2} gold".format(self.name, armor, armor.price))
        weapon = Item(self.level, ITEM_SLOT_WEAPON)
        if weapon.price <= self.gold:
            if self.weapon is None or self.weapon.level < weapon.level:
                self.gold -= weapon.price
                weapon.equip(self)
                self.save_history("{0} bought {1} for {2} gold".format(self.name, weapon, weapon.price))
        self.set_action(ACTION_NONE)
        self.need_save = True

    def rest(self):
        rec_hp = max(self.max_hp - self.hp, 0)
        rec_mp = max(self.max_mp - self.mp, 0)
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.set_action(ACTION_NONE)
        self.need_save = True
        self.save_history("{0} rested and recovered {1} hp and {2} mp".format(self.name, rec_hp, rec_mp))

    def __str__(self):
        res = self.trans.get_message(M_CHARACTER_HEADER, self.locale)\
            .format(self.name, self.class_name, self.hp, self.max_hp, self.mp, self.max_mp, self.exp,
                    self.base_attack, self.attack, self.base_defence, self.defence)
        res += chr(10)
        res += self.trans.get_message(M_CHARACTER_LOCATION, self.locale).\
            format(self.trans.get_message(ACTION_NAMES[self.action], self.locale), self.town_distance,
                   self.quest, self.quest_progress,)
        res += chr(10)
        res += chr(10)
        if self.weapon is not None:
            res += self.trans.get_message(M_CHARACTER_WEAPON, self.locale).format(self.weapon)
        if self.armor is not None:
            res += self.trans.get_message(M_CHARACTER_ARMOR, self.locale).format(self.armor)
        res += chr(10)
        first_spell = True
        for i in self.spells:
            if first_spell:
                first_spell = False
                res += self.trans.get_message(M_CHARACTER_SPELL_LIST, self.locale)
                res += chr(10)
            res += "  "
            res += i.translate(self.trans, self.locale)
            res += chr(10)
        if first_spell:
            res += self.trans.get_message(M_CHARACTER_HAVE_NO_SPELLS, self.locale)
        res += chr(10)
        res += self.trans.get_message(M_CHARACTER_GOLD_AND_POTIONS, self.locale).format(self.gold, self.health_potions,
                                                                                        self.mana_potions)
        if len(self.effects) > 0:
            res += chr(10)
            res += chr(10)
            res += self.trans.get_message(M_CHARACTER_EFFECT_LIST, self.locale)
            for i in self.effects:
                res += "  " + str(i) + chr(10)
        else:
            res += self.trans.get_message(M_CHARACTER_HAVE_NO_EFFECTS, self.locale)

        res += chr(10)
        res += chr(10)
        if len(self.history) > 0:
            res += self.trans.get_message(M_CHARACTER_LAST_EVENTS, self.locale)
            res += chr(10)
        for i in self.history:
            res += i
            res += chr(10)
        if self.enemy is not None and not self.dead:
            res += chr(10) + self.trans.get_message(M_CHARACTER_ENEMY, self.locale).format(self.enemy)
        if self.dead:
            res += chr(10) + self.trans.get_message(M_CHARACTER_RESURRECT_TIMER, self.locale).format(self.wait_counter)
        return res
