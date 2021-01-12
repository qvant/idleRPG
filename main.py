from lib.character import Character
import argparse
import codecs
import json
import random
import copy
import datetime
import time
from lib.char_classes import CharClass
from lib.spell import Spell
from lib.monster import Monster
from lib.ai import CharAI
from lib.consts import *
from lib.config import Config
from lib.dictionary import set_class_list, set_ai_list
from lib.item import Item
from lib.persist import Persist
from lib.queue import QueueListener
from lib.utility import check_chance, get_logger

global player_list
global class_list
global monster_list
global quest_verbs
global quest_numbers
global quest_adjective
global quest_noun
global db
global config
global start_mode
global weapon_list
global armor_list
global app_log
global game_log
global bot_queue


def init():
    global player_list
    global monster_list
    global class_list
    global quest_verbs
    global quest_numbers
    global quest_adjective
    global quest_noun
    global db
    global config
    global start_mode
    global weapon_list
    global armor_list
    global app_log
    global game_log
    global bot_queue
    player_list = []

    parser = argparse.ArgumentParser(description='Idle RPG server.')
    parser.add_argument("--clear", '-c', help="Restart with empty character base", action="store_true", default=False)
    parser.add_argument("--config", '-cfg', help="Path to config file", action="store", default="cfg//main.json")
    args = parser.parse_args()
    if args.clear:
        start_mode = START_CLEAR
    else:
        start_mode = START_RESUME

    config = Config(args.config)

    app_log = get_logger(LOG_MAIN_APP, config.log_level, True)
    game_log = get_logger(LOG_GAME, config.log_level)

    db = Persist(config)

    bot_queue = QueueListener(config)

    Character.set_logger(config)
    Character.set_history_length(config)

    f = "db//classes.json"
    fp = codecs.open(f, 'r', "utf-8")
    class_list_j = json.load(fp)
    class_list = []
    for i in class_list_j:
        temp_class = CharClass(init_hp=class_list_j[i]["init_hp"],
                               init_mp=class_list_j[i]["init_mp"],
                               init_attack=class_list_j[i]["init_attack"],
                               init_defence=class_list_j[i]["init_defence"],
                               class_name=class_list_j[i]["Name"])
        if "spells" in class_list_j[i].keys():
            for j in class_list_j[i]["spells"]:
                temp_spell = Spell(name=j["name"], cost=j["cost"], min_damage=j["min_damage"],
                                   max_damage=j["max_damage"])
                temp_class.add_spell(temp_spell)
        class_list.append(temp_class)
    set_class_list(class_list)

    f = "db//ai.json"
    fp = codecs.open(f, 'r', "utf-8")
    ai_list_j = json.load(fp)
    ai_list = []
    for i in ai_list_j:
        ai_list.append(CharAI(retreat_hp_threshold=ai_list_j[i]["retreat_hp_threshold"],
                              retreat_mp_threshold=ai_list_j[i]["retreat_mp_threshold"],
                              mana_potion_gold_percent=ai_list_j[i]["mana_potion_gold_percent"],
                              health_potion_gold_percent=ai_list_j[i]["health_potion_gold_percent"],
                              max_attack_instead_spell=ai_list_j[i]["max_attack_instead_spell"]))
    set_ai_list(ai_list)

    f = "db//quests.json"
    fp = codecs.open(f, 'r', "utf-8")
    q_list_j = json.load(fp)
    quest_verbs = q_list_j["verb"]
    quest_numbers = q_list_j["numbers"]
    quest_adjective = q_list_j["adjective"]
    quest_noun = q_list_j["noun"]

    f = "db//monsters.json"
    fp = codecs.open(f, 'r', "utf-8")
    m_list_j = json.load(fp)
    monster_list = []
    for i in m_list_j:
        monster_list.append(Monster(name=i, attack=m_list_j[i]["attack"], defence=m_list_j[i]["defence"],
                                    hp=m_list_j[i]["hp"],
                                    exp=m_list_j[i]["exp"],
                                    level_multiplier=m_list_j[i]["level_multiplier"],
                                    level=m_list_j[i]["level"],
                                    gold=m_list_j[i]["gold"],))

    f = "db//weapons.json"
    fp = codecs.open(f, 'r', "utf-8")
    weapon_list = json.load(fp)
    Item.weapon_list = weapon_list

    f = "db//armor.json"
    fp = codecs.open(f, 'r', "utf-8")
    armor_list = json.load(fp)
    Item.armor_list = armor_list

    if start_mode == START_CLEAR:
        db.clear_all()
    else:
        player_list = db.load_all_characters(class_list, ai_list[0])


