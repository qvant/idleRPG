global class_list
global class_list_text
global ai_list


def set_class_list(cl, locales):
    global class_list
    global class_list_text
    class_list_text = {}
    class_list = cl
    for i in cl:
        class_list_text[i.class_name] = {}
        for j in locales:
            class_list_text[i.class_name][j] = locales[j].get_message(i.class_name)


def set_ai_list(cl):
    global ai_list
    ai_list = cl


def get_class_names():
    global class_list_text
    cl = []
    for i in class_list_text:
        cl.append(i)
    return cl


def get_class_list():
    global class_list
    return class_list


def get_class(name):
    global class_list
    for i in class_list:
        if i.class_name == name:
            return i
    return None


def get_ai():
    global ai_list
    return ai_list[0]
