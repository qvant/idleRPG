from .persist import Persist

MAX_MESSAGES_FROM_USER = 3


class Message:
    def __init__(self, telegram_id: int, telegram_nickname: str, message: str):
        self.telegram_id = telegram_id
        self.telegram_nickname = telegram_nickname
        self.message = message
        self.id = None


class MessageList:
    def __init__(self, db: Persist):
        self.messages = {}
        self.messages_by_id = {}
        self.db = db

    def add_message(self, telegram_id: int, telegram_nickname: str, message: str, msg_id: int = None,
                    suppress_limit_check: bool = False):
        msg = Message(telegram_id=telegram_id, telegram_nickname=telegram_nickname, message=message)
        if msg_id is None:
            self.db.save_message(msg)
        else:
            msg.id = msg_id
        if telegram_id in self.messages:
            if not suppress_limit_check and len(self.messages[telegram_id]) >= MAX_MESSAGES_FROM_USER:
                raise ValueError("Too many messages from user {0}".format(telegram_id))
            self.messages[telegram_id].append(msg)
        else:
            self.messages[telegram_id] = [msg]
        self.messages_by_id[msg.id] = msg

    def add_reply(self, user_id: int, message: str, msg_id: int):
        self.db.save_message_reply(message=message, message_id=msg_id, telegram_id=user_id)
        self.read_message(msg_id=msg_id, user_id=user_id)

    def read_message(self, msg_id: int, user_id: int):
        msg = self.messages_by_id.get(msg_id)
        if msg is not None:
            self.db.save_message(msg, user_id)
            self.messages[msg.telegram_id].remove(msg)
            del self.messages_by_id[msg_id]

    def get_message(self):
        for i in self.messages_by_id:
            return self.messages_by_id[i]
        return None

    def get_message_sender(self, msg_id):
        return self.messages_by_id[msg_id].telegram_id

    def load(self):
        self.db.load_messages(self)

    def get_message_number(self):
        return len(self.messages_by_id)
