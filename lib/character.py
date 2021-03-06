import datetime
import math
import typing

from .ai import CharAI
from .char_classes import CharClass
from .config import Config
from .consts import LOG_CHARACTER, ACTIONS, ABILITY_TRIGGER_COMBAT_START, ACTION_NONE, ACTION_DEAD, RESURRECT_TIMER, \
    EXP_FOR_RETREAT_RATIO, ABILITY_TRIGGER_COMBAT_RECEIVE_DMG, ABILITY_TRIGGER_COMBAT_ATTACK, HEALTH_POTION_PRICE, \
    MANA_POTION_PRICE, ITEM_SLOT_WEAPON, ACTION_RETREAT, ITEM_SLOT_ARMOR, ACTION_NAMES
from .event import Event, EVENT_TYPE_RESURRECTED, EVENT_TYPE_KILLED, EVENT_TYPE_DIED, EVENT_TYPE_DRINK_HEALTH_POTION, \
    EVENT_TYPE_DRINK_MANA_POTION, EVENT_TYPE_RUN_AWAY, EVENT_TYPE_RUN_AWAY_FAILED, EVENT_TYPE_CASTED_SPELL, \
    EVENT_TYPE_CASTED_SPELL_ON_HIMSELF, EVENT_TYPE_ACCEPTED_QUEST, EVENT_TYPE_COMPLETED_QUEST, \
    EVENT_TYPE_REACHED_LEVEL, EVENT_TYPE_BOUGHT_HEALTH_POTIONS, EVENT_TYPE_BOUGHT_MANA_POTIONS, \
    EVENT_TYPE_BOUGHT_EQUIPMENT, EVENT_TYPE_RESTED
from .item import Item
from .l18n import Translator
from .messages import M_CHARACTER_HEADER, M_CHARACTER_LOCATION, M_CHARACTER_WEAPON, M_CHARACTER_ARMOR, \
    M_CHARACTER_HAVE_NO_SPELLS, M_CHARACTER_ABILITIES_LIST, M_CHARACTER_HAVE_NO_ABILITIES, \
    M_CHARACTER_GOLD_AND_POTIONS, M_CHARACTER_EFFECT_LIST, M_CHARACTER_HAVE_NO_EFFECTS, M_CHARACTER_LAST_EVENTS, \
    M_CHARACTER_ENEMY, M_CHARACTER_RESURRECT_TIMER, M_GP, M_POTION, M_CHARACTER_SPELL_LIST
from .monster import Monster
from .quest import Quest
from .utility import check_chance, get_logger


