import argparse
import codecs
import datetime
import json
import random
import time

from lib.ability import AbilityType
from lib.ai import CharAI
from lib.char_classes import CharClass
from lib.character import Character
from lib.config import Config
from lib.consts import *
from lib.dictionary import set_class_list, set_ai_list
from lib.effect import EffectType
from lib.feedback import MessageList
from lib.item import Item
from lib.l18n import Translator
from lib.quest import Quest
from lib.monster import MonsterType
from lib.persist import Persist
from lib.queue import QueueListener
from lib.server import Server
from lib.spell import Spell
from lib.utility import check_chance, get_logger

global player_list
global class_list
global monster_list
global db
global feedback
global config
global start_mode
global weapon_list
global armor_list
global app_log
global game_log
global bot_queue
global server
global trans


def init():
    global player_list
    global monster_list
    global class_list
    global db
    global feedback
    global config
    global start_mode
    global weapon_list
    global armor_list
    global app_log
    global game_log
    global bot_queue
    global server
    global trans
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

    server = Server()

    app_log = get_logger(LOG_MAIN_APP, config.log_level, True)
    try:
        game_log = get_logger(LOG_GAME, config.log_level)

        db = Persist(config)
        db.check_version()

        feedback = MessageList(db=db)

        bot_queue = QueueListener(config)

        Character.set_logger(config)
        Character.set_history_length(config)
        trans = Translator()
        Character.set_translator(trans)

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
            if "spells" in class_list_j[i]:
                for j in class_list_j[i]["spells"]:
                    is_positive = j.get("is_positive")
                    if is_positive is None:
                        is_positive = False
                    temp_effect = j.get("effect")
                    effect = None
                    if temp_effect is not None:
                        effect = EffectType(name=j["name"], is_positive=temp_effect["is_positive"],
                                            attack=temp_effect.get("attack"), defence=temp_effect.get("defence"),
                                            damage_per_turn=temp_effect.get("damage_per_turn"),
                                            heal_per_turn=temp_effect.get("heal_per_turn"),
                                            duration=temp_effect["duration"],
                                            level_scale_modifier=temp_effect.get("level_scale_modifier"),
                                            can_stack=temp_effect.get("can_stack"),
                                            die_at=temp_effect.get("die_at"),
                                            attack_percent=temp_effect.get("attack_percent"),
                                            defence_percent=temp_effect.get("defence_percent"),
                                            )
                    temp_spell = Spell(name=j["name"], cost=j["cost"], min_damage=j["min_damage"],
                                       max_damage=j["max_damage"], is_positive=is_positive, effect=effect)

                    temp_class.add_spell(temp_spell)
            if "abilities" in class_list_j[i]:
                for j in class_list_j[i]["abilities"]:
                    temp_effect = j.get("effect")
                    effect = None
                    if temp_effect is not None:
                        effect = EffectType(name=j["name"], is_positive=temp_effect["is_positive"],
                                            attack=temp_effect.get("attack"), defence=temp_effect.get("defence"),
                                            damage_per_turn=temp_effect.get("damage_per_turn"),
                                            heal_per_turn=temp_effect.get("heal_per_turn"),
                                            duration=temp_effect["duration"],
                                            level_scale_modifier=temp_effect.get("level_scale_modifier"),
                                            can_stack=temp_effect.get("can_stack"),
                                            die_at=temp_effect.get("die_at"),
                                            attack_percent=temp_effect.get("attack_percent"),
                                            defence_percent=temp_effect.get("defence_percent"),
                                            )
                    temp_ability = AbilityType(name=j["name"], event=j["event"], action=j["action"],
                                               description_code=j["description_code"], chance=j["chance"],
                                               effect=effect)

                    temp_class.add_ability(temp_ability)
            class_list.append(temp_class)
        set_class_list(class_list, trans.locales)
        server.set_translator(trans)

        f = "db//ai.json"
        fp = codecs.open(f, 'r', "utf-8")
        ai_list_j = json.load(fp)
        ai_list = []
        for i in ai_list_j:
            ai_list.append(CharAI(retreat_hp_threshold=ai_list_j[i]["retreat_hp_threshold"],
                                  retreat_mp_threshold=ai_list_j[i]["retreat_mp_threshold"],
                                  mana_potion_gold_percent=ai_list_j[i]["mana_potion_gold_percent"],
                                  health_potion_gold_percent=ai_list_j[i]["health_potion_gold_percent"],
                                  max_attack_instead_spell=ai_list_j[i]["max_attack_instead_spell"],
                                  max_hp_percent_to_heal=ai_list_j[i]["max_hp_percent_to_heal"],
                                  ))
        set_ai_list(ai_list)

        f = "db//quests.json"
        fp = codecs.open(f, 'r', "utf-8")
        q_list_j = json.load(fp)
        quest_verbs = q_list_j["verb"]
        # TODO: Заменить константой или настройкой
        quest_numbers = q_list_j["numbers"]
        quest_adjective = q_list_j["adjective"]
        quest_noun = q_list_j["noun"]

        Quest.set_adjectives(quest_adjective)
        Quest.set_nouns(quest_noun)
        Quest.set_numbers(quest_numbers)
        Quest.set_verbs(quest_verbs)

        f = "db//monsters.json"
        fp = codecs.open(f, 'r', "utf-8")
        m_list_j = json.load(fp)
        monster_list = []
        for i in m_list_j:
            monster_list.append(MonsterType(name=i, attack=m_list_j[i]["attack"], defence=m_list_j[i]["defence"],
                                            hp=m_list_j[i]["hp"],
                                            exp=m_list_j[i]["exp"],
                                            level_multiplier=m_list_j[i]["level_multiplier"],
                                            level=m_list_j[i]["level"],
                                            gold=m_list_j[i]["gold"], ))

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
            feedback.load()
    except BaseException as err:
        app_log.critical(err)
        raise


