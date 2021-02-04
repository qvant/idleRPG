import datetime
import json

import pika
import sys

from .character import Character
from .consts import QUEUE_NAME_INIT, QUEUE_NAME_DICT, QUEUE_NAME_CMD, CMD_GET_CLASS_LIST, CMD_CREATE_CHARACTER, \
    CMD_DELETE_CHARACTER, QUEUE_NAME_RESPONSES, CMD_GET_CHARACTER_STATUS, CMD_GET_SERVER_STATS, \
    CMD_SERVER_SHUTDOWN_IMMEDIATE, CMD_SERVER_SHUTDOWN_NORMAL, LOG_QUEUE, CMD_SET_CLASS_LIST, CMD_SERVER_STATS, \
    CMD_SERVER_OK, CMD_FEEDBACK_RECEIVE, CMD_FEEDBACK, CMD_GET_FEEDBACK, CMD_SENT_FEEDBACK, CMD_CONFIRM_FEEDBACK,\
    CMD_SET_CLASS_DESCRIPTION
from .dictionary import get_class_list, get_class_names, get_class, get_ai
from .messages import *
from .utility import get_logger

QUEUE_INIT_BATCH = 10
QUEUE_STATUS_OK = 0
QUEUE_STATUS_ERROR = 500
QUEUE_STATUS_NAME_EMPTY = 501
QUEUE_STATUS_CLASS_EMPTY = 502
QUEUE_STATUS_CLASS_UNKNOWN = 503
QUEUE_STATUS_NAME_TAKEN = 504
QUEUE_STATUS_CHARACTER_EXISTS = 505
QUEUE_STATUS_TLG_ID_EMPTY = 506
QUEUE_STATUS_CHARACTER_NOT_EXISTS = 507


