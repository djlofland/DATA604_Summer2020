# ------------------------------------------------------------------------------------------------------------
class Actions:
    BUY_CANDY = 'BUY_CANDY'
    COLLECT_REWARD = 'COLLECT_REWARD'
    DONATE_ANIMAL = 'DONATE_ANIMAL'
    FEED_ANIMAL = 'FEED_ANIMAL'
    FREE_CRATE = 'FREE_CRATE'
    MERGE_CANDY = 'MERGE_CANDY'
    SPIN_WHEEL = 'SPIN_WHEEL'
    SWAP_ANIMALS = 'SWAP_ANIMALS'


# ------------------------------------------------------------------------------------------------------------
class Animal:
    TYPE_ID = 'Animal_ID'
    FAMILY = 'Family'
    ID = 'id'
    LEVEL = 'Level'
    LEVEL_UNLOCKED = 'Level_Unlocked'
    RARITY = 'Rarity'
    REVENUE = 'Revenue'
    SET_ID = 'Set_ID'
    SET_NAME = 'Set_Name'
    STATUS = 'active'
    TREATS_EARNED = 'Treats_Earned'
    
    
# ------------------------------------------------------------------------------------------------------------
class AnimalState:
    ACTIVE = 1
    INVENTORIED = 2
    DONATED = 3
    ALL = 4


# ------------------------------------------------------------------------------------------------------------
class Candy:
    ID = 'id'
    ID_1 = 'id_1'
    ID_2 = 'id_2'
    LEVEL = 'Level'
    COST = 'Candy_Cost'


# ------------------------------------------------------------------------------------------------------------
class Column:
    ANIMAL_ID = 'Animal_ID'
    ANIMAL_ID_1 = 'Animal_ID_1'
    ANIMAL_ID_2 = 'Animal_ID_2'
    ANIMAL_ID_3 = 'Animal_ID_3'
    ANIMAL_ID_4 = 'Animal_ID_4'
    ANIMAL_ID_5 = 'Animal_ID_5'
    ANIMAL_NAME = 'Animal_Name'
    ANIMAL_SET_ID = 'Animal_Set_ID'
    ANIMAL_SOCKETS = 'Animal_Sockets'
    CANDY_COST = 'Candy_Cost'
    CANDY_COST_MAX = 'Candy_Cost_Max'
    CANDY_COST_MIN = 'Candy_Cost_Min'
    CANDY_LEVEL = 'Candy_Level'
    CANDY_LEVEL_MAX = 'Candy_Level_Max'
    CANDY_LEVEL_MIN = 'Candy_Level_Min'
    CANDY_MERGE_MAX = 'Candy_Merge_Max'
    CANDY_SLOT_ID = 'Candy_Slot_ID'
    CANDY_SLOTS = 'Candy_Slots'
    COST = 'Cost'
    CUMULATIVE = 'Cumulative'
    CURR_LETTERS = 'Curr_Letters'
    CURR_NAME = 'Curr_Name'
    CURR_NUMBER = 'Curr_Number'
    CURR_VALUE = 'Curr_Value'
    CURRENCY = 'Currency'
    CURRENCY_SOFT = 'Currency_Soft'
    EGG_COUNT = 'Egg_Count'
    EGG_ID = 'Egg_ID'
    EGG_NAME = 'Egg_Name'
    FAMILY = 'Family'
    GOAL = 'Goal'
    LEVEL_UNLOCKED = 'Level_Unlocked'
    LUR_EGG_ID = 'LUR_Egg_ID'
    LUR_SOFT = 'LUR_Soft'
    PLAYER_LEVEL = 'Player_Level'
    RARITY = 'Rarity'
    RARITY_1 = 'Rarity_1'
    RARITY_2 = 'Rarity_2'
    RARITY_3 = 'Rarity_3'
    RARITY_4 = 'Rarity_4'
    RARITY_5 = 'Rarity_5'
    REVENUE = 'Revenue'
    REWARD_ID = 'Reward_ID'
    RTP_TARGET_ANIMALS = 'RTP_Target_Animals'
    RTP_TARGET_REVENUE = 'RTP_Target_Revenue'
    RTP_TARGET_STARS = 'RTP_Target_Stars'
    SET_ID = 'Set_ID'
    SET_NAME = 'Set_Name'
    SHOP_ID = 'Shop_ID'
    SOCKET_ID = 'Socket_ID'
    TREATS_EARNED = 'Treats_Earned'
    UNLOCK_LEVEL = 'Unlock_Level'
    XP_EARNED = 'XP_Earned'
    XP_REQ_NEXT = 'XP_Req_Next'
    XP_REQ_TOTAL = 'XP_Req_Total'


# ------------------------------------------------------------------------------------------------------------
class Currency:
    BALANCE = 'balance'
    EARNED = 'earned'
    MAX = 'max'
    PER_SECOND = 'per_second'
    SPENT = 'spent'


