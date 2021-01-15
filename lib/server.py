import datetime


class Server:
    def __init__(self):
        self.startup = datetime.datetime.now()
        self.players = []
        self.sys_commands_proceed = 0
        self.user_commands_proceed = 0
        self.turn = 0
        self.is_shutdown = False

    @property
    def uptime(self):
        return datetime.datetime.now() - self.startup

    def inc_turns(self):
        self.turn += 1

    def inc_sys_cmd(self, cmd):
        self.sys_commands_proceed += cmd

    def inc_user_cmd(self, cmd):
        self.user_commands_proceed += cmd

    def set_players(self, players):
        self.players = players

    def shutdown(self):
        self.is_shutdown = True

    def __str__(self):
        res = "Server started at {0} (uptime {1} second).".format(self.startup, self.uptime) + chr(10)
        res += "Now it runs with {0} characters".format(len(self.players)) + chr(10)
        res += "{0} turns passed".format(self.turn) + chr(10)
        res += "Was processed {0} system and {1} user commands".format(self.sys_commands_proceed,
                                                                       self.user_commands_proceed) + chr(10)
        if self.is_shutdown:
            res += "Server is shutting down now."
        else:
            res += "Server is running."
        return res
