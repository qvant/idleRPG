from .messages import M_CLASS_HEADER, M_CHARACTER_SPELL_LIST, M_CHARACTER_HAVE_NO_SPELLS, M_CHARACTER_ABILITIES_LIST, \
    M_CHARACTER_HAVE_NO_ABILITIES


class CharClass:
    def __init__(self, init_hp, init_mp, init_attack, init_defence, class_name):
        self.init_hp = init_hp
        self.init_mp = init_mp
        self.init_attack = init_attack
        self.init_defence = init_defence
        self.class_name = class_name
        self.spells = []
        self.abilities = []

    def add_spell(self, spell):
        self.spells.append(spell)

    def add_ability(self, ability):
        self.abilities.append(ability)

    def init_character(self, character):
        character.class_name = self.class_name
        character.hp = self.init_hp
        character.max_hp = self.init_hp
        character.mp = self.init_mp
        character.max_mp = self.init_mp
        character.base_attack = self.init_attack
        character.base_defence = self.init_defence
        character.spells = self.spells
        character.abilities = self.abilities

    def level_up(self, character):
        character.max_hp += self.init_hp
        character.max_mp += self.init_mp
        character.base_attack += self.init_attack
        character.base_defence += self.init_defence

    def translate(self, trans, code):
        # TODO: reuse this code in character's translation
        res = trans.get_message(M_CLASS_HEADER, code).\
            format(trans.get_message(self.class_name, code),
                   self.init_attack, self.init_defence, self.init_hp, self.init_mp)
        res += chr(10)
        first_spell = True
        for i in self.spells:
            if first_spell:
                first_spell = False
                res += trans.get_message(M_CHARACTER_SPELL_LIST, code)
                res += chr(10)
            res += "  "
            res += i.translate(trans, code)
            res += chr(10)
        if first_spell:
            res += trans.get_message(M_CHARACTER_HAVE_NO_SPELLS, code)
        res += chr(10)
        first_ability = True
        for i in self.abilities:
            if first_ability:
                first_ability = False
                res += trans.get_message(M_CHARACTER_ABILITIES_LIST, code)
                res += chr(10)
            res += "  "
            res += i.translate(trans, code)
            res += chr(10)
        if first_ability:
            res += trans.get_message(M_CHARACTER_HAVE_NO_ABILITIES, code)
        return res
