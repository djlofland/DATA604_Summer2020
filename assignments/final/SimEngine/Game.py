import simpy
import random
import math

from functools import lru_cache

from SimEngine.SimOutput import *
from SimEngine.StringConstants import *
from SimEngine.UtilityFunctions import *


class Game:
    """Common base class for all SimEngine Games"""
    
    # -----------------------------------------------------------
    # STATIC PROPERTIES GO HERE (Shared by all player instances)
    is_logging_enabled = False
    
    # =============================================================================================================
    # SETUP and INITIALIZE Game
    # =============================================================================================================
    def __init__(self):
        """
        Game Constructor
        """
        random.seed(42)
        
        self.env = simpy.Environment()
        
        # ----- Time track -----
        self.day = 1
        self.session = 1  # track the current session number
        self.frame = 0  # hold current player simulation time (seconds)
        self.time_free_crate_reset = 0
        self.time_inapp = 0  # hold current player simulation time (seconds)
        self.time_real = 0
        self.time_session = 0
        self.time_video_reset = 0
        
        # ----- Economy Config Data loaded from Google Sheets -----
        self.data_animals = None
        self.data_animal_sockets = None
        self.data_candy_slots = None
        self.data_candies = None
        self.data_currency_labels = None
        self.data_eggs = None
        self.data_eggs_raw = None
        self.data_gacha_eggs = None
        self.data_player_levels = None
        self.data_rtp = None
        self.data_shop = None
        
        # ----- Simulation Output - will get dumped to CSV -----
        self.snapshot = None
        
        # ----- Player reference -----
        self.player = None
        
        # ----- Player settings (may differ based on variant) -----
        self.settings = {
            Setting.CANDY_LEVEL_MAX       : 0,
            Setting.EGG_UNLOCK_LEVEL      : 0,
            Setting.FORTUNE_SPIN_COST_1   : 0,
            Setting.FORTUNE_SPIN_COST_2   : 0,
            Setting.FORTUNE_SPIN_REWARD_1 : 0,
            Setting.FORTUNE_SPIN_REWARD_2 : 0,
            Setting.FORTUNE_SPIN_UNLOCK_1 : 0,
            Setting.FORTUNE_SPIN_UNLOCK_2 : 0,
            Setting.OFFLINE_REGEN_TIME_CAP: 0,
            Setting.RTP_TIME_MIN          : 0,
            Setting.RTP_TIME_MAX          : 0,
            Setting.SIM_FPS               : 4,
            Setting.SIM_MODE              : 1,
            Setting.SNAPSHOT_TIME         : 1,
            Setting.STARTING_ANIMALS      : None,
            Setting.VIDEO_LIMIT           : 10,
            Setting.VIDEO_LIMIT_RESET     : 86400,
        }
        
        # ----- Track Game State Data -----
        self.state = {
            State.ACTIONS             : [],  # Player Action queue
            State.ANIMAL_SOCKETS      : [],  # Animals in habitats earning $
            State.CANDY_SLOTS         : [],  # Candy's on board available for merging or feeding
            State.CURRENT_EGG_ID      : 0,  # Which egg is player working on completing
            State.CURRENT_EGG_PROGRESS: 0,  # Player progress on completing current egg
            State.FREE_CRATE_NUMBER   : 0,  # counter - increments with each free crate
            State.CURRENT_SESS_ONLINE : 0,  # current session duration
            State.CURRENT_SESS_OFFLINE: 0  # current offline durtion
        }
    
    # -------------------------------------------------------------------------------------------------------------
    def init_game(self, v_data):
        """Set the economy this player will use"""
        
        # Each player makes a copy of the original untouched master DataFrames (loaded from GoogleSheets)
        # Note: we convert each dataframe to a dictionary for performance
        
        # --- animals config
        self.data_animals = v_data[Variants.DATA_ANIMALS]
        self.data_animals = self.data_animals.to_dict(orient="records")
        self.data_animals = {(b[Column.ANIMAL_ID]): b for b in self.data_animals}
        
        # --- habitat slots for active animals in zoo
        self.data_animal_sockets = v_data[Variants.DATA_ANIMAL_SOCKETS]
        self.data_animal_sockets = self.data_animal_sockets.to_dict(orient="records")
        self.data_animal_sockets = {(b[Column.SOCKET_ID]): b for b in self.data_animal_sockets}
        
        # --- candy config
        self.data_candies = v_data[Variants.DATA_CANDIES]
        self.data_candies = self.data_candies.to_dict(orient="records")
        self.data_candies = {(b[Column.CANDY_LEVEL]): b for b in self.data_candies}
        
        # --- candy board for merging candies
        self.data_candy_slots = v_data[Variants.DATA_CANDY_SLOTS]
        self.data_candy_slots = self.data_candy_slots.to_dict(orient="records")
        self.data_candy_slots = {(b[Column.CANDY_SLOT_ID]): b for b in self.data_candy_slots}
        
        # --- names/labels for really big values
        self.data_currency_labels = v_data[Variants.DATA_CURRENCY_LABELS]
        self.data_currency_labels = self.data_currency_labels.to_dict(orient="records")
        self.data_currency_labels = {(b[Column.CURR_NUMBER]): b for b in self.data_currency_labels}
        
        # --- Egg Progress config
        # The data_eggs tab in Google is not laid out correct - need to reformat it
        self.data_eggs_raw = v_data[Variants.DATA_EGGS]
        self.data_eggs = {}
        
        egg_id = 1
        for _, row in self.data_eggs_raw.iterrows():
            for c in range(0, int(row[Column.EGG_COUNT])):
                self.data_eggs[egg_id] = {
                    Column.EGG_ID      : egg_id,
                    Column.PLAYER_LEVEL: row[Column.PLAYER_LEVEL],
                    Column.EGG_COUNT   : row[Column.EGG_COUNT],
                    Column.GOAL        : row[Column.GOAL],
                    Column.REWARD_ID   : row[Column.REWARD_ID],
                    Column.CUMULATIVE  : egg_id
                }
                
                egg_id += 1
        
        # --- Egg config - map egg_id to rules about what they contain
        self.data_gacha_eggs = v_data[Variants.DATA_GACHA_EGGS]
        self.data_gacha_eggs = self.data_gacha_eggs.to_dict(orient="records")
        self.data_gacha_eggs = {(b[Column.EGG_ID]): b for b in self.data_gacha_eggs}
        
        # --- Player config per player_level
        self.data_player_levels = v_data[Variants.DATA_PLAYER_LEVELS]
        self.data_player_levels = self.data_player_levels.to_dict(orient="records")
        self.data_player_levels = {(b[Column.PLAYER_LEVEL]): b for b in self.data_player_levels}
        
        # --- RTP (Return to Player) config for free crates
        self.data_rtp = v_data[Variants.DATA_RTP]
        self.data_rtp = self.data_rtp.to_dict(orient="records")
        self.data_rtp = {(b[Column.PLAYER_LEVEL]): b for b in self.data_rtp}
        
        # --- Shop Config
        self.data_shop = v_data[Variants.DATA_SHOP]
        self.data_shop = self.data_shop.to_dict(orient="records")
        self.data_shop = {(b[Column.SHOP_ID], b[Column.CURRENCY], b[Column.CURRENCY_SOFT]): b for b in self.data_shop}
        
        # Class to manage simulation output CSV
        self.snapshot = SimOutput(self)
        
        # Read settings/config from Variants Tab in GoogleSheet
        self.settings[Setting.ANIMAL_INVENTORY_CAP] = v_data[Variants.ANIMAL_INVENTORY_CAP]
        self.settings[Setting.CANDY_LEVEL_MAX] = v_data[Variants.CANDY_LEVEL_MAX]
        self.settings[Setting.EGG_UNLOCK_LEVEL] = v_data[Variants.EGG_UNLOCK_LEVEL]
        self.settings[Setting.FORTUNE_SPIN_UNLOCK_1] = v_data[Variants.FORTUNE_SPIN_UNLOCK_1]
        self.settings[Setting.FORTUNE_SPIN_COST_1] = v_data[Variants.FORTUNE_SPIN_COST_1]
        self.settings[Setting.FORTUNE_SPIN_REWARD_1] = v_data[Variants.FORTUNE_SPIN_REWARD_1]
        self.settings[Setting.FORTUNE_SPIN_UNLOCK_2] = v_data[Variants.FORTUNE_SPIN_UNLOCK_2]
        self.settings[Setting.FORTUNE_SPIN_COST_2] = v_data[Variants.FORTUNE_SPIN_COST_2]
        self.settings[Setting.FORTUNE_SPIN_REWARD_2] = v_data[Variants.FORTUNE_SPIN_REWARD_2]
        self.settings[Setting.OFFLINE_REGEN_TIME_CAP] = v_data[Variants.OFFLINE_REGEN_CAP]
        self.settings[Setting.RTP_TIME_MIN] = v_data[Variants.RTP_TIME_MIN]
        self.settings[Setting.RTP_TIME_MAX] = v_data[Variants.RTP_TIME_MAX]
        self.settings[Setting.STARTING_ANIMALS] = v_data[Variants.STARTING_ANIMAL].split(',')
        self.settings[Setting.VIDEO_LIMIT] = v_data[Variants.VIDEO_LIMIT]
        self.settings[Setting.VIDEO_LIMIT_RESET] = v_data[Variants.VIDEO_LIMIT_RESET]
        
        # Initial Free Crate timer in game status
        self.state[State.FREE_CRATE_TIMER] = self.get_rtp_timer()
    
    # -------------------------------------------------------------------------------------------------------------
    def set_player(self, player):
        """Create reference to the player instance"""
        self.player = player
        
        self.snapshot.init(player)
    
    # =============================================================================================================
    # ANIMAL Methods
    # =============================================================================================================
    @lru_cache()
    def get_animal_by_animal_id(self, animal_id):
        """Get animal details from config data
        
        Parameters:
            animal_id (Int): Animal_ID (every animal has an ID)
        Returns (Dict)"""
        if animal_id in self.data_animals:
            return self.data_animals[animal_id]
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_animal_set(self, animal_id):
        """Get animal set for the provided animal_id

        Parameters:
            animal_id (Int): Animal_ID (every animal has an ID)
        Returns (Int)"""
        if animal_id in self.data_animals:
            return self.data_animals[animal_id][Column.SET_ID]
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_unlocked_animals(self, player_level):
        """Get all unlocked animals based on player player_level
        
        Parameters:
            player_level (Int): Current player player_level
            
        Returns List of animal Dictionaries"""
        animals = []
        
        for animal_id, animal in self.data_animals.items():
            if animal[Column.LEVEL_UNLOCKED] <= player_level:
                animals.append(animal)
            else:
                break
        
        return animals
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animals_not_found(self, player_level):
        """Build list of all animals the player doesn't have yet but are unlocked

        Parameters:
            player_level (Int): Current player player_level

        Returns List of animal Dictionaries"""
        animals = []
        
        unlocked_animals = self.get_unlocked_animals(player_level)
        acquired_animals = self.player.get_acquired_animals()
        
        for animal in unlocked_animals:
            if animal[Animal.TYPE_ID] not in acquired_animals:
                animals.append(animal.copy())
        
        return animals
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animals_not_found_1_3(self, player_level):
        """Build list of all Rarity 1-3 animals the player doesn't have yet

        Parameters:
            player_level (Int): Current player player_level

        Returns List of animal Dictionaries"""
        unlocked_animals = self.get_animals_not_found(player_level)
        animals = []
        
        for animal in unlocked_animals:
            if animal[Animal.RARITY] <= 3:
                animals.append(animal)
        
        return animals
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animals_not_found_4_5(self, player_level):
        """Build list of all Rarity 4-5 animals the player doesn't have yet

        Parameters:
            player_level (Int): Current player player_level

        Returns List of animal Dictionaries"""
        unlocked_animals = self.get_animals_not_found(player_level)
        animals = []
        
        for animal in unlocked_animals:
            if animal[Animal.RARITY] >= 4:
                animals.append(animal)
        
        return animals
    
    # =============================================================================================================
    # ANIMAL SOCKET Methods
    # =============================================================================================================
    @lru_cache()
    def animal_socket_cap(self, player_level):
        """Return number of active animals player can have at their player_level

        Parameters:
            player_level (Int): Current player player_level

        Returns Int"""
        socket_cap = 0
        
        for idx, a in self.data_animal_sockets.items():
            if a[Column.UNLOCK_LEVEL] <= player_level:
                socket_cap = a[Column.SOCKET_ID]
            else:
                break
        
        return socket_cap
    
    # ------------------------------------------------------------------------------------------------------------
    def animal_socket_available(self):
        """Are there any open slots for an animal in the zoo?

        Returns Boolean"""
        if len(self.state[State.ANIMAL_SOCKETS]) < self.animal_socket_cap(self.player.level):
            return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def animal_socket_has(self, animal_id):
        """Is the Animal_ID currently active in an animal slot?

        Parameters:
            animal_id (Int): Animal Unique ID

        Returns Boolean"""
        return animal_id in self.state[State.ANIMAL_SOCKETS]
    
    # ------------------------------------------------------------------------------------------------------------
    def animal_socket_add(self, animal_id):
        """Attempt to add an animal to the zoo slot

        Parameters:
            animal_id (Int): Animal Unique ID

        Returns Boolean"""
        if self.animal_socket_available():
            
            if animal_id not in self.state[State.ANIMAL_SOCKETS]:
                self.state[State.ANIMAL_SOCKETS].append(animal_id)
                self.player.animal_inventory[animal_id][Animal.STATUS] = AnimalState.ACTIVE
                return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def animal_socket_remove(self, animal_id):
        """Attempt to remove an animal from the zoo slot

        Parameters:
            animal_id (Int): Animal Unique ID

        Returns Boolean"""
        if animal_id in self.state[State.ANIMAL_SOCKETS]:
            self.state[State.ANIMAL_SOCKETS].remove(animal_id)
            self.player.animal_inventory[animal_id][Animal.STATUS] = AnimalState.INVENTORIED
            
            return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def get_animal_socket_animals(self):
        """Get list of animal dictionary objects currently active in the Zoo

        Returns List"""
        animals = []
        
        for animal_id in self.state[State.ANIMAL_SOCKETS]:
            animals.append(self.player.get_animal_by_unique_id(animal_id))
        
        return animals
    
    # ============================================================================================================
    # CANDY Methods
    # ============================================================================================================
    @lru_cache()
    def candy_data(self, candy_level):
        """Return candy details for given candy player_level

        Parameters:
            candy_level (Int): Candy player_level (1...n)

        Returns Dictionary"""
        return self.data_candies[candy_level]
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_candy_cost(self, candy_level):
        """Return candy cost for the given candy player_level

        Parameters:
            candy_level (Int): Candy player_level (1...n)

        Returns Int"""
        return self.candy_data(candy_level)[Column.CANDY_COST]
    
    # ============================================================================================================
    # CANDY SLOT Methods
    # ============================================================================================================
    @lru_cache()
    def candy_slot_cap(self, player_level):
        """Return board size (candy slots) for merging candies

        Parameters:
            player_level (Int): Player player_level

        Returns Int"""
        slot_cap = 0
        
        for idx, c in self.data_candy_slots.items():
            if c[Column.UNLOCK_LEVEL] <= player_level:
                slot_cap = c[Column.CANDY_SLOTS]
            else:
                break
        
        return slot_cap
    
    # ------------------------------------------------------------------------------------------------------------
    def candy_slot_available(self):
        """Are there any open slots for buying candies?

        Returns Boolean"""
        if len(self.state[State.CANDY_SLOTS]) < self.candy_slot_cap(self.player.level):
            return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def candy_slot_add(self, candy_level):
        """Add a candy to the board

        Parameters:
            candy_level (Int): Candy player_level

        Returns Boolean"""
        if self.candy_slot_available():
            self.state[State.CANDY_SLOTS].append(candy_level)
            return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def candy_slot_remove(self, candy_level):
        """Remove a candy from the board

        Parameters:
            candy_level (Int): Candy player_level

        Returns Boolean"""
        if candy_level in self.state[State.CANDY_SLOTS]:
            self.state[State.CANDY_SLOTS].remove(candy_level)
            return True
        else:
            return False
    
    # ------------------------------------------------------------------------------------------------------------
    def get_candy_slot_candies(self):
        """Get list of all candy levels on board

        Returns List"""
        return self.state[State.CANDY_SLOTS]
    
    # ------------------------------------------------------------------------------------------------------------
    def get_candy_slot_unique(self):
        """Get a list of all unique candy levels (no duplicates) on board

        Returns List"""
        return list(set(self.state[State.CANDY_SLOTS]))
    
    # ------------------------------------------------------------------------------------------------------------
    def get_candy_count(self, candy_level):
        """Return the count of candies on board of given candy_level
        
        Parameters:
            candy_level (Int) - candy player_level to find
            
        Returns Int"""
        return len([1 for c in self.state[State.CANDY_SLOTS] if c == candy_level])
    
    # ============================================================================================================
    # EGGS
    # ============================================================================================================
    @lru_cache()
    def get_egg_data(self, egg_id):
        """Return Dictionary of Egg Config details for given egg_id

        Parameters:
            egg_id (Int) - egg_id to lookup
            
        Returns Dictionary"""
        if egg_id in self.data_eggs:
            return self.data_eggs[egg_id]
        
        return False
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def are_eggs_unlocked(self, player_level):
        """Are the Eggs feature available for player (at their player_level)?

        Parameters:
            player_level (Int) - player player_level

        Returns Boolean"""
        for egg_id, e in self.data_eggs.items():
            if e[Column.PLAYER_LEVEL] == player_level:
                return e[Column.EGG_COUNT] > 0
        
        return False
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_egg_id(self, player_level):
        """Get the first egg_id for the player's player_level (there may be multiple eggs per player_level

        Parameters:
            player_level (Int) - player player_level

        Returns Int or False"""
        for egg_id, e in self.data_eggs.items():
            if e[Column.PLAYER_LEVEL] == player_level:
                return egg_id
        
        return False
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_egg_goal(self, egg_id):
        """Get the progression goal for the egg_id

        Parameters:
            egg_id (Int) - player player_level

        Returns Int or False"""
        if egg_id in self.data_eggs:
            return self.get_egg_data(egg_id)[Column.GOAL]
        
        return False
    
    # ------------------------------------------------------------------------------------------------------------
    def get_curr_egg_id(self):
        """Get the current egg_id player is working on

        Returns Int"""
        return self.state[State.CURRENT_EGG_ID]
    
    # ------------------------------------------------------------------------------------------------------------
    def get_curr_egg_progress(self):
        """Get the current progression player has on completing the egg

        Returns Int"""
        return self.state[State.CURRENT_EGG_PROGRESS]
    
    # ------------------------------------------------------------------------------------------------------------
    def get_curr_egg_goal(self):
        """Get the goal for the current egg player is working on

        Returns Int"""
        if self.state[State.CURRENT_EGG_ID] > 0:
            return self.get_egg_goal(self.state[State.CURRENT_EGG_ID])
        
        return False
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_egg_reward(self, egg_id):
        """Get the reward for completing a specific egg

        Returns Int (Egg_ID)"""
        return self.get_egg_data(egg_id)[Column.REWARD_ID]
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_gacha_egg_data(self, egg_id):
        """Get details on what rarity animals an egg might contain

        Returns Dictionary"""
        return self.data_gacha_eggs[egg_id]
    
    # ------------------------------------------------------------------------------------------------------------
    def open_egg(self, egg_id, unique=False):
        """WHen opening an egg, figure out what animal was earned

        Parameters:
            egg_id (Int) - egg id to lookup
            unique (Boolean) - Can player get a duplicate animal or should it be new (unique)
            
        Returns Int - Animal Type ID"""
        egg_data = self.get_gacha_egg_data(egg_id)
        
        # Get data_animals that meet player_level lock (unique flag for RTP)
        if unique:
            animals = self.get_animals_not_found(self.player.level)
            
            if len(animals) == 0:
                animals = self.get_unlocked_animals(self.player.level)
        else:
            animals = self.get_unlocked_animals(self.player.level)
        
        # Now filter the possible data_animals based on unlocked Animal Sets
        allowed_sets = self.player.get_acquired_sets()
        allowed_sets = allowed_sets + [max(allowed_sets) + 1]
        animals = [a for a in animals if a[Animal.SET_ID] in allowed_sets]
        
        # Finally, use the Egg_ID rarity rules to further filter
        pool = []
        for rarity in range(1, 6):
            col = f'Rarity_{rarity}'
            weight = egg_data[col]
            
            # If no weight assigned, skip this rarity
            if not weight >= 1:
                continue
            
            # Add data_animals of this rarity to the pool to draw from
            for animal in animals:
                if animal[Animal.RARITY] == rarity:
                    pool.append(animal)
        
        # Randomly draw an animal from possible animals
        draw = get_random_uniform(0, len(pool), RANDOM.INTEGER)
        animal = pool[draw]
        
        self.log(f"open_egg() {egg_id} {len(pool)} {animal[Animal.TYPE_ID]}")
        
        return animal[Animal.TYPE_ID]
    
    # ============================================================================================================
    # RTP Free Crate Methods
    # ============================================================================================================
    def get_rtp_timer(self):
        """Get time until next free create spawns

        Returns Int - seconds"""
        return get_random_uniform(self.settings[Setting.RTP_TIME_MIN],
                                  self.settings[Setting.RTP_TIME_MAX],
                                  RANDOM.INTEGER)
    
    # ============================================================================================================
    # PLAYER LEVEL Methods
    # ============================================================================================================
    @lru_cache()
    def get_player_level_data(self, player_level):
        """Return config for the current player player_level

        Parameters:
            player_level (Int) - player player_level

        Returns Dictionary - Player Data"""
        return self.data_player_levels[player_level]
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_player_candy_range(self, player_level):
        """What candy levels can player buy?

        Parameters:
            player_level (Int) - player player_level

        Returns Tuple (min candy player_level, max candy player_level)"""
        candy_level_min = self.get_player_level_data(player_level)[Column.CANDY_LEVEL_MIN]
        candy_level_max = self.get_player_level_data(player_level)[Column.CANDY_LEVEL_MAX]
        return candy_level_min, candy_level_max

    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_player_xp_level(self, xp):
        """Given XP, what player_level is player?

        Parameters:
            xp (Int) - experience points (earned by buying candies)

        Returns Int - Player player_level"""
        player_level = 1
        
        # Loop thru levels and match the XP value to pick row
        for level_data in self.data_player_levels.values():
            if xp >= level_data[Column.XP_REQ_TOTAL]:
                player_level = level_data[Column.PLAYER_LEVEL] + 1
            else:
                break
        
        return player_level
    
    # ------------------------------------------------------------------------------------------------------------
    @lru_cache()
    def get_player_level_reward(self, player_level):
        """When a player levels up, what Egg do they get and how much soft currency?

        Parameters:
            player_level (Int) - experience points (earned by buying candies)

        Returns Int - Player level"""
        # Get data for player_level
        level_data = self.get_player_level_data(player_level)
        
        curr_soft = level_data[Column.LUR_SOFT]  # soft currency earned on levelup
        egg_id = level_data[Column.LUR_EGG_ID]  # egg_id (optional) earned
        
        return curr_soft, egg_id
    
    # =============================================================================================================
    # QUEUE ACTION
    # =============================================================================================================
    def add_action(self, action, key, data):
        """Add an action to the player queue of possible actions.

        Parameters:
            action (String) - ActionType (from enums)
            key (Object) - Unique identifier to differential similar actions
            data (Dict) - payload of parameters necessary to do action

        Returns Boolean - was action added"""
        
        # Check for a duplicate action already in queue - if found, bail out
        for a in self.state[State.ACTIONS]:
            if a[Params.ACTION] == action and a[Params.KEY] == key:
                return False
        
        # Action not yet in queue, go ahead and add the action
        self.state[State.ACTIONS].append({
            Params.ACTION_ID: len(self.state[State.ACTIONS]) + 1,
            Params.ACTION   : action,
            Params.KEY      : key,
            Params.DATA     : data,
            Params.TIMER    : self.player.get_general_time()
        })
        
        return True
    
    # =============================================================================================================
    # Candy Buying
    # =============================================================================================================
    def check_buy_candy(self):
        """Can player buy any candies?
        
        Returns Boolean"""
        self.log(f"check_buy_candy()")
        
        # If no slots available, player cannot purchase
        if not self.candy_slot_available():
            return False
        
        # Remove any previous BUY_CANDY actions from queue
        actions = []
        for action in self.state[State.ACTIONS]:
            if action[Params.ACTION] != Actions.BUY_CANDY:
                actions.append(action)
        self.state[State.ACTIONS] = actions
        
        # get allow range of possible candy levels can be purchased
        candy_level_min, candy_level_max = self.get_player_candy_range(self.player.level)
        
        # Does player have enough soft currency to buy cheapest candy?
        if self.player.get_soft_currency() < self.get_candy_cost(candy_level_min):
            return False
        
        # Does the player have any low player_level single data_candies?
        single_candy = False
        for candy_level in range(candy_level_min, candy_level_max + 1):
            if self.get_candy_count(candy_level) == 1:
                single_candy = self.candy_data(candy_level)
                break
        
        # Buy singles to fill in and merge low so they aren't blocking a candy slot
        if single_candy:
            if self.player.get_soft_currency() >= self.get_candy_cost(single_candy[Column.CANDY_LEVEL]):
                # Add action to action queue
                self.add_action(action=Actions.BUY_CANDY,
                                key=single_candy[Column.CANDY_LEVEL],
                                data=single_candy)
                
                return True
        
        # Otherwise buy highest affordable
        else:
            for candy_level in range(candy_level_max, candy_level_min - 1, -1):
                if self.player.get_soft_currency() >= self.get_candy_cost(candy_level):
                    # Build payload to add to action
                    candy = self.candy_data(candy_level)
                    
                    # Add action to action queue
                    self.add_action(action=Actions.BUY_CANDY,
                                    key=candy_level,
                                    data=candy)
                    
                    return True
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    def click_buy_candy(self, candy):
        """Player has clicked to buy a candy
        
        Parameters:
            candy (Dict) - Action data payload
            
        Returns Boolean"""
        self.log(f"click_buy_candy(), {candy[Column.CANDY_LEVEL]}, {candy[Column.CANDY_COST]}")
        
        # Verify player still has sufficient soft currency
        if self.player.get_soft_currency() < candy[Column.CANDY_COST]:
            return False
        
        # Make sure there is an available candy slot for he purchase
        if not self.candy_slot_available():
            return False
        
        self.player.spend_soft_currency(candy[Column.CANDY_COST])
        self.player.earn_xp(candy[Column.XP_EARNED])
        self.candy_slot_add(candy[Column.CANDY_LEVEL])
        self.player.track[Track.BUY_CANDY] += f'{candy[Column.CANDY_LEVEL]},'
        
        return True
    
    # =============================================================================================================
    # Free Crates (RTP Return to Player System)
    # =============================================================================================================
    def check_free_crate(self):
        """Check if any free crates should spawn or are available
        
        Returns Boolean"""
        
        self.log(f"check_free_crate()")
        
        # ----- Check if a free chest is available -----
        if self.time_free_crate_reset > self.state[State.FREE_CRATE_TIMER]:
            # TODO - Use RTP to calculate contents and add to data payload
            
            # Create payload to add to action
            data = {}
            
            # Add action to action queue
            self.add_action(action=Actions.FREE_CRATE,
                            key=self.state[State.FREE_CRATE_NUMBER],
                            data=data)
            
            return True
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    def click_free_crate(self, data):
        """Player has clicked to open a free chest reward
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        
        self.log(f"click_free_crate()")
        
        # TODO - Award Free Crate
        
        self.time_free_crate_reset = 0
        self.state[State.FREE_CRATE_NUMBER] += 1
        self.player.track[Track.FREE_CRATE] += 1
        self.state[State.FREE_CRATE_TIMER] = self.get_rtp_timer()
        
        return True
    
    # =============================================================================================================
    # Animal Donation
    # =============================================================================================================
    def click_donate_animal(self, data):
        """Player has clicked to donate n animal
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        
        self.log(f"click_donate_animal()")
        
        animal_id = data[Animal.ID]
        self.player.donate_animal(animal_id)
        
        return True
    
    # =============================================================================================================
    # Feeding Animals
    # =============================================================================================================
    def check_egg_progress(self):
        """Has player completed any Eggs?
        
        Returns Boolean"""
        self.log(f"check_egg_progress()")
        
        # See if data_eggs are unlocked or can be
        if self.state[State.CURRENT_EGG_ID] == 0 and self.are_eggs_unlocked(self.player.level):
            self.state[State.CURRENT_EGG_ID] = self.get_egg_id(self.player.level)
            self.state[State.CURRENT_EGG_PROGRESS] = 0
            return False
        
        elif not self.are_eggs_unlocked(self.player.level):
            return False
        
        # Convenience Aliases
        egg_id = self.state[State.CURRENT_EGG_ID]
        progress = self.state[State.CURRENT_EGG_PROGRESS]
        goal = self.get_egg_goal(egg_id)
        
        if progress >= goal:
            egg_type = self.get_egg_reward(egg_id)
            delta = progress - goal
            
            self.player.earn_egg(egg_id, egg_type)
            
            self.state[State.CURRENT_EGG_ID] += 1
            self.state[State.CURRENT_EGG_PROGRESS] = delta
        
        return True
    
    # =============================================================================================================
    # Feeding Animals
    # =============================================================================================================
    def check_feed_animal(self):
        """Can player feed any data_animals?
        
        Returns Boolean"""
        self.log(f"check_feed_animal()")
        
        # Get list of currently active data_animals
        animals = self.player.get_animal_inventory(status=AnimalState.ACTIVE)
        if len(animals) == 0:
            return False
        
        # Get list of available data_candies to feed
        candy_levels = sorted(list(set(self.get_candy_slot_candies())))
        if len(candy_levels) == 0:
            return False
        
        # Get lowest player_level animal (assume player always feeds lowest possible)
        animals_ordered = sorted(animals,
                                 key=lambda a: (a[Animal.LEVEL], -a[Animal.RARITY], a[Animal.ID]))
        animal = animals_ordered[0]
        
        candy_options = []
        for candy_level in candy_levels:
            if candy_level >= animal[Animal.LEVEL]:
                candy_options.append(candy_level)
        
        # If not available feed options, bail
        if len(candy_options) == 0:
            return False
        
        # Player behavior - player feed highest possible candy
        if self.player.behavior_bet == 1:
            candy = candy_options[-1]
        
        # Player behavior player feeds lowest allowed candy
        elif self.player.behavior_bet == 2:
            candy = candy_options[0]
        
        # Player selects random allowed candy
        else:
            roll = get_random_normal(0, len(candy_options), RANDOM.INTEGER)
            candy = candy_options[roll]
        
        # Build payload with action details
        data = {
            Params.ANIMAL_ID    : animal[Animal.ID],
            Params.ANIMAL_LEVEL : animal[Animal.LEVEL],
            Params.ANIMAL_RARITY: animal[Animal.RARITY],
            Params.CANDY_LEVEL  : candy
        }
        
        # Add action to action queue
        self.add_action(action=Actions.FEED_ANIMAL,
                        key=animal[Animal.ID],
                        data=data)
        
        return True
    
    # -------------------------------------------------------------------------------------------------------------
    def click_feed_animal(self, data):
        """Player has clicked to feed an animal
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        self.log(f"click_feed_animal()")
        
        animal_id = data[Params.ANIMAL_ID]
        candy_level = data[Params.CANDY_LEVEL]
        
        # Make sure animal is still slotted
        if not self.animal_socket_has(animal_id):
            return False
        
        # If candy player_level is still available, remove it, feed animal, earn egg progress
        if self.candy_slot_remove(candy_level):
            self.player.feed_animal(animal_id, candy_level)
            
            if self.state[State.CURRENT_EGG_ID]:
                self.state[State.CURRENT_EGG_PROGRESS] += self.get_candy_cost(candy_level)
    
    # =============================================================================================================
    # Merging Candies
    # =============================================================================================================
    def check_merge_candy(self):
        """Can player merge and data_candies on board?
        
        Returns Boolean"""
        self.log(f"check_merge_candy()")
        
        # Player has to have 2+ data_candies to even do a merge
        if len(self.state[State.CANDY_SLOTS]) < 2:
            return False
        
        # Get list of unique candy levels in candy slots
        unique_candies = sorted(self.get_candy_slot_unique())
        
        # Loop thru each candy player_level and see if we have 2+ that could be merged
        # Note: There is a cap on allowed candy_level
        for candy_level in unique_candies:
            if candy_level > self.settings[Setting.CANDY_LEVEL_MAX]:
                continue
            
            candy_count = self.get_candy_count(candy_level)
            
            # Players has at least 2, so can merge
            if candy_count >= 2:
                # Build payload with action details
                data = {Params.CANDY_LEVEL: candy_level}
                
                # Add action to action queue
                self.add_action(action=Actions.MERGE_CANDY,
                                key=candy_level,
                                data=data)
        
        return True
    
    # -------------------------------------------------------------------------------------------------------------
    def click_merge_candy(self, data):
        """Player has clicked to merge 2 candies to a higher level
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        self.log(f"click_merge_candy()")
        
        # Make sure we still have 2+ of these data_candies on the board
        candy_level = data[Params.CANDY_LEVEL]
        candy_count = self.get_candy_count(candy_level)
        
        # Make sure player still has 2+ of these data_candies to merge
        if candy_count >= 2:
            # Remove both data_candies
            self.candy_slot_remove(candy_level)
            self.candy_slot_remove(candy_level)
            
            # Add new candy of +1 player_level to board
            new_candy = candy_level + 1
            self.candy_slot_add(new_candy)
            
            self.player.track[Track.MERGE_CANDY] += f'{new_candy},'
            
            return True
        
        return False
    
    # =============================================================================================================
    # Gacha Spin Wheel
    # =============================================================================================================
    def check_spin_wheel(self):
        """Is a Spin Wheel available to click?
        
        Returns Boolean"""
        self.log(f"check_spin_wheel()")
        
        max_set = self.player.get_max_set()
        
        # Check if player can do Spin Wheel #2 (higher player_level)
        if max_set >= self.settings[Setting.FORTUNE_SPIN_UNLOCK_2]:
            if self.player.get_secondary_currency() >= self.settings[Setting.FORTUNE_SPIN_COST_2]:
                if len(self.get_animals_not_found_4_5(self.player.level)) > 0:
                    # Build payload with action details
                    data = {
                        Params.SPIN_WHEEL: Wheel.TWO,
                        Params.SPIN_COST : self.settings[Setting.FORTUNE_SPIN_COST_2],
                        Params.EGG_ID    : self.settings[Setting.FORTUNE_SPIN_REWARD_2],
                    }
                    
                    # Add action to action queue
                    self.add_action(action=Actions.SPIN_WHEEL,
                                    key=Wheel.TWO,
                                    data=data)
                    
                    return True
        
        # Check if player can do Spin Wheel #1 (lower player_level)
        elif max_set >= self.settings[Setting.FORTUNE_SPIN_UNLOCK_1]:
            if self.player.get_secondary_currency() >= self.settings[Setting.FORTUNE_SPIN_COST_1]:
                if len(self.get_animals_not_found_1_3(self.player.level)) > 0:
                    # Build payload with action details
                    data = {
                        Params.SPIN_WHEEL: Wheel.ONE,
                        Params.SPIN_COST : self.settings[Setting.FORTUNE_SPIN_COST_1],
                        Params.EGG_ID    : self.settings[Setting.FORTUNE_SPIN_REWARD_1],
                    }
                    
                    # Add action to action queue
                    self.add_action(action=Actions.SPIN_WHEEL,
                                    key=Wheel.ONE,
                                    data=data)
                    
                    return True
    
    # -------------------------------------------------------------------------------------------------------------
    def click_spin_wheel(self, data):
        """Player has clicked to spin wheel
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        self.log(f"click_spin_wheel()")
        
        if self.player.get_secondary_currency() < data[Params.SPIN_COST]:
            return False
        
        self.player.spend_secondary_currency(data[Params.SPIN_COST])
        animal_id = self.player.earn_egg('S', data[Params.EGG_ID])
        
        if data[Params.SPIN_WHEEL] == 1:
            self.player.track[Track.SPIN_WHEEL_1] += f'{animal_id},'
        else:
            self.player.track[Track.SPIN_WHEEL_2] += f'{animal_id},'
        
        return True
    
    # =============================================================================================================
    # Swap Animals from Inventory into Socket
    # =============================================================================================================
    def check_swap_animals(self):
        """Should or can the player swap any data_animals?
        
        Returns True"""
        self.log(f"check_swap_animals()")
        
        # Find active animal that would be best to swap into inventory
        animal_active = self.player.get_animal_to_swap()
        
        # Get animal from INVENTORY that would be best to make ACTIVE
        animal_not_active = self.player.get_animal_to_socket()
        
        # If either is missing, we can bail ... swapping not possible
        if not animal_active or not animal_not_active:
            return False
        
        # Check if the non-active is better than our active animal
        swap = False
        
        if animal_not_active[Animal.LEVEL] < animal_active[Animal.LEVEL]:
            swap = True
        
        # If non-active is better queue up a swap
        if swap:
            # Build payload with action details
            data = {
                Params.SWAP_ID_1: animal_active[Animal.ID],
                Params.SWAP_ID_2: animal_not_active[Animal.ID]
            }
            
            # Add action to action queue
            self.add_action(action=Actions.SWAP_ANIMALS,
                            key=animal_active[Animal.ID],
                            data=data)
            
            return True
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    def click_swap_animals(self, data):
        """Player has clicked to swap animals
        
        Parameters:
            data (Dict) - Action data payload
            
        Returns Boolean"""
        swap_id_1 = data[Params.SWAP_ID_1]
        swap_id_2 = data[Params.SWAP_ID_2]
        
        self.log(f"click_swap_animals(), {swap_id_1}, {swap_id_2}")
        
        if self.animal_socket_has(swap_id_1) and self.player.animal_inventory_has(swap_id_2):
            self.animal_socket_remove(swap_id_1)
            self.animal_socket_add(swap_id_2)
            
            self.player.track[Track.SWAP_ANIMAL] += f'(-{swap_id_1},+{swap_id_2}),'
            
            return True
        
        return False
    
    # =============================================================================================================
    # Handle Offline Regen
    # =============================================================================================================
    def check_offline(self):
        """Check if Player has gone offline

        Returns Int - seconds until next active session"""
        # ----- Check Session Online/Offline -----
        if self.frame % self.settings[Setting.SIM_FPS] == 0:
            self.time_session += 1
            self.time_inapp += 1
            self.time_real += 1
            self.time_video_reset += 1
            self.time_free_crate_reset += 1
        
        # Check if Session is over
        if self.time_session >= self.state[State.CURRENT_SESS_ONLINE]:
            # Remove certain queued actions that may no longer be relevant
            for i, a in enumerate(self.state[State.ACTIONS]):
                remove_these = [Actions.BUY_CANDY, Actions.SPIN_WHEEL, Actions.MERGE_CANDY,
                                Actions.FEED_ANIMAL, Actions.DONATE_ANIMAL,
                                Actions.SWAP_ANIMALS]
                
                if a[Params.ACTION] in remove_these:
                    self.state[State.ACTIONS] = self.player.remove_action_by_id(self.state[State.ACTIONS],
                                                                                a[Params.ACTION_ID])
            
            # Calculate offline time until next session
            offline_time = self.player.get_offline_duration() - self.state[State.CURRENT_SESS_ONLINE]
            
            # --- Calculate new levels and output
            
            # Players earn passive revenue while offline - cal and add to balances
            self.process_offline_regen(offline_time)
            
            self.player.gcd = 0
            self.time_inapp += 1
            self.time_session = 1
            self.time_real += offline_time
            self.time_video_reset += offline_time
            self.time_free_crate_reset += offline_time
            self.day = math.ceil(self.time_real / 86400)
            
            self.session += 1
            
            self.snapshot.save_snapshot()
            
            # Calculate next online session duration
            self.state[State.CURRENT_SESS_ONLINE] = self.player.get_session_duration(self.session)
            
            return offline_time
        
        else:
            return 0
    
    # =============================================================================================================
    def process_offline_regen(self, t):
        """Player earns passive revenue while offline.  Calculate and add offline regen to their balance"""
        
        # Offline passive revenue is time capped
        time_cap = self.settings[Setting.OFFLINE_REGEN_TIME_CAP]
        t = t if t < time_cap else time_cap
        
        # Earn Soft Currency per Sec
        self.player.earn_soft_currency(math.floor(self.player.get_soft_per_sec() * t))
    
    # =============================================================================================================
    # MAIN SIMULATION CORE LOOP
    # =============================================================================================================
    def simulation(self, env):
        while True:
            self.frame = env.now + 1
            
            # ----- Check if player has gone offline -----
            # timer will hold the "offline time" if appropriate (0 if still online)
            timer = self.check_offline()
            
            # if we hit a offline time, yield simpy so simulation env matches our time tracking
            if timer > 0:
                yield env.timeout(timer * self.settings[Setting.SIM_FPS])
            
            # Check if video limit should be reset
            self.player.check_reset_video_count()
            
            # ----- Check if player has earned soft currency -----
            if self.frame % self.settings[Setting.SIM_FPS] == 0:
                self.player.earn_soft_currency(self.player.get_soft_per_sec())
            
            # ----- Check available actions player can do -----
            # If player is in middle of another action, don't check for new ones yet
            if self.player.gcd <= 0:
                # self.check_free_crate()
                self.check_spin_wheel()
                self.check_merge_candy()
                self.check_feed_animal()
                self.check_buy_candy()
                self.check_swap_animals()
                
                self.check_egg_progress()
                
                # Player is stuck (no actions remaining) - end session early
                if self.time_inapp > 60 and len(self.state[State.ACTIONS]) == 0:
                    self.state[State.CURRENT_SESS_ONLINE] = self.time_session
            
            # ----- Process Player actions -----
            self.player.choose_action()
            
            # ----- Save out current status to a row in our results csv -----
            if self.frame % (self.settings[Setting.SNAPSHOT_TIME] * self.settings[Setting.SIM_FPS]) == 0:
                self.snapshot.save_snapshot()
            
            yield env.timeout(1)
    
    # ------
    def start_sim(self, sim_time_length):
        self.env.process(self.simulation(self.env))
        self.env.run(until=int(sim_time_length))
    
    # ------------------------------------------------------------------------------------------------------------
    def log(self, message, console=False, eol=True):
        log_to_file(f"{self.player.player_id}, {self.frame / self.settings[Setting.SIM_FPS]}, " + message, console=console, eol=eol)
