import random


class Spell:
    def __init__(self, name, cost, min_damage, max_damage):
        self.name = name
        self.cost = int(cost)
        self.min_damage = min_damage
        self.max_damage = max_damage

    @property
    def damage(self):
        return round(self.max_damage + self.min_damage / 2)

    def roll_damage(self):
        return round((self.max_damage - self.min_damage) * random.random()) + self.min_damage

    def __str__(self):
        return "{0} cost {1} min damage {2} max damage {3}".format(self.name, self.cost, self.min_damage, self.max_damage)