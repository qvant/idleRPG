from .messages import *

class MonsterType:
    def __init__(self, name, attack, defence, hp, exp, gold, level_multiplier, level):
        self.name = name
        self.attack = attack
        self.defence = defence
        self.hp = hp
        self.exp = exp
        self.gold = gold
        self.level_multiplier = level_multiplier
        self.level = level
        self.level_applied = False

    def create_monster(self, apply_level, player):
        m = Monster(self.name, self.attack, self.defence, self.hp, self.exp, self.gold, self.level_multiplier, apply_level, player)
        if apply_level > 0:
            m.apply_level(apply_level)
        return m


class Monster:
    def __init__(self, name, attack, defence, hp, exp, gold, level_multiplier, level, player):
        self.name = name
        self.attack = attack
        self.defence = defence
        self.hp = hp
        self.exp = exp
        self.gold = gold
        self.level_multiplier = level_multiplier
        self.level = level
        self.level_applied = False
        self.player = player

    def apply_level(self, level):
        if not self.level_applied:
            self.level_applied = True
            self.attack = round(self.attack * level * self.level_multiplier)
            self.defence = round(self.defence * level * self.level_multiplier)
            self.hp = round(self.hp * level * self.level_multiplier)
            self.exp = round(self.exp * level * self.level_multiplier)

    def __str__(self):
        return "{0} {6}: {1}, {4}: {2}, {5}: {3}".format(
            self.player.trans.get_message(self.name, self.player.locale), self.hp, self.attack, self.defence,
            self.player.trans.get_message(M_ATTACK, self.player.locale), self.player.trans.get_message(M_DEFENCE, self.player.locale),
        self.player.trans.get_message(M_HP, self.player.locale))
