from .messages import *

EVENT_TYPE_RESURRECTED = 1
EVENT_TYPE_KILLED = 2
EVENT_TYPE_DIED = 3
EVENT_TYPE_DRINK_HEALTH_POTION = 4
EVENT_TYPE_DRINK_MANA_POTION = 5
EVENT_TYPE_RUN_AWAY = 6
EVENT_TYPE_RUN_AWAY_FAILED = 7
EVENT_TYPE_CASTED_SPELL = 8
EVENT_TYPE_CASTED_SPELL_ON_HIMSELF = 9
EVENT_TYPE_FOUND_LOOT = 10
EVENT_TYPE_ACCEPTED_QUEST = 11
EVENT_TYPE_COMPLETED_QUEST = 12
EVENT_TYPE_REACHED_LEVEL = 13
EVENT_TYPE_BOUGHT_HEALTH_POTIONS = 14
EVENT_TYPE_BOUGHT_MANA_POTIONS = 15
EVENT_TYPE_BOUGHT_EQUIPMENT = 16
EVENT_TYPE_RESTED = 17
EVENT_TYPE_USED_ABILITY = 18


class Event:
    def __init__(self, event_type, player, enemy=None, hp=None, mp=None, spell=None, damage=None, potion_number=None,
                 exp=None, gold=None, quest=None, level=None, item=None, ability_type=None):
        self.type = event_type
        self.player = player
        self.enemy = enemy
        self.hp = hp
        self.mp = mp
        self.spell = spell
        self.damage = damage
        self.potion_number = potion_number
        self.exp = exp
        self.gold = gold
        self.quest = quest
        self.level = level
        self.item = item
        self.ability_type = ability_type

    def __str__(self):
        if self.type == EVENT_TYPE_RESURRECTED:
            return self.player.trans.get_message(M_RESURRECTED, self.player.locale).format(self.player.name)
        elif self.type == EVENT_TYPE_KILLED:
            return self.player.trans.get_message(M_KILLED_BY_ENEMY, self.player.locale).\
                format(self.player.name,
                       self.player.trans.get_message(self.enemy.name, self.player.locale))
        elif self.type == EVENT_TYPE_DIED:
            return self.player.trans.get_message(M_DIED, self.player.locale).format(self.player.name)
        elif self.type == EVENT_TYPE_DRINK_HEALTH_POTION:
            return self.player.trans.get_message(M_DRINK_HEALTH_POTION, self.player.locale).format(self.player.name,
                                                                                                   self.hp)
        elif self.type == EVENT_TYPE_DRINK_MANA_POTION:
            return self.player.trans.get_message(M_DRINK_MANA_POTION, self.player.locale).format(self.player.name,
                                                                                                 self.mp)
        elif self.type == EVENT_TYPE_RUN_AWAY:
            return self.player.trans.get_message(M_RUN_AWAY, self.player.locale).format(self.player.name,
                                                                                        self.player.trans.get_message(
                                                                                            self.enemy.name,
                                                                                            self.player.locale),
                                                                                        self.hp)
        elif self.type == EVENT_TYPE_RUN_AWAY_FAILED:
            return self.player.trans.get_message(M_RUN_AWAY_FAILED, self.player.locale).\
                format(self.player.name,
                       self.player.trans.get_message(self.enemy.name, self.player.locale),
                       self.hp)
        elif self.type == EVENT_TYPE_CASTED_SPELL:
            return self.player.trans.get_message(M_CASTED_SPELL, self.player.locale).format(self.player.name,
                                                                                            self.spell.translate(
                                                                                                self.player.trans,
                                                                                                self.player.locale),
                                                                                            self.enemy, self.damage)
        elif self.type == EVENT_TYPE_CASTED_SPELL_ON_HIMSELF:
            return self.player.trans.get_message(M_CASTED_SPELL_ON_HIMSELF, self.player.locale).\
                format(self.player.name,
                       self.spell.translate(self.player.trans, self.player.locale),
                       self.enemy)
        elif self.type == EVENT_TYPE_FOUND_LOOT:
            return self.player.trans.get_message(M_FOUND_LOOT, self.player.locale).\
                format(self.player.name,
                       self.player.trans.get_message(self.enemy.name, self.player.locale),
                       self.gold,
                       self.exp)
        elif self.type == EVENT_TYPE_ACCEPTED_QUEST:
            return self.player.trans.get_message(M_ACCEPTED_QUEST, self.player.locale).format(self.player.name,
                                                                                              self.quest)
        elif self.type == EVENT_TYPE_COMPLETED_QUEST:
            return self.player.trans.get_message(M_COMPLETED_QUEST, self.player.locale).format(self.player.name,
                                                                                               self.quest)
        elif self.type == EVENT_TYPE_REACHED_LEVEL:
            return self.player.trans.get_message(M_REACHED_LEVEL, self.player.locale).format(self.player.name,
                                                                                             self.level)
        elif self.type == EVENT_TYPE_BOUGHT_HEALTH_POTIONS:
            return self.player.trans.get_message(M_BOUGHT_HEALTH_POTIONS, self.player.locale).format(self.player.name,
                                                                                                     self.potion_number)
        elif self.type == EVENT_TYPE_BOUGHT_MANA_POTIONS:
            return self.player.trans.get_message(M_BOUGHT_MANA_POTIONS, self.player.locale).format(self.player.name,
                                                                                                   self.potion_number)
        elif self.type == EVENT_TYPE_BOUGHT_EQUIPMENT:
            return self.player.trans.get_message(M_BOUGHT_EQUIPMENT, self.player.locale).format(self.player.name,
                                                                                                self.item, self.gold)
        elif self.type == EVENT_TYPE_RESTED:
            return self.player.trans.get_message(M_RESTED, self.player.locale).format(self.player.name, self.hp,
                                                                                      self.mp)
        elif self.type == EVENT_TYPE_USED_ABILITY:
            return self.player.trans.get_message(M_USED_ABILITY, self.player.locale).\
                format(self.player.name,
                       self.player.trans.get_message(self.ability_type.name, self.player.locale),
                       self.damage,
                       self.player.trans.get_message(self.enemy.name, self.player.locale))
