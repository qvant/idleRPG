import random

from .consts import ITEM_SLOT_ARMOR, ITEM_SLOT_WEAPON
from .utility import get_random_array_element


class Item:
    weapon_list = {}
    armor_list = {}

    def __init__(self, level: int, slot: int):
        if slot == ITEM_SLOT_WEAPON:
            self.affix = get_random_array_element(Item.weapon_list["affixes"])
            self.type = get_random_array_element(Item.weapon_list["types"])
            self.suffix = get_random_array_element(Item.weapon_list["suffixes"])
        if slot == ITEM_SLOT_ARMOR:
            self.affix = get_random_array_element(Item.armor_list["affixes"])
            self.type = get_random_array_element(Item.armor_list["types"])
            self.suffix = get_random_array_element(Item.armor_list["suffixes"])
        self.level = round(random.random() * level + 1)
        self.slot = slot
        self.owner = None

    @property
    def name(self) -> str:
        if self.owner is None:
            return self._name
        else:
            return "{0} {1} {2}".format(self.owner.trans.get_message(self.affix, self.owner.locale,
                                                                     connected_word=self.type),
                                        self.owner.trans.get_message(self.type, self.owner.locale),
                                        self.owner.trans.get_message(self.suffix, self.owner.locale))

    def name_in_form(self, is_ablative: bool = False, is_accusative: bool = False) -> str:
        if self.owner is None:
            return self._name
        else:
            return "{0} {1} {2}".format(self.owner.trans.get_message(self.affix, self.owner.locale,
                                                                     connected_word=self.type, is_ablative=is_ablative,
                                                                     is_accusative=is_accusative),
                                        self.owner.trans.get_message(self.type, self.owner.locale,
                                                                     is_ablative=is_ablative,
                                                                     is_accusative=is_accusative),
                                        self.owner.trans.get_message(self.suffix, self.owner.locale))

    @property
    def _name(self) -> str:
        return "{0} {1} {2}".format(self.affix, self.type, self.suffix)

    @property
    def price(self) -> int:
        return self.level * 250

    @property
    def attack(self) -> int:
        res = 0
        if self.slot == ITEM_SLOT_WEAPON:
            res = self.level
        return res

    @property
    def defence(self) -> int:
        res = 0
        if self.slot == ITEM_SLOT_ARMOR:
            res = self.level
        return res

    # recover parts of name from result string
    def set_name(self, name: str):
        parts = name.split(" ")
        # TODO: rewrite completely
        pos = 0
        self.affix = ""
        while pos < len(parts):
            if len(self.affix) > 0:
                self.affix += " "
            self.affix += parts[pos]
            pos += 1
            self.affix = self.affix.strip()
            if self.slot == ITEM_SLOT_WEAPON:
                if self.affix in Item.weapon_list["affixes"]:
                    break
            elif self.slot == ITEM_SLOT_ARMOR:
                if self.affix in Item.armor_list["affixes"]:
                    break
        self.type = ""
        while pos < len(parts):
            if len(self.type) > 0:
                self.type += " "
            self.type += parts[pos]
            pos += 1
            self.type = self.type.strip()
            if self.slot == ITEM_SLOT_WEAPON:
                if self.type in Item.weapon_list["types"]:
                    break
            elif self.slot == ITEM_SLOT_ARMOR:
                if self.type in Item.armor_list["types"]:
                    break
        self.suffix = ""
        while pos < len(parts):
            if len(self.suffix) > 0:
                self.suffix += " "
            self.suffix += parts[pos]
            pos += 1
            self.suffix = self.suffix.strip()
            if self.slot == ITEM_SLOT_WEAPON:
                if self.suffix in Item.weapon_list["suffixes"]:
                    break
            elif self.slot == ITEM_SLOT_ARMOR:
                if self.suffix in Item.armor_list["suffixes"]:
                    break

    def equip(self, owner):
        self.owner = owner
        if self.slot == ITEM_SLOT_WEAPON:
            owner.weapon = self
        elif self.slot == ITEM_SLOT_ARMOR:
            owner.armor = self

    def translate(self, is_ablative: bool = False, is_accusative: bool = False):
        return "{0} + {1}".format(self.name_in_form(is_ablative=is_ablative, is_accusative=is_accusative), self.level)

    def __str__(self):
        return "{0} + {1}".format(self.name, self.level)
