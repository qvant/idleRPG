from typing import Union

from .ai import CharAI
from .char_classes import CharClass
from .l18n import L18n

global class_list
global class_list_text
global ai_list


def set_class_list(cl: [CharClass], locales: [L18n]):
    global class_list
    global class_list_text
    class_list_text = {}
    class_list = cl
    for i in cl:
        class_list_text[i.class_name] = {}
        for j in locales:
            class_list_text[i.class_name][j] = locales[j].get_message(i.class_name)


def set_ai_list(cl: [CharAI]):
    global ai_list
    ai_list = cl


def get_class_names() -> [str]:
    global class_list_text
    cl = []
    for i in class_list_text:
        cl.append(i)
    return cl


def get_class_list() -> [str]:
    global class_list_text
    return class_list_text


def get_class(name: str) -> Union[CharClass, None]:
    global class_list
    for i in class_list:
        if i.class_name == name:
            return i
    return None


def get_ai() -> CharAI:
    global ai_list
    return ai_list[0]
