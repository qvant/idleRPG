class CharAI:
    def __init__(self, retreat_hp_threshold, retreat_mp_threshold, max_attack_instead_spell, health_potion_gold_percent,
                 mana_potion_gold_percent, max_hp_percent_to_heal):
        self.retreat_hp_threshold = retreat_hp_threshold
        self.retreat_mp_threshold = retreat_mp_threshold
        self.max_attack_instead_spell = max_attack_instead_spell
        self.health_potion_gold_percent = health_potion_gold_percent
        self.mana_potion_gold_percent = mana_potion_gold_percent
        self.max_hp_percent_to_heal = max_hp_percent_to_heal
