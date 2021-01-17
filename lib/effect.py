

class Effect:
    def __init__(self, name, is_positive, attack, defence, init_duration, damage_per_turn, heal_per_turn, effect_type):
        self.name = name
        self.type = effect_type
        self.is_positive = is_positive
        self.attack = attack
        self.defence = defence
        self.init_duration = init_duration
        self.duration = init_duration
        self.damage_per_turn = damage_per_turn
        self.heal_per_turn = heal_per_turn

    def tick(self, target):
        target.hp -= self.damage_per_turn
        target.hp += min(self.heal_per_turn, target.max_hp - target.hp)
        self.duration -= 1

    def __str__(self):
        res = "{0}:".format(self.name)
        if self.attack != 0:
            res += " attack {0}".format(self.attack)
        if self.defence != 0:
            res += " defence {0}".format(self.defence)
        if self.damage_per_turn != 0:
            res += " damage per turn {0}".format(self.damage_per_turn)
        if self.heal_per_turn != 0:
            res += " heal per turn {0}".format(self.heal_per_turn)
        res += " duration  {0} / {1}".format(self.duration, self.init_duration)
        return res


class EffectType:
    def __init__(self, name, is_positive, attack, defence, duration, damage_per_turn, heal_per_turn,
                 level_scale_modifier=0):
        self.name = name
        self.is_positive = is_positive
        if attack is not None:
            self.attack = attack
        else:
            self.attack = 0
        if defence is not None:
            self.defence = defence
        else:
            self.defence = 0
        self.duration = duration
        if damage_per_turn is not None:
            self.damage_per_turn = damage_per_turn
        else:
            self.damage_per_turn = 0
        if heal_per_turn is not None:
            self.heal_per_turn = heal_per_turn
        else:
            self.heal_per_turn = 0
        if level_scale_modifier is not None:
            self.level_scale_modifier = level_scale_modifier
        else:
            self.level_scale_modifier = 0

    def apply(self, target):
        effect = Effect(self.name, self.is_positive, self.attack * (1 + self.level_scale_modifier * (target.level - 1)),
                        self.defence * (1 + self.level_scale_modifier * (target.level - 1)), self.duration,
                        self.damage_per_turn * (1 + self.level_scale_modifier * (target.level - 1)),
                        self.heal_per_turn * (1 + self.level_scale_modifier * (target.level - 1)),
                        self)
        target.effects.append(effect)

    def __str__(self):
        res = ""
        if self.attack != 0:
            res += " attack {0}".format(self.attack)
        if self.defence != 0:
            res += " defence {0}".format(self.defence)
        if self.damage_per_turn != 0:
            res += " damage per turn {0}".format(self.damage_per_turn)
        if self.heal_per_turn != 0:
            res += " heal per turn {0}".format(self.heal_per_turn)
        if self.level_scale_modifier != 0:
            res += " effect strength increased on {0} per level".format(self.level_scale_modifier)
        res += " duration  {0}".format(self.duration)
        return res
