ACTION_NONE = 0
ACTION_RETREAT = 1
ACTION_QUEST = 2
ACTION_DEAD = 3
ACTION_SHOP = 4

EXP_FOR_RETREAT_RATIO = 0.1

RESURRECT_TIMER = 2

MONSTER_CHANCE_ON_QUEST = 0.25
MONSTER_CHANCE_ON_RETREAT = 0.25
MONSTER_AMPLIFY_CHANCE = 0.3
MONSTER_AMPLIFY_MIN_LEVEL = 3

HEALTH_POTION_PRICE = 10
MANA_POTION_PRICE = 12

ACTIONS = [ACTION_NONE, ACTION_RETREAT, ACTION_QUEST, ACTION_DEAD, ACTION_SHOP]
ACTION_NAMES = ["Unknown", "Retreating", "Questing", "Dead", "Do shopping"]

CMD_CREATE_CHARACTER = "create_character"
CMD_DELETE_CHARACTER = "delete_character"
CMD_GET_CHARACTER_STATUS = "get_character_status"

CONFIG_PARAM_TURN_TIME = "TURN_TIME"
CONFIG_PARAM_LOG_LEVEL = "LOG_LEVEL"
CONFIG_PARAM_CONFIG_RELOAD_TIME = "CONFIG_RELOAD_TIME"
CONFIG_PARAM_MAX_TURNS = "DEBUG_MAX_TURNS"
CONFIG_PARAM_HALT_ON_GAME_ERRORS = "DEBUG_HALT_ON_GAME_ERROR"
CONFIG_PARAM_HALT_ON_PERSIST_ERRORS = "DEBUG_HALT_ON_PERSIST_ERROR"
CONFIG_PARAM_NEW_PATH = "CONFIG_PATH"
CONFIG_PARAM_SERVER_NAME = "SERVER_NAME"
CONFIG_PARAM_SECRET_CONST = "rokada216"
CONFIG_PARAM_DB_PORT = "DB_PORT"
CONFIG_PARAM_DB_NAME = "DB_NAME"
CONFIG_PARAM_DB_HOST = "DB_HOST"
CONFIG_PARAM_DB_USER = "DB_USER"
CONFIG_PARAM_DB_PASSWORD = "DB_PASSWORD"
CONFIG_PARAM_QUEUE_ENABLED = "QUEUE_ENABLED"
CONFIG_PARAM_QUEUE_HOST = "QUEUE_HOST"
CONFIG_PARAM_QUEUE_PORT = "QUEUE_PORT"

QUEUE_NAME_INIT = "InitQueue"
QUEUE_NAME_DICT = "DictionaryQueue"
QUEUE_NAME_CMD = "CommandQueue"
QUEUE_NAME_RESPONSES = "ResponsesQueue"


LOG_TRACE = 10
LOG_DEBUG = 30
LOG_INFO = 50
LOG_WARN = 80
LOG_ERROR = 90
LOG_CRITICAL = 100

LOG_CONFIG = "Config"
LOG_CHARACTER = "Character"
LOG_GAME = "Game"
LOG_MAIN_APP = "Core"
LOG_PERSIST = "Storage"
LOG_QUEUE = "Message_queue"

START_CLEAR = 1
START_RESUME = 2

ITEM_SLOT_WEAPON = 1
ITEM_SLOT_ARMOR = 2