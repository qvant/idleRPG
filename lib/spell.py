import random


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

    def __str__(self):
        res = "{0} (cost: {1} mp".format(self.name, self.cost)
        if self.min_damage > 0:
            res += ", min damage: {0}, max damage: {1}".format(self.min_damage, self.max_damage)
        if self.effect is not None:
            res += ", effect: {0}".format(str(self.effect))
        res += ")"
        return res
