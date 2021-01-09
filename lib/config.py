import codecs
import datetime
import json
from .consts import *
from .utility import get_logger
from .security import is_password_encrypted, encrypt_password, decrypt_password


class Config:
    def __init__(self, file, reload=False):
        f = file
        fp = codecs.open(f, 'r', "utf-8")
        config = json.load(fp)
        if not reload:
            self.logger = get_logger(LOG_CONFIG, is_system=True)
        self.logger.info("Read settings from {0}".format(file))
        self.file_path = file
        self.old_file_path = file
        self.turn_time = config.get(CONFIG_PARAM_TURN_TIME)
        self.log_level = config.get(CONFIG_PARAM_LOG_LEVEL)
        self.logger.setLevel(self.log_level)
        self.max_turns = config.get(CONFIG_PARAM_MAX_TURNS)
        self.server_name = config.get(CONFIG_PARAM_SERVER_NAME)
        self.halt_on_game_errors = config.get(CONFIG_PARAM_HALT_ON_GAME_ERRORS)
        self.halt_on_persist_errors = config.get(CONFIG_PARAM_HALT_ON_PERSIST_ERRORS)
        self.halt_on_queue_errors = config.get(CONFIG_PARAM_HALT_ON_QUEUE_ERRORS)
        self.queue_enabled = config.get(CONFIG_PARAM_QUEUE_ENABLED)
        self.queue_host = config.get(CONFIG_PARAM_QUEUE_HOST)
        self.queue_port = config.get(CONFIG_PARAM_QUEUE_PORT)
        self.queue_user = config.get(CONFIG_PARAM_QUEUE_USER)
        self.queue_password_read = config.get(CONFIG_PARAM_QUEUE_PASSWORD)
        self.queue_batch_size = config.get(CONFIG_PARAM_QUEUE_BATCH_SIZE)
        self.char_batch_size = config.get(CONFIG_PARAM_CHAR_BATCH_SIZE)
        self.char_history_len = config.get(CONFIG_PARAM_CHAR_HISTORY_LEN)
        self.db_name = config.get(CONFIG_PARAM_DB_NAME)
        self.db_port = config.get(CONFIG_PARAM_DB_PORT)
        self.db_host = config.get(CONFIG_PARAM_DB_HOST)
        self.db_user = config.get(CONFIG_PARAM_DB_USER)
        self.db_password_read = config.get(CONFIG_PARAM_DB_PASSWORD)
        if config.get(CONFIG_PARAM_NEW_PATH) is not None:
            self.file_path = config.get(CONFIG_PARAM_NEW_PATH)
        self.reload_time = config.get(CONFIG_PARAM_CONFIG_RELOAD_TIME)
        self.next_reload = datetime.datetime.now()
        self.reloaded = False
        self.db_credential_changed = False

        if is_password_encrypted(self.db_password_read):
            self.logger.info("DB password encrypted, do nothing")
            self.db_password = decrypt_password(self.db_password_read, self.server_name, self.db_port)
        else:
            self.logger.info("DB password in plain text, start encrypt")
            password = encrypt_password(self.db_password_read, self.server_name, self.db_port)
            self._save_db_password(password)
            self.logger.info("DB password encrypted and save back in config")
            self.db_password = self.db_password_read

        if is_password_encrypted(self.queue_password_read):
            self.logger.info("MQ password encrypted, do nothing")
            self.queue_password = decrypt_password(self.queue_password_read, self.queue_host, self.queue_port)
        elif self.queue_password_read is not None:
            self.logger.info("MQ password in plain text, start encrypt")
            password = encrypt_password(self.queue_password_read, self.queue_host, self.queue_port)
            self._save_mq_password(password)
            self.logger.info("MQ password encrypted and save back in config")
            self.queue_password = self.queue_password_read
        else:
            self.logger.info("MQ password empty")
            self.queue_password = None

    def _save_db_password(self, password):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_DB_PASSWORD] = password
        json.dump(config, fp, indent=2)
        fp.close()

    def _save_mq_password(self, password):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_QUEUE_PASSWORD] = password
        json.dump(config, fp, indent=2)
        fp.close()

    def renew_if_needed(self):
        if datetime.datetime.now() >= self.next_reload:
            self.logger.debug("Time to reload settings")
            old_file_path = self.old_file_path
            old_db_password = self.db_password
            try:
                self.__init__(self.file_path, reload=True)
                self.reloaded = True
                if self.db_password != old_db_password:
                    self.logger.info("DB password changed, need to reconnect")
                    self.db_credential_changed = True
            except BaseException as exc:
                self.logger.critical("Can't reload settings from new path {0}, error {1}".format(self.file_path, exc))
                self.old_file_path = old_file_path
                self.file_path = old_file_path
        else:
            self.logger.debug("Too early to reload settings")

    def mark_reload_finish(self):
        self.reloaded = False
        self.db_credential_changed = False
