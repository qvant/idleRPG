
MAX_MESSAGES_FROM_USER = 3


class Message:
    def __init__(self, telegram_id, telegram_nickname, message):
        self.telegram_id = telegram_id
        self.telegram_nickname = telegram_nickname
        self.message = message
        self.id = None


class MessageList:
    def __init__(self, db):
        self.messages = {}
        self.messages_by_id = {}
        self.db = db

    def add_message(self, telegram_id, telegram_nickname, message, msg_id=None, supress_limit_check=False):
        msg = Message(telegram_id=telegram_id, telegram_nickname=telegram_nickname, message=message)
        if msg_id is None:
            self.db.save_message(msg)
        else:
            msg.id = msg_id
        if telegram_id in self.messages.keys():
            if not supress_limit_check and len(self.messages[telegram_id]) >= MAX_MESSAGES_FROM_USER:
                raise ValueError("Too many messages from user {0}".format(telegram_id))
            self.messages[telegram_id].append(msg)
        else:
            self.messages[telegram_id] = [msg]
        self.messages_by_id[msg.id] = msg

    def read_message(self, id_msg):
        msg = self.messages_by_id.get(id_msg)
        print(msg)
        print(id_msg)
        if msg is not None:
            self.db.save_message(msg)
            self.messages[msg.telegram_id].remove(msg)
            del self.messages_by_id[id_msg]

    def get_message(self):
        for i in self.messages_by_id:
            return self.messages_by_id[i]
        return None

    def load(self):
        self.db.load_messages(self)

    def get_message_number(self):
        return len(self.messages_by_id)
