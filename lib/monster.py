class Monster:
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

    def apply_level(self, level):
        if not self.level_applied:
            self.level_applied = True
            self.attack = round(self.attack * level * self.level_multiplier)
            self.defence = round(self.defence * level * self.level_multiplier)
            self.hp = round(self.hp * level * self.level_multiplier)
            self.exp = round(self.exp * level * self.level_multiplier)

    def __str__(self):
        return "{0} HP: {1}, attack: {2}, defence: {3}".format(self.name, self.hp, self.attack, self.defence)