# ------------------------------------------------------------------------------------------------------------
class EggNames:
    RARITY_1_1 = 'Rarity_1_1'
    RARITY_1_2 = 'Rarity_1_2'
    RARITY_1_3 = 'Rarity_1_3'
    RARITY_1_4 = 'Rarity_1_4'
    RARITY_1_5 = 'Rarity_1_5'
    RARITY_2_2 = 'Rarity_2_2'
    RARITY_2_3 = 'Rarity_2_3'
    RARITY_2_4 = 'Rarity_2_4'
    RARITY_2_5 = 'Rarity_2_5'
    RARITY_3_3 = 'Rarity_3_3'
    RARITY_3_4 = 'Rarity_3_4'
    RARITY_3_5 = 'Rarity_3_5'
    RARITY_4_4 = 'Rarity_4_4'
    RARITY_4_5 = 'Rarity_4_5'
    RARITY_5_5 = 'Rarity_5_5'


# ------------------------------------------------------------------------------------------------------------
class Params:
    ACTION = 'action'
    ACTION_ID = 'action_id'
    ANIMAL_ID = 'animal_id'
    ANIMAL_LEVEL = 'animal_level'
    ANIMAL_RARITY = 'animal_rarity'
    CANDY_LEVEL = 'candy_level'
    DATA = 'data'
    EGG_ID = 'egg_id'
    ID = 'id'
    KEY = 'key'
    SPIN_COST = 'spin_cost'
    SPIN_WHEEL = 'spin_wheel'
    SWAP_ID_1 = 'swap_id_1'
    SWAP_ID_2 = 'swap_id_2'
    TIME_LIMIT = 'time_limit'
    TIMER = 'timer'


# ------------------------------------------------------------------------------------------------------------
class RANDOM:
    INTEGER = 1
    FLOAT = 2


# ------------------------------------------------------------------------------------------------------------
class Setting:
    ANIMAL_INVENTORY_CAP = 'animal_inventory_cap'
    CANDY_LEVEL_MAX = 'candy_level_max'
    EGG_UNLOCK_LEVEL = 'egg_unlock_level'
    FORTUNE_SPIN_COST_1 = 'fortune_spin_cost_1'
    FORTUNE_SPIN_COST_2 = 'fortune_spin_cost_2'
    FORTUNE_SPIN_REWARD_1 = 'fortune_spin_reward_1'
    FORTUNE_SPIN_REWARD_2 = 'fortune_spin_reward_2'
    FORTUNE_SPIN_UNLOCK_1 = 'fortune_spin_unlock_1'
    FORTUNE_SPIN_UNLOCK_2 = 'fortune_spin_unlock_2'
    OFFLINE_REGEN_TIME_CAP = 'offline_regen_time_cap'
    RTP_TIME_MAX = 'rtp_time_max'
    RTP_TIME_MIN = 'rtp_time_min'
    SIM_FPS = 'sim_fps'
    SIM_MODE = 'sim_mode'
    SNAPSHOT_TIME = 'snapshot_time'
    STARTING_ANIMALS = 'starting_animals'
    VIDEO_LIMIT = 'video_limit'
    VIDEO_LIMIT_RESET = 'video_limit_reset'


# ------------------------------------------------------------------------------------------------------------
class ShopCurrency:
    GEMS = 'Gems'
    IAP = 'IAP'
    OW = 'OW'
    VIDEO = 'Video'


# ------------------------------------------------------------------------------------------------------------
class Session:
    PER_DAY = 'sess_per_day'
    DURATION_MIN = 'sess_duration_min'
    DURATION_MAX = 'sess_duration_max'


# ------------------------------------------------------------------------------------------------------------
class State:
    ACTIONS = 'actions'
    ANIMAL_SOCKETS = 'data_animal_sockets'
    CANDY_SLOTS = 'data_candy_slots'
    CURRENT_EGG_ID = 'egg_id'
    CURRENT_EGG_PROGRESS = 'egg_progress'
    CURRENT_SESS_ONLINE = 'session_online'
    CURRENT_SESS_OFFLINE = 'session_offline'
    EGGS_UNLOCKED = 'eggs_unlocked'
    FREE_CRATE_NUMBER = 'free_crate_num'
    FREE_CRATE_TIMER = 'free_crate_timer'