class QueueListener:
    def __init__(self, config, reload=False):
        self.enabled = config.queue_enabled
        if reload:
            self.logger.setLevel(config.log_level)
        else:
            self.logger = get_logger(LOG_QUEUE, config.log_level, is_system=True)
            self.trans = None
        if not self.enabled:
            return
        self.host = config.queue_host
        self.port = config.queue_port
        self.batch_size = config.queue_batch_size
        if reload and self.channel is not None:
            self.channel.close()
            self.queue.close()
        else:
            self.queue = None
            self.channel = None
        try:
            if config.queue_password is not None:
                cred = pika.credentials.PlainCredentials(config.queue_user, config.queue_password)
                self.queue = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=self.port, credentials=cred))
            else:
                self.queue = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
            self.channel = self.queue.channel()
            self.channel.queue_declare(queue=QUEUE_NAME_INIT)
            self.channel.queue_declare(queue=QUEUE_NAME_DICT, durable=True)
            self.channel.queue_declare(queue=QUEUE_NAME_CMD, durable=True)
            self.channel.queue_declare(queue=QUEUE_NAME_RESPONSES, durable=True)
        except pika.exceptions.AMQPError as exc:
            self.logger.critical(exc)
            self.enabled = False

    def renew(self, config):
        self.__init__(config, reload=True)

    def set_translator(self, trans):
        self.trans = trans

    def listen(self, server, player_list, db, feedback):
        self.listen_control(server)
        self.listen_cmd(server, player_list, db, feedback)

    def listen_control(self, server):
        if not self.enabled:
            return
        try:
            msg_proceed = 0
            start_time = datetime.datetime.now()
            class_list = get_class_list()
            msg_cnt = 0
            for method_frame, properties, body in self.channel.consume(QUEUE_NAME_INIT, inactivity_timeout=0.01):
                # if not timeout
                if method_frame is not None:
                    self.logger.info("Received message {0}, delivery tag {1} in queue".format(body,
                                                                                              method_frame.delivery_tag,
                                                                                              QUEUE_NAME_INIT))
                    msg = json.loads(body)
                    cmd = msg.get("cmd_type")
                    if cmd == CMD_GET_CLASS_LIST:
                        response = {"class_list": class_list, "cmd_type": CMD_SET_CLASS_LIST}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        for i in class_list:
                            for j in server.get_locales():

                                response = {"class_name": i, "cmd_type": CMD_SET_CLASS_DESCRIPTION,
                                            "class_description": server.trans_message(i + "_description", j),
                                            "class_stats": get_class(i).translate(server._trans, j),
                                            "locale": j
                                            }
                                response = json.dumps(response)
                                self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.logger.info("For class list request with delivery tag {0} sent response".format(
                            method_frame.delivery_tag, response))
                    elif cmd == CMD_GET_SERVER_STATS:
                        locale = msg.get("locale")
                        response = {"server_info": server.translate(locale), "cmd_type": CMD_SERVER_STATS,
                                    "user_id": msg.get("user_id")}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.logger.info("For server stats request with delivery tag {0} sent response {1}".format(
                            method_frame.delivery_tag, response))
                    elif cmd == CMD_SERVER_SHUTDOWN_IMMEDIATE:
                        locale = msg.get("locale")
                        response = {"cmd_type": CMD_SERVER_OK,
                                    "user_id": msg.get("user_id"),
                                    "message": server.trans_message(M_SERVER_SHUTTING_DOWN, locale)}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.channel.cancel()
                        self.logger.info("Received immediate shutdown command, finish work")
                        self.channel.basic_ack(method_frame.delivery_tag)
                        self.logger.info("Message with delivery tag {0} acknowledged".format(method_frame.delivery_tag))
                        sys.exit(0)
                    elif cmd == CMD_SERVER_SHUTDOWN_NORMAL:
                        locale = msg.get("locale")
                        response = {"cmd_type": CMD_SERVER_OK,
                                    "user_id": msg.get("user_id"),
                                    "message": server.trans_message(M_SERVER_SHUTTING_DOWN, locale)}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.channel.cancel()
                        self.logger.info("Received normal shutdown command, will finish work on the end of turn")
                        server.shutdown()
                    elif cmd == CMD_GET_FEEDBACK:
                        feed = server.feedback.get_message()
                        if feed is not None:
                            response = {"cmd_type": CMD_SENT_FEEDBACK,
                                        "user_id": msg.get("user_id"), "message": feed.message,
                                        "user_sent_id": feed.telegram_id, "user_sent_nick": feed.telegram_nickname,
                                        "message_id": feed.id}
                        else:
                            locale = msg.get("locale")
                            response = {"cmd_type": CMD_SERVER_OK,
                                        "user_id": msg.get("user_id"),
                                        "message": server.trans_message(M_NO_FEEDBACK, locale)}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.logger.info("Received send feedback message, sent response")
                    elif cmd == CMD_CONFIRM_FEEDBACK:
                        locale = msg.get("locale")
                        feed_id = msg.get("message_id")
                        telegram_id = msg.get("user_id")
                        server.feedback.read_message(feed_id, telegram_id)
                        response = {"cmd_type": CMD_SERVER_OK,
                                    "user_id": msg.get("user_id"),
                                    "message": server.trans_message(M_FEEDBACK_CONFIRMED, locale).format(feed_id)}
                        response = json.dumps(response)
                        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                        self.logger.info("Received send feedback message, sent response")
                    else:
                        self.logger.error("Message {0} has unknown command type {1}".format(msg, cmd))
                    # Acknowledge the message
                    self.channel.basic_ack(method_frame.delivery_tag)
                    self.logger.info("Message with delivery tag {0} acknowledged".format(method_frame.delivery_tag))
                    msg_proceed += 1
                    msg_cnt += 1
                    if msg_cnt >= self.batch_size > 0:
                        self.logger.info("Proceed {0} messages in queue {1}, interrupt".format(msg_cnt,
                                                                                               QUEUE_NAME_DICT))
                        break
                else:
                    self.logger.info("No more messages in queue {0}".format(QUEUE_NAME_DICT))
                    break
            self.logger.info("Processing init bot queue done")
            end_time = datetime.datetime.now()
            server.inc_sys_cmd(msg_proceed)
            self.logger.info("Queue processing done, started at: {0}, ended at: {1}, {2} messages proceed".format(
                start_time, end_time, msg_proceed))
            self.channel.cancel()
        except pika.exceptions.AMQPError as exc:
            self.logger.critical(exc)
            self.enabled = False

    def listen_cmd(self, server, player_list, db, feedback):
        if not self.enabled:
            return
        try:
            start_time = datetime.datetime.now()
            class_list = get_class_names()
            msg_cnt = 0
            user_msg_proceed = 0
            admin_msg_proceed = 0
            for method_frame, properties, body in self.channel.consume(QUEUE_NAME_CMD, inactivity_timeout=0.01):

                # if not timeout
                if method_frame is not None:
                    self.logger.info("Received message {0}, delivery tag {1} in queue".format(body,
                                                                                              method_frame.delivery_tag,
                                                                                              QUEUE_NAME_CMD))
                    msg = json.loads(body)
                    cmd = msg.get("cmd_type")
                    if cmd == CMD_CREATE_CHARACTER:
                        self.create_character_handler(msg, db, class_list, player_list, method_frame.delivery_tag)
                    elif cmd == CMD_DELETE_CHARACTER:
                        self.delete_character_handler(msg, db, player_list, method_frame.delivery_tag)
                    elif cmd == CMD_GET_CHARACTER_STATUS:
                        self.get_character_status_handler(msg, db, player_list, method_frame.delivery_tag)
                    elif cmd == CMD_FEEDBACK:
                        self.feedback_message_handler(msg, db, feedback, method_frame.delivery_tag)
                    else:
                        self.logger.error("Message with command type {0} not supported".format(cmd))
                    # Acknowledge the message
                    self.channel.basic_ack(method_frame.delivery_tag)
                    self.logger.info("Message with delivery tag {0} acknowledged".format(method_frame.delivery_tag))
                    if msg.get("sent_by_admin"):
                        admin_msg_proceed += 1
                    else:
                        user_msg_proceed += 1
                    msg_cnt += 1
                    if msg_cnt >= self.batch_size > 0:
                        self.logger.info("Proceed {0} messages in queue {1}, interrupt".format(msg_cnt,
                                                                                               QUEUE_NAME_CMD))
                        break
                else:
                    self.logger.info("No more messages in queue {0}".format(QUEUE_NAME_CMD))
                    break
            self.channel.cancel()
            end_time = datetime.datetime.now()
            server.inc_user_cmd(user_msg_proceed)
            server.inc_admin_cmd(admin_msg_proceed)
            self.logger.info("Queue processing done, started at: {0}, ended at: {1}, {2} messages proceed".format(
                start_time, end_time, admin_msg_proceed + user_msg_proceed))
        except pika.exceptions.AMQPError as exc:
            self.logger.critical(exc)
            self.enabled = False

    def create_character_handler(self, cmd, db, class_list, player_list, delivery_tag):
        char_name = cmd.get("name")
        char_class = cmd.get("class")
        telegram_id = cmd.get("user_id")
        locale = cmd.get("locale")
        self.logger.info("Character creation for user {0} started".format(telegram_id))
        char_id = None
        result = ''
        if char_name is None or len(char_name) == 0:
            result = 'Name is empty'
            code = QUEUE_STATUS_NAME_EMPTY
        elif char_class is None or len(char_class) == 0:
            result = 'Class is empty'
            code = QUEUE_STATUS_CLASS_EMPTY
        elif char_class not in class_list:
            result = 'Class {0) is unknown'.format(char_class)
            code = QUEUE_STATUS_CLASS_UNKNOWN
        else:
            for i in player_list:
                if i.name == char_name:
                    result = self.trans.get_message(M_NAME_IS_ALREADY_TAKEN, locale)
                    code = QUEUE_STATUS_NAME_TAKEN
                    break
                elif telegram_id is not None and i.telegram_id == telegram_id:
                    result = self.trans.get_message(M_USER_ALREADY_HAS_CHARACTER, locale).format(telegram_id)
                    code = QUEUE_STATUS_CHARACTER_EXISTS
                    break
        if len(result) == 0:
            new_character = Character(char_name, get_class(char_class), telegram_id)
            new_character.set_ai(get_ai())
            new_character.need_save = True
            self.logger.debug("try to save character")
            db.save_character(character=new_character)
            if db.was_error:
                result = "Unknown error"
                code = QUEUE_STATUS_ERROR
            else:
                player_list.append(new_character)
                char_id = new_character.id
                result = self.trans.get_message(M_CHARACTER_WAS_CREATED, locale).\
                    format(self.trans.get_message(new_character.class_name, locale).capitalize(), new_character.name)
                db.save_character(new_character)
                db.commit()
                code = QUEUE_STATUS_OK

        resp = {"code": code, "message": result}
        if code == 0 and char_id is not None:
            resp["persist_id"] = char_id
            resp["user_id"] = new_character.telegram_id
            resp["class"] = new_character.class_name
            resp["name"] = new_character.name
        else:
            resp["user_id"] = telegram_id
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))

    def delete_character_handler(self, cmd, db, player_list, delivery_tag):
        telegram_id = cmd.get("user_id")
        locale = cmd.get("locale")
        self.logger.info("Character deletion for user {0} started".format(telegram_id))
        code = None
        result = ''
        if telegram_id is None:
            code = QUEUE_STATUS_TLG_ID_EMPTY
            result = 'Telegram_id is empty'
        else:
            for i in range(len(player_list)):
                if player_list[i].telegram_id == telegram_id:
                    result = self.trans.get_message(M_CHARACTER_WAS_DELETED, locale).\
                        format(self.trans.get_message(player_list[i].class_name, locale).capitalize(),
                               player_list[i].name, player_list[i].level)
                    db.delete_character(player_list[i])
                    db.commit()
                    del player_list[i]
                    code = QUEUE_STATUS_OK
                    break
        if code is None:
            code = QUEUE_STATUS_CHARACTER_NOT_EXISTS
            result = self.trans.get_message(M_USER_HAS_NO_CHARACTER, locale).format(telegram_id)
        resp = {"code": code, "message": result, "user_id": telegram_id}
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))

    def get_character_status_handler(self, cmd, db, player_list, delivery_tag):
        telegram_id = cmd.get("user_id")
        locale = cmd.get("locale")
        self.logger.info("try to find character with telegram id {0}".format(telegram_id))
        char_info = ''
        if telegram_id is None:
            result = 'telegram_id is empty'
            code = QUEUE_STATUS_TLG_ID_EMPTY
        else:
            for i in range(len(player_list)):
                if player_list[i].telegram_id == telegram_id:
                    player_list[i].set_locale(cmd.get("locale"))
                    char_info = str(player_list[i])
                    if player_list[i].need_save:
                        db.commit()
                    code = QUEUE_STATUS_OK
                    result = "Success"
                    break
            if len(char_info) == 0:
                char_info = self.trans.get_message(M_USER_HAS_NO_CHARACTER, locale).format(telegram_id)
                result = "Success"
                code = QUEUE_STATUS_OK
        resp = {"code": code, "message": result, "user_id": telegram_id, "char_info": char_info,
                "cmd_type": CMD_GET_CHARACTER_STATUS}
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))

    def feedback_message_handler(self, cmd, db, feedback, delivery_tag):
        telegram_id = cmd.get("user_id")
        telegram_nickname = cmd.get("user_name")
        message = cmd.get("message")
        if telegram_id is None:
            result = 'telegram_id is empty'
            code = QUEUE_STATUS_TLG_ID_EMPTY
        else:
            try:
                feedback.add_message(telegram_id=telegram_id, telegram_nickname=telegram_nickname, message=message)
                result = "Success"
                code = QUEUE_STATUS_OK
            except ValueError as err:
                result = str(err)
                code = QUEUE_STATUS_ERROR
        resp = {"code": code, "message": result, "user_id": telegram_id,
                "cmd_type": CMD_FEEDBACK_RECEIVE}
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))

