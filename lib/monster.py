from .messages import *
from .event import Event, EVENT_TYPE_FOUND_LOOT


class MonsterType:
    def __init__(self, name: str, attack: int, defence: int, hp: int, exp: int, gold: int,
                 level_multiplier: int, level: int):
        self.name = name
        self.attack = attack
        self.defence = defence
        self.hp = hp
        self.exp = exp
        self.gold = gold
        self.level_multiplier = level_multiplier
        self.level = level
        self.level_applied = False

    def create_monster(self, apply_level: int, player):
        m = Monster(self.name, self.attack, self.defence, self.hp, self.exp, self.gold, self.level_multiplier,
                    apply_level, player)
        if apply_level > 0:
            m.apply_level(apply_level)
        return m


class Monster:
    def __init__(self, name: str, attack: int, defence: int, hp: int, exp: int, gold: int, level_multiplier: int,
                 level: int, player):
        self.name = name
        self.base_attack = attack
        self.base_defence = defence
        self.hp = hp
        self.max_hp = hp
        self.exp = exp
        self.gold = gold
        self.level_multiplier = level_multiplier
        self.level = level
        self.level_applied = False
        self.player = player
        self.effects = []

    @property
    def trans(self):
        return self.player.trans

    @property
    def locale(self):
        return self.player.locale

    @property
    def die_at(self):
        return 0

    @property
    def attack(self):
        effect_bonus = 0
        effect_percent = 1
        for i in self.effects:
            effect_bonus += i.attack
            if i.attack_percent != 1:
                effect_percent += i.attack_percent
        return round(max((self.base_attack + effect_bonus) * effect_percent, 0))

    @property
    def defence(self):
        effect_bonus = 0
        effect_percent = 1
        for i in self.effects:
            effect_bonus += i.defence
            if i.defence_percent != 1:
                effect_percent += i.defence_percent
        return round((self.base_defence + effect_bonus) * effect_percent)

    def apply_effects(self):
        for i in self.effects:
            i.tick(self)
            if i.duration <= 0:
                self.effects.remove(i)
        if self.hp <= 0:
            self.die()

    def apply_level(self, level: int):
        if not self.level_applied:
            self.level_applied = True
            self.base_attack = round(self.base_attack * level * self.level_multiplier)
            self.base_defence = round(self.base_defence * level * self.level_multiplier)
            self.hp = round(self.hp * level * self.level_multiplier)
            self.exp = round(self.exp * level * self.level_multiplier)

    def die(self):
        self.player.give_exp(self.exp)
        self.player.give_gold(self.gold)
        self.player.monsters_killed += 1
        self.player.save_history(
            Event(player=self.player, event_type=EVENT_TYPE_FOUND_LOOT, enemy=self, gold=self.gold,
                  exp=self.exp))
        self.player.set_enemy(None)

    def translate(self, is_ablative: bool = False):
        res = "{0} ({6}: {1}/{9}, {4}: {7}({2}), {5}: {8}({3})). ".format(
            self.player.trans.get_message(self.name, self.player.locale, is_ablative=is_ablative),
            self.hp, self.attack, self.defence,
            self.player.trans.get_message(M_ATTACK, self.player.locale).capitalize(),
            self.player.trans.get_message(M_DEFENCE, self.player.locale).capitalize(),
            self.player.trans.get_message(M_HP, self.player.locale).capitalize(),
            self.base_attack, self.base_defence, self.max_hp)

        if len(self.effects) > 0:
            res += self.player.trans.get_message(M_CHARACTER_EFFECT_LIST, self.player.locale)
            for i in self.effects:
                res += "  " + str(i) + ";"

        return res

    def __str__(self):
        return self.translate()