# ------------------------------------------------------------------------------------------------------------
class Track:
    ACTION_COUNT = 'action_count'
    ANIMAL_IDS = 'animal_ids'
    ANIMALS_EARNED = 'animals_earned'
    BUY_CANDY = 'buy_candy'
    DONATE_ANIMAL = 'donate_animal'
    EGG_COMPLETE = 'egg_complete'
    FEED_ANIMAL = 'feed_animal'
    FREE_CRATE = 'free_crate'
    MERGE_CANDY = 'merge_candy'
    PLAYER_LEVEL_UP = 'player_level_up'
    PREMIUM_EARNED = 'premium_earned'
    PREMIUM_SPENT = 'premium_spent'
    SECONDARY_EARNED = 'secondary_earned'
    SECONDARY_SPENT = 'secondary_spent'
    SOFT_EARNED = 'soft_earned'
    SOFT_SPENT = 'soft_spent'
    SPIN_WHEEL_1 = 'spin_wheel_1'
    SPIN_WHEEL_2 = 'spin_wheel_2'
    SWAP_ANIMAL = 'swap_animal'
    VIDEO_WATCHED = 'video_watched'


# ------------------------------------------------------------------------------------------------------------
class Variants:
    VARIANT_LABEL = 'variant_label'
    SIM_COUNT = 'sim_count'
    SIM_CORES = 'sim_cores'
    SIM_LENGTH = 'sim_length'
    SIM_FPS = 'sim_fps'
    SIM_MODE = 'sim_mode'
    SIM_SNAPSHOT_TIME = 'sim_snapshot_time'
    
    SESS_PER_DAY = 'sess_per_day'
    SESS_DURATION_MIN = 'sess_duration_min'
    SESS_DURATION_MAX = 'sess_duration_max'

    DATA_ANIMALS = 'data_animals'
    DATA_ANIMAL_SETS = 'data_animal_sets'
    DATA_ANIMAL_SOCKETS = 'data_animal_sockets'
    DATA_CANDY_SLOTS = 'data_candy_slots'
    DATA_CANDIES = 'data_candies'
    DATA_CURRENCY_LABELS = 'data_currency_labels'
    DATA_EGGS = 'data_eggs'
    DATA_GACHA_EGGS = 'data_gacha_eggs'
    DATA_PLAYER_LEVELS = 'data_player_levels'
    DATA_RTP = 'data_rtp'
    DATA_SHOP = 'data_shop'
    
    PLAYER_BEHAVIOR_ACTION = 'player_behavior_action'
    PLAYER_BEHAVIOR_ANIMAL_SWAP = 'player_behavior_animal_swap'
    PLAYER_BEHAVIOR_BET = 'player_behavior_bet'
    PLAYER_BEHAVIOR_FEED_ORDER = 'player_behavior_feed_order'
    PLAYER_BEHAVIOR_OFFERWALL = 'player_behavior_offerwall'
    PLAYER_BEHAVIOR_SHOP = 'player_behavior_video'
    PLAYER_BEHAVIOR_VIDEO = 'player_behavior_video'
    
    PLAYER_TIME_GENERAL_MIN = 'player_time_general_max'
    PLAYER_TIME_GENERAL_MAX = 'player_time_general_min'
    
    ANIMAL_INVENTORY_CAP = 'animal_inventory_cap'
    CANDY_FEED_LEVEL_MAX = 'candy_feed_level_max'
    CANDY_LEVEL_MAX = 'candy_level_max'
    CURRENCY_PREMIUM_LABEL = 'currency_premium_label'
    CURRENCY_PREMIUM_START = 'currency_premium_start'
    CURRENCY_SECONDARY_LABEL = 'currency_secondary_label'
    CURRENCY_SECONDARY_START = 'currency_secondary_start'
    CURRENCY_SOFT_LABEL = 'currency_soft_label'
    CURRENCY_SOFT_START = 'currency_soft_start'
    EGG_UNLOCK_LEVEL = 'egg_unlock_level'
    FORTUNE_SPIN_COST_1 = 'fortune_spin_cost_1'
    FORTUNE_SPIN_COST_2 = 'fortune_spin_cost_2'
    FORTUNE_SPIN_REWARD_1 = 'fortune_spin_reward_1'
    FORTUNE_SPIN_REWARD_2 = 'fortune_spin_reward_2'
    FORTUNE_SPIN_UNLOCK_1 = 'fortune_spin_unlock_1'
    FORTUNE_SPIN_UNLOCK_2 = 'fortune_spin_unlock_2'
    INITIAL_BALANCE = 'initial_balance'
    OFFLINE_REGEN_CAP = 'offline_regen_cap'
    RTP = 'data_rtp'
    RTP_TIME_MAX = 'rtp_time_min'
    RTP_TIME_MIN = 'rtp_time_max'
    STARTING_ANIMAL = 'starting_animal'
    VIDEO_LIMIT = 'video_limit'
    VIDEO_LIMIT_RESET = 'video_limit_reset'


# ------------------------------------------------------------------------------------------------------------
class Video:
    NEVER = 0
    ALWAYS = 1
    RANDOM = 2
    EXPERT = 3


# ------------------------------------------------------------------------------------------------------------
class Wheel:
    ONE = 1
    TWO = 2
