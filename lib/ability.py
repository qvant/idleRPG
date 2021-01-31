from .messages import *
from .event import Event, EVENT_TYPE_USED_ABILITY
from .utility import check_chance

ABILITY_BACKSTAB = "backstab"
ABILITY_SHIELD_SLAM = "Shield slam"
ABILITY_ASSAULT = "Assault"
ABILITY_SECOND_STRIKE = "Second strike"
ABILITY_BLEED = "Bleed"
ABILITY_JUST_EFFECT = "JUST_EFFECT"
ABILITY_TRIGGER_COMBAT_START = "combat_start"
ABILITY_TRIGGER_COMBAT_ATTACK = "combat_attack"
ABILITY_TRIGGER_COMBAT_RECEIVE_DMG = "receive_damage"

ABILITY_TRIGGERS = [ABILITY_TRIGGER_COMBAT_START, ABILITY_TRIGGER_COMBAT_ATTACK, ABILITY_TRIGGER_COMBAT_RECEIVE_DMG]
ABILITIES = [ABILITY_BACKSTAB, ABILITY_SHIELD_SLAM, ABILITY_ASSAULT, ABILITY_SECOND_STRIKE, ABILITY_BLEED,
             ABILITY_JUST_EFFECT]


class AbilityType:
    def __init__(self, name, event, action, description_code, chance, effect=None):
        self.name = name
        self.chance = chance
        self.effect = effect
        self.description_code = description_code
        if event in ABILITY_TRIGGERS:
            self.event = event
        else:
            raise ValueError("event type {0} not supported".format(event))
        if action in ABILITIES:
            self.action = action
        else:
            raise ValueError("ability action {0} not supported".format(action))

    def trigger(self, event_type, player, from_ability=False):
        if event_type == self.event:
            if check_chance(self.chance):
                self.use(player, from_ability)

    def use(self, player, from_ability=False):
        # TODO: make separate functions, also think about more flexible way to implement them
        if self.action == ABILITY_BACKSTAB:
            if player.enemy is not None:
                dmg = player.attack + player.level
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
        elif self.action == ABILITY_SHIELD_SLAM:
            if player.enemy is not None:
                dmg = player.defence
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
        elif self.action == ABILITY_ASSAULT:
            if player.enemy is not None:
                dmg = player.defence * 3
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
        elif self.action == ABILITY_SECOND_STRIKE:
            if player.enemy is not None:
                dmg = max(player.attack - player.enemy.defence, 0)
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
                # TODO: make singe method to normal attack
                # Trigger on attack effects
                if not from_ability:
                    for i in player.abilities:
                        i.trigger(event_type=ABILITY_TRIGGER_COMBAT_ATTACK, player=player, from_ability=True)
        elif self.action == ABILITY_BLEED:
            if player.enemy is not None:
                dmg = 1
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
                # TODO: make singe method to normal attack
                # Trigger on attack effects
                if not from_ability:
                    for i in player.abilities:
                        i.trigger(event_type=ABILITY_TRIGGER_COMBAT_ATTACK, player=player, from_ability=True)

        if player.enemy is not None:
            if player.enemy.hp <= 0:
                player.enemy.die()
        if player.enemy is not None and self.effect is not None:
            if self.effect.is_positive:
                self.effect.apply(player)
            else:
                self.effect.apply(player.enemy)

    def translate(self, trans, code):
        res = "{0} ({1}: {2}. {3}. {4}: {5} %.".format(trans.get_message(self.name, code).capitalize(),
                                                       trans.get_message(M_ABILITY_TRIGGER, code),
                                                       trans.get_message(self.event, code),
                                                       trans.get_message(self.description_code, code),
                                                       trans.get_message(M_ABILITY_CHANCE, code),
                                                       int(self.chance * 100))
        if self.effect is not None:
            res += " {1}: {0}".format(self.effect.translate(trans, code),
                                      trans.get_message(M_EFFECT, code).capitalize())
        res += ")"
        return res
