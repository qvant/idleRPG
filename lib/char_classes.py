class CharClass:
    def __init__(self, init_hp, init_mp, init_attack, init_defence, class_name):
        self.init_hp = init_hp
        self.init_mp = init_mp
        self.init_attack = init_attack
        self.init_defence = init_defence
        self.class_name = class_name
        self.spells = []

    def add_spell(self, spell):
        self.spells.append(spell)

    def init_character(self, character):
        character.class_name = self.class_name
        character.hp = self.init_hp
        character.max_hp = self.init_hp
        character.mp = self.init_mp
        character.max_mp = self.init_mp
        character.base_attack = self.init_attack
        character.base_defence = self.init_defence
        character.spells = self.spells

    def level_up(self, character):
        character.max_hp += self.init_hp
        character.max_mp += self.init_mp
        character.base_attack += self.init_attack
        character.base_defence += self.init_defence



