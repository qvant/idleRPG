import datetime
import os
import psutil
from .messages import *


class Server:
    def __init__(self):
        self.startup = datetime.datetime.now().replace(microsecond=0)
        self.players = []
        self.sys_commands_proceed = 0
        self.user_commands_proceed = 0
        self.admin_commands_proceed = 0
        self.turn = 0
        self.is_shutdown = False
        self.memory_after_turn_1 = None
        self.memory_after_turn_max_hist = None
        self.memory_after_turn_last = None
        self.history_length = None
        self.feedback = None
        self._trans = None

    @property
    def uptime(self):
        return datetime.datetime.now().replace(microsecond=0) - self.startup

    def inc_turns(self):
        if self.turn == 1:
            self.memory_after_turn_1 = self.get_memory_usage()
        if self.turn == self.history_length:
            self.memory_after_turn_max_hist = self.get_memory_usage()
        self.memory_after_turn_last = self.get_memory_usage()
        self.turn += 1

    def set_translator(self, locales):
        self._trans = locales

    def inc_sys_cmd(self, cmd):
        self.sys_commands_proceed += cmd

    def inc_user_cmd(self, cmd):
        self.user_commands_proceed += cmd

    def inc_admin_cmd(self, cmd):
        self.admin_commands_proceed += cmd

    def set_players(self, players):
        self.players = players

    def set_hist_len(self, history_length):
        self.history_length = history_length

    def set_feedback(self, feedback):
        self.feedback = feedback

    def shutdown(self):
        self.is_shutdown = True

    @staticmethod
    def get_memory_usage():
        process = psutil.Process(os.getpid())
        return round(process.memory_full_info().rss / 1024 ** 2, 2)

    @staticmethod
    def get_memory_percent():
        process = psutil.Process(os.getpid())
        return round(process.memory_percent("rss"), 2)

    @staticmethod
    def get_cpu_times():
        process = psutil.Process(os.getpid())
        return str(process.cpu_times())

    @staticmethod
    def get_cpu_percent():
        process = psutil.Process(os.getpid())
        return str(process.cpu_percent())

    def translate(self, code):
        res = self._trans.get_message(M_SERVER_UPTIME, code).format(self.startup, self.uptime) + chr(10)
        res += self._trans.get_message(M_SERVER_CHARACTERS, code).format(len(self.players)) + chr(10)
        res += self._trans.get_message(M_SERVER_TURNS_PASSED, code).format(self.turn) + chr(10)
        res += self._trans.get_message(M_SERVER_FEEDBACK_MESSAGES, code).format(self.feedback.get_message_number()) + chr(10)
        res += self._trans.get_message(M_SERVER_CMD_PROCEED, code).\
            format(self.sys_commands_proceed, self.user_commands_proceed, self.admin_commands_proceed) + chr(10)
        res += chr(10)
        res += self._trans.get_message(M_SERVER_MEMORY_TOTAL, code).format(self.get_memory_usage(), self.get_memory_percent())
        res += chr(10)
        if self.memory_after_turn_last is not None:
            res += self._trans.get_message(M_SERVER_MEMORY_LAST_TURN, code).format(self.memory_after_turn_last)
            res += chr(10)
        if self.memory_after_turn_max_hist is not None:
            res += self._trans.get_message(M_SERVER_MEMORY_STAB, code).format(self.memory_after_turn_max_hist)
            res += chr(10)
        if self.memory_after_turn_1 is not None:
            res += self._trans.get_message(M_SERVER_MEMORY_FIRST_TURN, code).format(self.memory_after_turn_1)
            res += chr(10)
        res += self._trans.get_message(M_SERVER_CPU_TIMES, code).format(self.get_cpu_times())
        res += chr(10)
        res += self._trans.get_message(M_SERVER_CPU_PERCENT, code).format(self.get_cpu_percent())
        res += chr(10)
        if self.is_shutdown:
            res += self._trans.get_message(M_SERVER_SHUTTING_DOWN, code)
        else:
            res += self._trans.get_message(M_SERVER_RUNNING, code)
        return res
