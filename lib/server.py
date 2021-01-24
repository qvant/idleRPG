import datetime
import os
import psutil


class Server:
    def __init__(self):
        self.startup = datetime.datetime.now()
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

    @property
    def uptime(self):
        return datetime.datetime.now() - self.startup

    def inc_turns(self):
        if self.turn == 1:
            self.memory_after_turn_1 = self.get_memory_usage()
        if self.turn == self.history_length:
            self.memory_after_turn_max_hist = self.get_memory_usage()
        self.memory_after_turn_last = self.get_memory_usage()
        self.turn += 1

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

    def __str__(self):
        res = "Server started at {0} (uptime {1} second).".format(self.startup, self.uptime) + chr(10)
        res += "Now it runs with {0} characters".format(len(self.players)) + chr(10)
        res += "{0} turns passed".format(self.turn) + chr(10)
        res += "Was processed {0} system, {1} user and {2} admin commands".\
            format(self.sys_commands_proceed, self.user_commands_proceed, self.admin_commands_proceed) + chr(10)
        res += chr(10)
        res += "Used memory: {0} mb, {1} % from total".format(self.get_memory_usage(), self.get_memory_percent())
        res += chr(10)
        if self.memory_after_turn_last is not None:
            res += "After last turn was used: {0}".format(self.memory_after_turn_last)
            res += chr(10)
        if self.memory_after_turn_max_hist is not None:
            res += "After stabilizing was used: {0}".format(self.memory_after_turn_max_hist)
            res += chr(10)
        if self.memory_after_turn_1 is not None:
            res += "After turn 1 was used: {0}".format(self.memory_after_turn_1)
            res += chr(10)
        res += "CPU times: {0}".format(self.get_cpu_times())
        res += chr(10)
        res += "CPU percent {0}".format(self.get_cpu_percent())
        res += chr(10)
        if self.is_shutdown:
            res += "Server is shutting down now."
        else:
            res += "Server is running."
        return res
