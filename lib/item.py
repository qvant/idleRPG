import random
from .consts import ITEM_SLOT_ARMOR, ITEM_SLOT_WEAPON
from .utility import get_random_array_element


class Item:
    weapon_list = {}
    armor_list = {}

    def __init__(self, level, slot):
        name = ''
        if slot == ITEM_SLOT_WEAPON:
            name = get_random_array_element(Item.weapon_list["affixes"]) + " "
            name += get_random_array_element(Item.weapon_list["types"]) + " "
            name += get_random_array_element(Item.weapon_list["suffixes"])
        if slot == ITEM_SLOT_ARMOR:
            name = get_random_array_element(Item.armor_list["affixes"]) + " "
            name += get_random_array_element(Item.armor_list["types"]) + " "
            name += get_random_array_element(Item.armor_list["suffixes"])
        self.name = name
        self.level = round(random.random() * level + 1)
        self.slot = slot

    @property
    def price(self):
        return self.level * 250

    @property
    def attack(self):
        res = 0
        if self.slot == ITEM_SLOT_WEAPON:
            res = self.level
        return res

    @property
    def defence(self):
        res = 0
        if self.slot == ITEM_SLOT_ARMOR:
            res = self.level
        return res

    def __str__(self):
        return "{0} + {1}".format(self.name, self.level)
