from .messages import *


class Effect:
    def __init__(self, name, is_positive, attack, defence, init_duration, damage_per_turn, heal_per_turn, effect_type,
                 owner, attack_percent=None, defence_percent=None, die_at=None):
        self.name = name
        self.type = effect_type
        self.is_positive = is_positive
        self.attack = int(attack)
        self.attack_percent = attack_percent
        self.defence = int(defence)
        self.defence_percent = defence_percent
        self.init_duration = init_duration
        self.duration = init_duration
        self.damage_per_turn = damage_per_turn
        self.heal_per_turn = heal_per_turn
        self.owner = owner
        self.die_at = die_at

    def tick(self, target):
        target.hp -= self.damage_per_turn
        target.hp += min(self.heal_per_turn, target.max_hp - target.hp)
        self.duration -= 1

    def __str__(self):
        # TODO use str from type, they are quite the same
        res = "{0}:".format(self.owner.trans.get_message(self.name, self.owner.locale))
        if self.attack != 0:
            res += " {1} {0}".format(self.attack, self.owner.trans.get_message(M_ATTACK, self.owner.locale))
        if self.defence != 0:
            res += " {1} {0}".format(self.defence, self.owner.trans.get_message(M_DEFENCE, self.owner.locale))
        if self.attack_percent != 1:
            res += " {1} {0}%".format(int(self.attack_percent * 100),
                                      self.owner.trans.get_message(M_ATTACK, self.owner.locale))
        if self.defence_percent != 1:
            res += " {1} {0}%".format(int(self.defence_percent * 100),
                                      self.owner.trans.get_message(M_DEFENCE, self.owner.locale))
        if self.damage_per_turn != 0:
            res += " {1} {0}".format(self.damage_per_turn, self.owner.trans.get_message(M_DAMAGE_PER_TURN,
                                                                                        self.owner.locale))
        if self.heal_per_turn != 0:
            res += " {1} {0}".format(self.heal_per_turn,
                                     self.owner.trans.get_message(M_HEAL_PER_TURN, self.owner.locale))
        if self.die_at != 0:
            res += " {1} {0}".format(self.die_at,
                                     self.owner.trans.get_message(M_DIE_AT, self.owner.locale))
        res += " {2}  {0} / {1}".format(self.duration, self.init_duration,
                                        self.owner.trans.get_message(M_DURATION, self.owner.locale))
        return res


class EffectType:
    def __init__(self, name, is_positive, attack, defence, duration, damage_per_turn, heal_per_turn,
                 level_scale_modifier=0, attack_percent=None, defence_percent=None, can_stack=None,
                 die_at=None):
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
        if attack_percent is not None:
            self.attack_percent = attack_percent
        else:
            self.attack_percent = 1
        if defence_percent is not None:
            self.defence_percent = defence_percent
        else:
            self.defence_percent = 1
        if can_stack is not None:
            self.can_stack = can_stack
        else:
            self.can_stack = False
        if die_at is not None:
            self.die_at = die_at
        else:
            self.die_at = 0

    def apply(self, target):
        applied = False
        if not self.can_stack:
            for i in target.effects:
                if i.name == self.name:
                    applied = True
                    # renew
                    i.duration = max(self.duration, i.duration)
        if not applied:
            effect = Effect(name=self.name,
                            is_positive=self.is_positive,
                            attack=self.attack * (1 + self.level_scale_modifier * (target.level - 1)),
                            defence=self.defence * (1 + self.level_scale_modifier * (target.level - 1)),
                            init_duration=self.duration,
                            damage_per_turn=self.damage_per_turn * (1 + self.level_scale_modifier * (target.level - 1)),
                            heal_per_turn=self.heal_per_turn * (1 + self.level_scale_modifier * (target.level - 1)),
                            effect_type=self,
                            owner=target,
                            attack_percent=self.attack_percent,
                            defence_percent=self.defence_percent,
                            die_at=self.die_at)
            target.effects.append(effect)

    def translate(self, trans, code):
        res = ""
        if self.attack != 0:
            res += " {1} {0}".format(self.attack, trans.get_message(M_ATTACK, code))
        if self.attack_percent != 1:
            res += " {1} {0}%".format(int(self.attack_percent * 100), trans.get_message(M_ATTACK, code))
        if self.defence != 0:
            if len(res) > 0:
                res += ", "
            res += " {1} {0}".format(self.defence, trans.get_message(M_DEFENCE, code))
        if self.defence_percent != 1:
            if len(res) > 0:
                res += ", "
            res += " {1} {0}%".format((self.defence_percent * 100), trans.get_message(M_DEFENCE, code))
        if self.damage_per_turn != 0:
            if len(res) > 0:
                res += ", "
            res += " {1} {0}".format(self.damage_per_turn, trans.get_message(M_DAMAGE_PER_TURN, code))
        if self.heal_per_turn != 0:
            if len(res) > 0:
                res += ", "
            res += " {1} {0}".format(self.heal_per_turn, trans.get_message(M_HEAL_PER_TURN, code))
        if self.die_at != 0:
            if len(res) > 0:
                res += ", "
            res += " {1} {0}".format(self.die_at, trans.get_message(M_DIE_AT, code))
        if self.level_scale_modifier != 0:
            res += ", "
            res += trans.get_message(M_LEVEL_SCALED, code).format(self.level_scale_modifier)
        res += ", {1}  {0}".format(self.duration, trans.get_message(M_DURATION, code))
        return res

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
