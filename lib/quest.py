import random


class Quest:
    quest_verbs = []
    quest_adjective = []
    quest_nouns = []
    quest_max_target = None

    def __init__(self, owner):
        self.verb = self.quest_verbs[round(random.random() * len(self.quest_verbs)) - 1]
        self.adjective = self.quest_adjectives[round(random.random() * len(self.quest_adjectives)) - 1]
        self.noun = self.quest_nouns[round(random.random() * len(self.quest_nouns)) - 1]
        self.number = round(random.random() * self.quest_max_target) + 1
        self.owner = owner
        self.owner.set_quest(self)

    @classmethod
    def set_verbs(cls, verbs):
        cls.quest_verbs = verbs

    @classmethod
    def set_adjectives(cls, adjectives):
        cls.quest_adjectives = adjectives

    @classmethod
    def set_nouns(cls, nouns):
        cls.quest_nouns = nouns

    @classmethod
    def set_numbers(cls, numbers):
        cls.quest_max_target = len(numbers)

    def __str__(self):
        if self.owner.locale is None:
            return "{0} {1} {2} {3}".format(self.verb, self.number, self.adjective,
                                            self.noun)
        else:
            return "{0} {1} {2} {3}".format(self.owner.trans.get_message(self.verb, self.owner.locale),
                                            self.number,
                                            self.owner.trans.get_message(self.adjective, self.owner.locale),
                                            self.owner.trans.get_message(self.noun, self.owner.locale))
