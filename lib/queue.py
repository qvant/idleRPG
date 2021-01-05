import json
import datetime
import pika
from .consts import QUEUE_NAME_INIT, QUEUE_NAME_DICT, QUEUE_NAME_CMD, CMD_CREATE_CHARACTER, CMD_DELETE_CHARACTER, \
    QUEUE_NAME_RESPONSES, CMD_GET_CHARACTER_STATUS, LOG_QUEUE
from .dictionary import get_class_names, get_class, get_ai
from .character import Character
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
        if not self.enabled:
            return
        self.host = config.queue_host
        self.port = config.queue_port
        self.queue = None
        self.channel = None

    def renew(self, config):
        self.__init__(config, reload=True)

    def listen(self, player_list, db):
        if not self.enabled:
            return
        msg_proceed = 0
        start_time = datetime.datetime.now()
        class_list = get_class_names()
        self.queue = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
        self.channel = self.queue.channel()
        self.channel.queue_declare(queue=QUEUE_NAME_INIT)
        self.channel.queue_declare(queue=QUEUE_NAME_DICT, durable=True)
        for method_frame, properties, body in self.channel.consume(QUEUE_NAME_INIT, inactivity_timeout=1):
            # if not timeout
            if method_frame is not None:
                self.logger.info("Received message {0}, delivery tag {1} in queue".format(body,
                                                                                          method_frame.delivery_tag,
                                                                                          QUEUE_NAME_INIT))
                response = json.dumps(class_list)
                self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_DICT, body=response)
                self.logger.info("For class list request with  delivery tag {0} sent responce ".format(
                    method_frame.delivery_tag, response))
                # Acknowledge the message
                self.channel.basic_ack(method_frame.delivery_tag)
                self.logger.info("Message with delivery tag {0} acknowledged".format(method_frame.delivery_tag))
                msg_proceed += 1
            else:
                # empty channel
                break
            # Escape out of the loop after N messages
            if method_frame.delivery_tag == QUEUE_INIT_BATCH:
                break
        self.logger.info("Processing init bot queue done")
        self.channel.cancel()
        self.channel.queue_declare(queue=QUEUE_NAME_DICT, durable=True)
        for method_frame, properties, body in self.channel.consume(QUEUE_NAME_CMD, inactivity_timeout=1):

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
                    self.get_character_status_handler (msg, player_list, method_frame.delivery_tag)
                else:
                    self.logger.error("Message with command type {0} not supported".format(cmd))
                # Acknowledge the message
                self.channel.basic_ack(method_frame.delivery_tag)
                self.logger.info("Message with delivery tag {0} acknowledged".format(method_frame.delivery_tag))
                msg_proceed += 1
            else:
                break
        self.channel.close()
        self.queue.close()
        end_time = datetime.datetime.now()
        self.logger.info("Queue processing done, started at: {0}, ended at: {1}, {2} messages proceed".format(
                start_time, end_time, msg_proceed))

    def create_character_handler(self, cmd, db, class_list, player_list, delivery_tag):
        char_name = cmd.get("name")
        char_class = cmd.get("class")
        telegram_id = cmd.get("user_id")
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
                    result = 'Name is already taken'
                    code = QUEUE_STATUS_NAME_TAKEN
                    break
                elif telegram_id is not None and i.telegram_id == telegram_id:
                    result = 'User ' + str(telegram_id) + " already have character"
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
                result = "{} {} was created".format(new_character.class_name.capitalize(),
                                                    new_character.name)
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
        self.logger.info("Character deletion for user {0} started".format(telegram_id))
        code = None
        result = ''
        if telegram_id is None:
            code = QUEUE_STATUS_TLG_ID_EMPTY
            result = 'Telegram_id is empty'
        else:
            for i in range(len(player_list)):
                if player_list[i].telegram_id == telegram_id:
                    result = "{} {} (level {}) was deleted".format(player_list[i].class_name.capitalize(),
                                                                   player_list[i].name, player_list[i].level)
                    db.delete_character(player_list[i])
                    del player_list[i]
                    code = QUEUE_STATUS_OK
                    break
        if code is None:
            code = QUEUE_STATUS_CHARACTER_NOT_EXISTS
            result = "Character not found for user {0}".format(telegram_id)
        resp = {"code": code, "message": result, "user_id": telegram_id}
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))

    def get_character_status_handler(self, cmd, player_list, delivery_tag):
        print("try to find character")
        telegram_id = cmd.get("user_id")
        char_info = ''
        if telegram_id is None:
            result = 'telegram_id is empty'
            code = QUEUE_STATUS_TLG_ID_EMPTY
        else:
            for i in range(len(player_list)):
                if player_list[i].telegram_id == telegram_id:
                    char_info = str(player_list[i])
                    code = QUEUE_STATUS_OK
                    result = "Success"
                    break
            if len(char_info) == 0:
                char_info = "User {0} have no character".format(telegram_id)
                result = "Success"
                code = QUEUE_STATUS_OK
        resp = {"code": code, "message": result, "user_id": telegram_id, "char_info": char_info,
                "cmd_type": CMD_GET_CHARACTER_STATUS}
        self.channel.basic_publish(exchange='', routing_key=QUEUE_NAME_RESPONSES, body=json.dumps(resp))
        self.logger.info("For cmd with delivery tat {0} sent response {1} in queue {2}".format(delivery_tag, resp,
                                                                                               QUEUE_NAME_RESPONSES))