def make_quest():
    global quest_verbs
    global quest_numbers
    global quest_adjective
    global quest_noun
    ind_v = round(random.random() * len(quest_verbs)) - 1
    ind_n = round(random.random() * len(quest_numbers)) - 1
    ind_a = round(random.random() * len(quest_adjective)) - 1
    ind_noun = round(random.random() * len(quest_noun)) - 1
    return "{0} {1} {2} {3}".format(quest_verbs[ind_v], quest_numbers[ind_n], quest_adjective[ind_a],
                                    quest_noun[ind_noun])


def chose_action(player):
    if player.action == ACTION_NONE:
        if player.hp_percent <= player.ai.retreat_hp_threshold:
            player.set_action(ACTION_RETREAT)
        elif player.mp_percent <= player.ai.retreat_mp_threshold:
            player.set_action(ACTION_RETREAT)
        else:
            player.set_action(ACTION_QUEST)
            player.set_quest(make_quest())


def make_monster(player):
    i = -1
    while i < 0:
        i = round(random.random() * len(monster_list) - 1)
        if monster_list[i].level > player.level:
            i = -1
    monster = copy.deepcopy(monster_list[i])
    if check_chance(MONSTER_AMPLIFY_CHANCE) and player.level > MONSTER_AMPLIFY_MIN_LEVEL:
        monster.apply_level(round(random.random() * max(player.level - 1, 2)))
    return monster


def do_action(player):
    player.wait()
    if player.ready:
        if player.dead:
            player.resurrect()
        if player.enemy is not None:
            player.fight()
        elif player.action == ACTION_QUEST:
            if player.enemy is None:
                if check_chance(MONSTER_CHANCE_ON_QUEST):
                    monster = make_monster(player)
                    player.set_enemy(monster)
            player.do_quest()
        elif player.action == ACTION_SHOP:
            player.do_shopping()
        # retreat
        elif player.town_distance > 0:
            player.move(-1)
            if player.town_distance > 0:
                if check_chance(MONSTER_CHANCE_ON_RETREAT):
                    monster = make_monster(player)
                    player.set_enemy(monster)
        elif player.town_distance == 0:
            player.rest()
            player.set_action(ACTION_SHOP)
        else:
            player.set_action(ACTION_NONE)


def main():
    global db
    global config
    global bot_queue
    turn_number = 0
    while True:
        turn_start_time = datetime.datetime.now()
        turn_end_time_r = turn_start_time + datetime.timedelta(seconds=config.turn_time)
        player_cnt = 0
        for i in player_list:
            try:
                chose_action(i)
                do_action(i)
            except BaseException as err:
                if config.halt_on_game_errors:
                    app_log.critical(err)
                    raise
                else:
                    app_log.error(err)
            db.save_character(character=i)
            game_log.debug(i)
            player_cnt += 1
            if player_cnt >= config.char_batch_size > 0:
                player_cnt = 0
                bot_queue.listen(player_list, db)
        turn_number += 1
        db.commit()
        config.renew_if_needed()
        if config.reloaded:
            app_log.setLevel(config.log_level)
            game_log.setLevel(config.log_level)
            config.mark_reload_finish()
            if config.db_credential_changed:
                db.renew(config)
            bot_queue.renew(config)
        elif db.was_error:
            db.renew(config)
        turn_end_time = datetime.datetime.now()
        if config.turn_time > 0 and turn_end_time > turn_end_time_r:
            app_log.warning("Turn {4} takes too long: started at: {0}, ended at: {1}, should ended: {2} should take:{3}".format(
                turn_start_time, turn_end_time, turn_end_time_r, config.turn_time, turn_number))
        else:
            app_log.info("Turn {4} ended: started at: {0}, ended at: {1}, should ended: {2} should take:{3}".format(
                turn_start_time, turn_end_time, turn_end_time_r, config.turn_time, turn_number))
            if config.turn_time > 0:
                if config.queue_interval_on_sleep is not None:
                    while datetime.datetime.now() <= turn_end_time_r:
                        app_log.debug("Sleep in main cycle")
                        # when sleep, check and process message queue
                        time.sleep(min((turn_end_time_r - datetime.datetime.now()).seconds,
                                       config.queue_interval_on_sleep))
                        app_log.debug("Wake up to process queue")
                        bot_queue.listen(player_list, db)
                else:
                    app_log.debug("Sleep in main cycle")
                    time.sleep((turn_end_time_r - turn_end_time).seconds)
        if turn_number >= config.max_turns > 0:
            break
        bot_queue.listen(player_list, db)


if __name__ == '__main__':
    import sys

    sys.path.append("..")
    init()
    main()