class Character:
    def __init__(self, name: str, char_class: CharClass, telegram_id: int = None, is_created: bool = True):
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
        self.abilities = []
        self.action = ACTION_NONE
        self.town_distance = 0
        self.quest_progress = 0.00
        self.quests_complete = 0
        self.monsters_killed = 0
        self.gold = 0
        self.health_potions = 0
        self.mana_potions = 0
        self.last_user_activity = None
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
    def set_logger(cls, config: Config):
        cls.logger = get_logger(LOG_CHARACTER, config.log_level)

    @classmethod
    def set_translator(cls, trans: Translator):
        cls.trans = trans

    @classmethod
    def set_history_length(cls, config: Config):
        cls.history_length = config.char_history_len

    @property
    def attack(self) -> int:
        if self.weapon is not None:
            item_bonus = self.weapon.level
        else:
            item_bonus = 0
        effect_bonus = 0
        effect_percent = 1
        for i in self.effects:
            effect_bonus += i.attack
            if i.attack_percent != 1:
                effect_percent += i.attack_percent
        return round(max((self.base_attack + item_bonus + effect_bonus) * effect_percent, 0))

    @property
    def die_at(self) -> int:
        effect_bonus = 0
        for i in self.effects:
            effect_bonus += i.die_at
        return effect_bonus

    @property
    def defence(self) -> int:
        if self.armor is not None:
            item_bonus = self.armor.level
        else:
            item_bonus = 0
        effect_bonus = 0
        effect_percent = 1
        for i in self.effects:
            effect_bonus += i.defence
            if i.defence_percent != 1:
                effect_percent += i.defence_percent
        return round((self.base_defence + item_bonus + effect_bonus) * effect_percent)

    def apply_effects(self):
        for i in self.effects:
            i.tick(self)
            if i.duration <= 0:
                self.effects.remove(i)
        if self.hp <= 0 and not self.dead:
            self.die()

    def set_locale(self, locale: str):
        self.locale = locale

    def save_history(self, event: Event):
        while len(self.history) >= self.history_length:
            del self.history[0]
        self.history.append(event)
        self.logger.info(str(event))

    def set_action(self, action: int):
        if action not in ACTIONS:
            raise ValueError("Action {} is not exists".format(action))
        self.action = action

    def set_ai(self, ai: CharAI):
        self.ai = ai

    def set_last_user_activity(self):
        self.last_user_activity = datetime.datetime.now()
        self.need_save = True

    def reset_last_user_activity(self):
        self.last_user_activity = None

    def set_enemy(self, enemy: typing.Union[Monster, None]):
        self.enemy = enemy
        for i in self.abilities:
            i.trigger(event_type=ABILITY_TRIGGER_COMBAT_START, player=self)

    def set_id(self, db_id: int):
        if self.id is None:
            self.id = db_id
        else:
            raise ValueError("Character {0} already has an id {1}, when attempted to set id = {2}".
                             format(self, self.id, db_id))

    @property
    def ready(self) -> bool:
        return self.wait_counter == 0

    @property
    def hp_percent(self) -> float:
        return round(self.hp / self.max_hp * 100, 2)

    @property
    def mp_percent(self) -> float:
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
        self.save_history(Event(player=self, event_type=EVENT_TYPE_RESURRECTED))

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
            self.save_history(Event(player=self, event_type=EVENT_TYPE_KILLED, enemy=self.enemy))
        else:
            self.save_history(Event(player=self, event_type=EVENT_TYPE_DIED))
        self.set_enemy(None)

    def drink_health_potion(self):
        if self.health_potions > 0:
            self.save_history(Event(player=self, event_type=EVENT_TYPE_DRINK_HEALTH_POTION, hp=self.hp))
            self.health_potions -= 1
            self.hp = self.max_hp
            self.need_save = True

    def drink_mana_potion(self):
        if self.mana_potions > 0:
            self.save_history(Event(player=self, event_type=EVENT_TYPE_DRINK_MANA_POTION, mp=self.mp))
            self.mana_potions -= 1
            self.mp = self.max_mp
            self.need_save = True

    def fight(self):
        if self.enemy is not None:
            if self.ai.retreat_hp_threshold >= self.hp_percent or (self.hp <= self.enemy.attack - self.defence
                                                                   < self.max_hp):
                self.drink_health_potion()
            # check if it is time to run away
            if self.ai.retreat_hp_threshold >= self.hp_percent or self.enemy.attack >= self.hp \
                    or self.attack <= self.enemy.defence:
                # success
                if check_chance(0.5):
                    self.save_history(Event(player=self, event_type=EVENT_TYPE_RUN_AWAY, hp=self.hp, enemy=self.enemy))
                    self.give_exp(round(self.enemy.exp * EXP_FOR_RETREAT_RATIO))
                    self.set_action(ACTION_RETREAT)
                    self.enemy = None
                else:
                    # no penalty for fail
                    pass
                    self.save_history(Event(player=self, event_type=EVENT_TYPE_RUN_AWAY_FAILED, hp=self.hp,
                                            enemy=self.enemy))
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
                            self.save_history(
                                Event(player=self, event_type=EVENT_TYPE_CASTED_SPELL, enemy=self.enemy, spell=spell,
                                      damage=dmg))
                        else:
                            self.mp -= spell.cost
                            if spell.effect is not None:
                                spell.effect.apply(self)
                            self.save_history(
                                Event(player=self, event_type=EVENT_TYPE_CASTED_SPELL_ON_HIMSELF, spell=spell,
                                      enemy=self.enemy))
            if self.enemy.attack > 0:
                self.hp -= max(self.enemy.attack - self.defence, 1)
                for i in self.abilities:
                    i.trigger(event_type=ABILITY_TRIGGER_COMBAT_RECEIVE_DMG, player=self)
            if self.hp <= self.die_at:
                self.die()
            else:
                if not made_cast:
                    self.enemy.hp -= max(self.attack - self.enemy.defence, 0)
                if self.enemy.hp <= 0:
                    self.enemy.die()
                else:
                    for i in self.abilities:
                        i.trigger(event_type=ABILITY_TRIGGER_COMBAT_ATTACK, player=self)
                if self.enemy is not None:
                    self.enemy.apply_effects()

    def set_quest(self, quest: typing.Union[Quest, None]):
        self.quest = quest
        self.save_history(
            Event(player=self, event_type=EVENT_TYPE_ACCEPTED_QUEST, quest=self.quest))

    def move(self, distance: int = 1):
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
            self.save_history(
                Event(player=self, event_type=EVENT_TYPE_COMPLETED_QUEST, quest=self.quest))
            self.set_quest(None)
            self.set_action(ACTION_NONE)
            self.quests_complete += 1

    def give_gold(self, gold: int):
        self.gold += gold
        self.need_save = True

    def give_exp(self, exp: int):
        self.exp += exp
        if self.exp >= self.level * 1000 * (1 + self.level - 1) and not self.dead:
            self.level_up()
        self.need_save = True

    def level_up(self):
        self.char_class.level_up(character=self)
        self.rest()
        self.exp = 0
        self.level += 1
        self.save_history(
            Event(player=self, event_type=EVENT_TYPE_REACHED_LEVEL, level=self.level))

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
            self.save_history(
                Event(player=self, event_type=EVENT_TYPE_BOUGHT_HEALTH_POTIONS, potion_number=potion_number))
        potion_number = min(math.trunc(gold_mp_potion / MANA_POTION_PRICE), self.level * 2 - self.mana_potions)
        if potion_number > 0:
            self.gold -= MANA_POTION_PRICE * potion_number
            self.mana_potions += potion_number
            self.save_history(
                Event(player=self, event_type=EVENT_TYPE_BOUGHT_MANA_POTIONS, potion_number=potion_number))
        armor = Item(self.level, ITEM_SLOT_ARMOR)
        if armor.price <= self.gold:
            if self.armor is None or self.armor.level < armor.level:
                self.gold -= armor.price
                armor.equip(self)
                self.save_history(
                    Event(player=self, event_type=EVENT_TYPE_BOUGHT_EQUIPMENT, gold=armor.price, item=armor))
        weapon = Item(self.level, ITEM_SLOT_WEAPON)
        if weapon.price <= self.gold:
            if self.weapon is None or self.weapon.level < weapon.level:
                self.gold -= weapon.price
                weapon.equip(self)
                self.save_history(
                    Event(player=self, event_type=EVENT_TYPE_BOUGHT_EQUIPMENT, gold=weapon.price, item=weapon))
        self.set_action(ACTION_NONE)
        self.need_save = True

    def rest(self):
        rec_hp = max(self.max_hp - self.hp, 0)
        rec_mp = max(self.max_mp - self.mp, 0)
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.set_action(ACTION_NONE)
        self.need_save = True
        self.save_history(
            Event(player=self, event_type=EVENT_TYPE_RESTED, hp=rec_hp, mp=rec_mp))

    def __str__(self):
        res = self.trans.get_message(M_CHARACTER_HEADER, self.locale)\
            .format(self.name, self.trans.get_message(self.class_name, self.locale).lower(), self.hp, self.max_hp,
                    self.mp, self.max_mp, self.exp, self.base_attack, self.attack, self.base_defence, self.defence,
                    self.level, self.die_at)
        res += chr(10)
        res += self.trans.get_message(M_CHARACTER_LOCATION, self.locale).\
            format(self.trans.get_message(ACTION_NAMES[self.action], self.locale), self.town_distance,
                   self.quest, self.quest_progress, self.name)
        res += chr(10)
        res += chr(10)
        if self.weapon is not None:
            res += self.trans.get_message(M_CHARACTER_WEAPON, self.locale).format(
                self.weapon.translate(is_ablative=True))
        if self.armor is not None:
            res += self.trans.get_message(M_CHARACTER_ARMOR, self.locale).format(self.armor.translate(
                is_accusative=True))
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
        first_ability = True
        for i in self.abilities:
            if first_ability:
                first_ability = False
                res += self.trans.get_message(M_CHARACTER_ABILITIES_LIST, self.locale)
                res += chr(10)
            res += "  "
            res += i.translate(self.trans, self.locale)
            res += chr(10)
        if first_ability:
            res += self.trans.get_message(M_CHARACTER_HAVE_NO_ABILITIES, self.locale)
        res += chr(10)
        res += self.trans.get_message(M_CHARACTER_GOLD_AND_POTIONS,
                                      self.locale).format(self.gold,
                                                          self.health_potions,
                                                          self.mana_potions,
                                                          self.trans.get_message(M_GP, self.locale,
                                                                                 connected_number=self.gold),
                                                          self.trans.get_message(M_POTION, self.locale,
                                                                                 connected_number=self.health_potions),
                                                          self.trans.get_message(M_POTION, self.locale,
                                                                                 connected_number=self.mana_potions),
                                                          )
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
            res += '  ' + str(i)
            res += '.' + chr(10)
        if self.enemy is not None and not self.dead:
            res += chr(10) + self.trans.get_message(M_CHARACTER_ENEMY,
                                                    self.locale).format(self.enemy.translate(is_ablative=True))
        if self.dead:
            res += chr(10) + self.trans.get_message(M_CHARACTER_RESURRECT_TIMER, self.locale).format(self.wait_counter)
        return res