def chose_action(player):
    if player.action == ACTION_NONE:
        if player.hp_percent <= player.ai.retreat_hp_threshold:
            player.set_action(ACTION_RETREAT)
        elif player.mp_percent <= player.ai.retreat_mp_threshold:
            player.set_action(ACTION_RETREAT)
        else:
            player.set_action(ACTION_QUEST)
            if player.quest is None:
                Quest(player)


def make_monster(player):
    i = -1
    while i < 0:
        i = round(random.random() * len(monster_list) - 1)
        if monster_list[i].level > player.level:
            i = -1
    if check_chance(MONSTER_AMPLIFY_CHANCE) and player.level > MONSTER_AMPLIFY_MIN_LEVEL:
        lvl = (round(random.random() * max(player.level - 1, 2)))
    else:
        lvl = 0
    monster = monster_list[i].create_monster(lvl, player)

    return monster


def do_action(player):
    player.wait()
    player.apply_effects()
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
    global feedback
    global config
    global bot_queue
    global server
    global trans
    try:
        server.set_players(player_list)
        server.set_hist_len(config.char_history_len)
        server.set_feedback(feedback)
        bot_queue.set_translator(trans)
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
                    bot_queue.listen(server, player_list, db, feedback)
            server.inc_turns()
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
                app_log.warning("Turn {4} takes too long: started at: {0}, ended at: {1}, should ended: {2} "
                                "should take:{3}".format(turn_start_time, turn_end_time, turn_end_time_r, config.turn_time,
                                                         server.turn))
            else:
                app_log.info("Turn {4} ended: started at: {0}, ended at: {1}, should ended: {2} should take:{3}".format(
                    turn_start_time, turn_end_time, turn_end_time_r, config.turn_time, server.turn))
                if config.turn_time > 0:
                    if config.queue_interval_on_sleep is not None:
                        while datetime.datetime.now() <= turn_end_time_r:
                            app_log.debug("Sleep in main cycle")
                            # when sleep, check and process message queue
                            time.sleep(min((turn_end_time_r - datetime.datetime.now()).seconds,
                                           config.queue_interval_on_sleep))
                            app_log.debug("Wake up to process queue")
                            bot_queue.listen(server, player_list, db, feedback)
                    else:
                        app_log.debug("Sleep in main cycle")
                        time.sleep((turn_end_time_r - turn_end_time).seconds)
            if server.turn >= config.max_turns > 0 or server.is_shutdown:
                break
            bot_queue.listen(server, player_list, db, feedback)
    except BaseException as err:
        app_log.critical(err)
        raise


if __name__ == '__main__':
    init()
    main()
