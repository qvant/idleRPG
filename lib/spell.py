import random
from .messages import *

class Spell:
    def __init__(self, name, cost, min_damage, max_damage, is_positive=False, effect=None):
        self.name = name
        self.cost = int(cost)
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.is_positive = is_positive
        self.effect = effect

    @property
    def damage(self):
        return round(self.max_damage + self.min_damage / 2)

    def roll_damage(self):
        return round((self.max_damage - self.min_damage) * random.random()) + self.min_damage

    def translate(self, trans, code):
        res = "{0} ({2}: {1} {3}".format(trans.get_message(self.name, code), self.cost,
                                         trans.get_message(M_COST_MP, code), trans.get_message(M_MP, code))
        if self.min_damage > 0:
            res += ", {2}: {0}, {3}: {1}".format(self.min_damage, self.max_damage,
                                                 trans.get_message(M_MIN_DAMAGE, code),
                                                 trans.get_message(M_MAX_DAMAGE, code))
        if self.effect is not None:
            res += ", {1}: {0}".format(self.effect.translate(trans, code), trans.get_message(M_EFFECT, code))
        res += ")"
        return res

    def __str__(self):
        res = "{0} (cost: {1} mp".format(self.name, self.cost)
        if self.min_damage > 0:
            res += ", min damage: {0}, max damage: {1}".format(self.min_damage, self.max_damage)
        if self.effect is not None:
            res += ", effect: {0}".format(str(self.effect))
        res += ")"
        return res
