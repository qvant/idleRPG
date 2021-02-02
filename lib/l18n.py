import codecs
import json
import os
import re

DEFAULT_LOCALE = 'english'

FORM_NOMINATIVE = 1
FORM_GENITIVE = 2  # Родительный падеж
FORM_ACCUSATIVE = 3  # Винительный падеж
FORM_ABLATIVE = 4  # Творительный падеж
FORM_MULTIPLE = 5  # Множественное число
FORM_FEW = 6  # Творительный падеж
FORM_SINGLE = 7  # Творительный падеж
FORM_FEMININE = 8  # женский род
FORM_FEMININE_A = 9  # женский род творительный падеж
FORM_FEMININE_AC = 10  # женский род винительный падеж
FORM_NEUTER = 11  # срединий род
FORM_NEUTER_A = 12  # средний род творительный падеж
FORM_NEUTER_AC = 13  # средний род винительный падеж
FORM_DEFAULT = 14

MS_NUMBER_SINGLE_RULE = "NUMBER_SINGLE_RULE"
MS_NUMBER_FEW_RULE = "NUMBER_FEW_RULE"
MS_NUMBER_MANY_RULE = "NUMBER_MANY_RULE"

# TODO: replace for gettext
class L18n:
    # Class for translation messages to chosen language
    def __init__(self):
        self.locale = ''
        self.encoding = None
        self.msg_map = []
        self.alternative = None
        self.single_rule = None
        self.few_rule = None

    def set_encoding(self, encoding):
        self.encoding = encoding

    def set_locale(self, name):
        self.locale = name
        f = "l18n//" + name + ".lng"
        fp = codecs.open(f, 'r', "utf-8")
        self.msg_map = json.load(fp)
        self.single_rule = re.compile(self.msg_map.get(MS_NUMBER_SINGLE_RULE))
        self.few_rule = re.compile(self.msg_map.get(MS_NUMBER_FEW_RULE))
        if self.locale != DEFAULT_LOCALE:
            self.alternative = L18n()
            self.alternative.set_locale(DEFAULT_LOCALE)

    def get_message(self, msg_type, word_form=None):
        if msg_type in self.msg_map.keys():
            msg = self.msg_map[msg_type]
            if isinstance(msg, dict):
                # TODO rewrite
                if word_form == FORM_NOMINATIVE or word_form == FORM_DEFAULT or word_form == FORM_SINGLE:
                    msg = msg.get("nominative")
                elif word_form == FORM_GENITIVE:
                    msg = msg.get("genitive")
                elif word_form == FORM_ABLATIVE:
                    msg = msg.get("ablative")
                elif word_form == FORM_ACCUSATIVE:
                    msg = msg.get("accusative")
                elif word_form == FORM_MULTIPLE:
                    msg = msg.get("many")
                elif word_form == FORM_FEW:
                    msg = msg.get("few")
                elif word_form == FORM_FEMININE:
                    msg = msg.get("feminine")
                elif word_form == FORM_FEMININE_A:
                    msg = msg.get("feminine_a")
                elif word_form == FORM_FEMININE_AC:
                    msg = msg.get("feminine_ac")
                elif word_form == FORM_NEUTER:
                    msg = msg.get("neuter")
                elif word_form == FORM_NEUTER_A:
                    msg = msg.get("neuter_a")
                elif word_form == FORM_NEUTER_AC:
                    msg = msg.get("neuter_ac")
                if len(msg) == 0:
                    raise KeyError(
                        "Can't find message {} in locale {} (default locale {} with form {} )".
                            format(msg_type, self.locale, DEFAULT_LOCALE, word_form))
        elif self.locale != DEFAULT_LOCALE:
            msg = self.alternative.get_message(msg_type, word_form)
        else:
            raise KeyError("Can't find message {} in locale {} (default locale {})".format(msg_type, self.locale,
                                                                                           DEFAULT_LOCALE))
        if self.encoding is not None:
            msg = str(msg.encode(self.encoding))
        return msg

    def get_dependent_form(self, msg_type):
        if msg_type in self.msg_map.keys():
            msg = self.msg_map[msg_type]
            if isinstance(msg, dict):
                word_form = msg.get("adjective_form")
                if word_form == "nominative":
                    res = FORM_NOMINATIVE
                elif word_form == "feminine":
                    res = FORM_FEMININE
                elif word_form == "neuter":
                    res = FORM_NEUTER
                elif word_form == "many":
                    res = FORM_MULTIPLE
                elif word_form == "few":
                    res = FORM_FEW
                else:
                    res = FORM_NOMINATIVE
            else:
                res = FORM_NOMINATIVE
        elif self.locale != DEFAULT_LOCALE:
            res = self.alternative.get_dependent_form(msg_type)
        else:
            raise KeyError("Can't find message {} in locale {} (default locale {})".format(msg_type, self.locale,
                                                                                           DEFAULT_LOCALE))
        return res


class Translator:
    def __init__(self):
        self.locales = {}
        for dirpath, dirnames, filenames in os.walk("l18n"):
            for lang_file in filenames:
                self.locales[lang_file[:2]] = L18n()
                self.locales[lang_file[:2]].set_locale(lang_file[:-4])
        self.default_translator = self.locales["en"]
        self.active_translator = self.default_translator

    def set_locale(self, code):
        if code in self.locales.keys():
            self.active_translator = self.locales[code]
        else:
            self.active_translator = self.default_translator

    def get_message(self, msg_type, code, is_nominative=False, is_genitive=False, is_ablative=False, is_accusative=False,
                    connected_number=None, connected_word=None):
        if code in self.locales.keys():
            locale = self.locales[code]
        else:
            locale = self.default_translator
        word_form = FORM_DEFAULT
        if connected_word is not None:
            word_form = locale.get_dependent_form(connected_word)
            if word_form == FORM_FEMININE and is_ablative:
                word_form = FORM_FEMININE_A
            if word_form == FORM_FEMININE and is_accusative:
                word_form = FORM_FEMININE_AC
            if word_form == FORM_NEUTER and is_ablative:
                word_form = FORM_NEUTER_A
            if word_form == FORM_NEUTER and is_accusative:
                word_form = FORM_NEUTER_AC
            if word_form == FORM_NOMINATIVE and is_ablative:
                word_form = FORM_ABLATIVE
            if word_form == FORM_NOMINATIVE and is_accusative:
                word_form = FORM_ACCUSATIVE
        elif is_nominative:
            word_form = FORM_NOMINATIVE
        elif is_genitive:
            word_form = FORM_GENITIVE
        elif is_ablative:
            word_form = FORM_ABLATIVE
        elif is_accusative:
            word_form = FORM_ACCUSATIVE
        elif connected_number is not None:
            if locale.single_rule.search(str(connected_number)):
                word_form = FORM_SINGLE
            elif locale.few_rule.search(str(connected_number)):
                word_form = FORM_FEW
            else:
                word_form = FORM_MULTIPLE
        return locale.get_message(msg_type, word_form)
