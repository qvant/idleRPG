global class_list
global ai_list


def set_class_list(cl):
    global class_list
    class_list = cl


def set_ai_list(cl):
    global ai_list
    ai_list = cl


def get_class_names():
    global class_list
    cl = []
    for i in class_list:
        cl.append(i.class_name)
    return cl


def get_class(name):
    global class_list
    for i in class_list:
        if i.class_name == name:
            return i
    return None


def get_ai():
    global ai_list
    return ai_list[0]
