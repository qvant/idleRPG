from .messages import *
from .event import Event, EVENT_TYPE_USED_ABILITY
from .utility import check_chance

ABILITY_BACKSTAB = "backstab"
ABILITY_TRIGGER_COMBAT_START = "combat_start"

ABILITY_TRIGGERS = [ABILITY_TRIGGER_COMBAT_START]
ABILITIES = [ABILITY_BACKSTAB]


class AbilityType:
    def __init__(self, name, event, action, description_code, chance):
        self.name = name
        self.chance = chance
        self.description_code = description_code
        if event in ABILITY_TRIGGERS:
            self.event = event
        else:
            raise ValueError("event type {0} not supported".format(event))
        if action in ABILITIES:
            self.action = action
        else:
            raise ValueError("ability action {0} not supported".format(action))

    def trigger(self, event_type, player):
        if event_type == self.event:
            if check_chance(self.chance):
                self.use(player)

    def use(self, player):
        if self.action == ABILITY_BACKSTAB:
            if player.enemy is not None:
                dmg = player.attack + player.level
                player.enemy.hp -= dmg
                player.save_history(Event(player=player, event_type=EVENT_TYPE_USED_ABILITY, damage=dmg,
                                          enemy=player.enemy, ability_type=self))
                if player.enemy.hp <= 0:
                    player.enemy.die()

    def translate(self, trans, code):
        res = "{0} ({1}: {2}. {3}. {4}: {5} %).".format(trans.get_message(self.name, code).capitalize(),
                                                        trans.get_message(M_ABILITY_TRIGGER, code),
                                                        trans.get_message(self.event, code),
                                                        trans.get_message(self.description_code, code),
                                                        trans.get_message(M_ABILITY_CHANCE, code),
                                                        int(self.chance * 100))

        return res
