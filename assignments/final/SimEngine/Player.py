import random
import math
from functools import lru_cache

from .StringConstants import *
from .UtilityFunctions import *


class Player:
    """Common base class for all virtual SimEngine Players"""
    
    # -----------------------------------------------------------
    # STATIC PROPERTIES GO HERE (Shared by all player instances)
    
    # ------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        Player Constructor

        player_id (Integer)        - unique id assigned to each player (autoincrement)
        variant (Integer)          - which "group" the player is in
        """
        self.sim_mode = 1
        
        # ----- parameters passed when instantiating a player -----
        self.player_id = 0  # Unique run id - autoincrement
        self.variant = 0  # which variant is the player in?
        self.variant_label = ''
        
        # ----- Player details (may differ based on variant) -----
        self.game = None  # Reference to Game Object
        self.gcd = 0  # Global cool down (prevent spam actions)
        
        self.session_params = {
            Session.PER_DAY        : 0,
            Session.DURATION_MIN   : 0,
            Session.DURATION_MAX   : 0,
        }
        
        self.sessions = None
        
        # Behavior flags that determine how player will make choices
        self.behavior_action = None
        self.behavior_animal_swap = None
        self.behavior_bet = None
        self.behavior_feed_order = None
        self.behavior_offerwall = None
        self.behavior_shop = None
        self.behavior_video = None
        
        # Player reaction time to perform actions
        self.player_time_general_min = 0
        self.player_time_general_max = 0
        
        # ----- Player specific balances, information and track -----
        self.animal_count = 0  # How many animals does player have?
        self.last_action = None
        self.level = 1  # Player's level
        self.starting_animal_type = None  # Which animal did player start with?
        self.videos_watched = 0  # How many videos has player watched?
        self.xp = 0  # player's XP balance
        
        # In Zoo, this is CASH - used to buy candies
        self.curr_soft = {
            Currency.BALANCE   : 0,
            Currency.EARNED    : 0,
            Currency.MAX       : 0,
            Currency.PER_SECOND: 0,
            Currency.SPENT     : 0,
            
        }
        
        # In Zoo, these are TREATS - earned when getting new animals, used to pin fortune wheel
        self.curr_secondary = {
            Currency.BALANCE   : 0,
            Currency.EARNED    : 0,
            Currency.MAX       : 0,
            Currency.PER_SECOND: 0,
            Currency.SPENT     : 0,
        }
        
        # In Zoo, there are gems (diamonds) - used to buy stuff
        self.curr_premium = {
            Currency.BALANCE   : 0,
            Currency.EARNED    : 0,
            Currency.MAX       : 0,
            Currency.PER_SECOND: 0,
            Currency.SPENT     : 0,
        }
        
        # player's inventory of earned animals
        self.animal_inventory = {}
        
        # track counters for csv reporting per second
        self.track = {
            Track.ACTION_COUNT    : 0,
            Track.ANIMAL_IDS      : '',
            Track.ANIMALS_EARNED  : 0,
            Track.BUY_CANDY       : '',
            Track.DONATE_ANIMAL   : 0,
            Track.EGG_COMPLETE    : '',
            Track.FEED_ANIMAL     : '',
            Track.FREE_CRATE      : 0,
            Track.MERGE_CANDY     : '',
            Track.PLAYER_LEVEL_UP : 0,
            Track.PREMIUM_EARNED  : 0,
            Track.PREMIUM_SPENT   : 0,
            Track.SECONDARY_EARNED: 0,
            Track.SECONDARY_SPENT : 0,
            Track.SOFT_EARNED     : 0,
            Track.SOFT_SPENT      : 0,
            Track.SPIN_WHEEL_1    : '',
            Track.SPIN_WHEEL_2    : '',
            Track.SWAP_ANIMAL     : '',
            Track.VIDEO_WATCHED   : 0
        }
    
    # ------------------------------------------------------------------------------------------------------------
    def init_player(self, player_id, variant, v_data, game):
        """Set up the player
        
        Parameters:
            player_id (Int) - player ID
            variant (Int) - variant ID
            v_data (Dict) - player config details from GoogleSheet (Variants Tab)
            game (Game Object) - reference to main game object
            """
        self.game = game  # Reference to Game Object
        
        self.player_id = player_id  # Unique run id - autoincrement
        self.variant = variant  # which variant is the player in?
        self.variant_label = v_data[Variants.VARIANT_LABEL]
        
        # Set unique attributes/behaviors for the player (based on variant settings)
        self.game.settings[Setting.SIM_MODE] = v_data[Variants.SIM_MODE]
        self.game.settings[Setting.SIM_FPS] = v_data[Variants.SIM_FPS]
        self.game.settings[Setting.SNAPSHOT_TIME] = v_data[Variants.SIM_SNAPSHOT_TIME]
        
        # initial soft currency to start with
        self.curr_soft[Currency.BALANCE] = v_data[Variants.CURRENCY_SOFT_START]
        self.curr_soft[Currency.MAX] = v_data[Variants.CURRENCY_SOFT_START]
        
        # initial premium currency to start with
        self.curr_premium[Currency.BALANCE] = v_data[Variants.CURRENCY_PREMIUM_START]
        self.curr_premium[Currency.MAX] = v_data[Variants.CURRENCY_PREMIUM_START]
        
        # initial secondary currency to start with
        self.curr_secondary[Currency.BALANCE] = v_data[Variants.CURRENCY_SECONDARY_START]
        self.curr_secondary[Currency.MAX] = v_data[Variants.CURRENCY_SECONDARY_START]
        
        # Session (online/offline) settings
        self.session_params = {
            Session.PER_DAY        : v_data[Variants.SESS_PER_DAY],
            Session.DURATION_MIN   : v_data[Variants.SESS_DURATION_MIN].split(','),
            Session.DURATION_MAX   : v_data[Variants.SESS_DURATION_MAX].split(','),
        }
        
        # Player behavior flags
        self.behavior_action = v_data[Variants.PLAYER_BEHAVIOR_ACTION]
        self.behavior_animal_swap = v_data[Variants.PLAYER_BEHAVIOR_ANIMAL_SWAP]
        self.behavior_bet = v_data[Variants.PLAYER_BEHAVIOR_BET]
        self.behavior_feed_order = v_data[Variants.PLAYER_BEHAVIOR_FEED_ORDER]
        self.behavior_offerwall = v_data[Variants.PLAYER_BEHAVIOR_OFFERWALL]
        self.behavior_shop = v_data[Variants.PLAYER_BEHAVIOR_SHOP]
        self.behavior_video = v_data[Variants.PLAYER_BEHAVIOR_VIDEO]
        
        # Player reaction times
        self.player_time_general_min = v_data[Variants.PLAYER_TIME_GENERAL_MIN]
        self.player_time_general_max = v_data[Variants.PLAYER_TIME_GENERAL_MAX]
        
        # Set a reference on the Game instance to this Player instance
        self.game.player = self
        
        # Pick/initialize first animal (Dingo or Arabian Horse)
        roll = get_random_uniform(0,
                                  len(self.game.settings[Setting.STARTING_ANIMALS]),
                                  RANDOM.INTEGER)
        self.starting_animal_type = int(self.game.settings[Setting.STARTING_ANIMALS][roll])
        
        # Set initial online session duration
        self.game.state[State.CURRENT_SESS_ONLINE] = self.get_session_duration(1)
        
        # Add animal to player's inventory
        self.earn_animal(self.starting_animal_type)
    
    # =============================================================================================================
    # ANIMALS
    # =============================================================================================================
    def get_animal_unique_id(self):
        """Return a unique id for each animal - simple autoincrement
        
        Returns unique auto-number ID for every earned animal"""
        self.animal_count += 1
        return self.animal_count
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animal_by_unique_id(self, animal_id):
        """Return an animal object given it's unique ID
        
        Parameters:
            animal_id (Int) - animal ID
            
        Returns Dict - Animal Object or False"""
        if animal_id in self.animal_inventory:
            return self.animal_inventory[animal_id]
        else:
            return False
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animal_count(self, animal_type_id):
        """Return how many of the animal_id the player has in their inventory

        Parameters:
            animal_type_id (Int) - animal ID

        Returns Int """
        return sum([1 for a in self.animal_inventory.values() if a[Animal.TYPE_ID] == animal_type_id])

    # -------------------------------------------------------------------------------------------------------------
    def get_animal_to_socket(self):
        """Look through inventory and return optimal animal to make active"""
        # Find best non-active animal
        animals = self.get_animal_inventory(status=AnimalState.INVENTORIED)
    
        # If no animals available to swap, we can bail
        if len(animals) == 0:
            return False
    
        # Sort animals best to worse
        animals_ordered = sorted(animals,
                                 key=lambda a: (a[Animal.LEVEL], -a[Animal.RARITY], a[Animal.ID]))
        return animals_ordered[0]

    # -------------------------------------------------------------------------------------------------------------
    def get_animal_to_swap(self):
        """Look through active animals and return optimal animal to swap to inventory"""
        # Find best non-active animal
        animals = self.get_animal_inventory(status=AnimalState.ACTIVE)
    
        # If no animals available to swap, we can bail
        if len(animals) == 0:
            return False
    
        # Sort animals best to worse
        animals_ordered = sorted(animals,
                                 key=lambda a: (-a[Animal.LEVEL], a[Animal.RARITY], a[Animal.ID]))
        return animals_ordered[0]

    # -------------------------------------------------------------------------------------------------------------
    def get_animal_to_donate(self):
        """Look through inventory and return optimal animal to donate"""
        # Find best non-active animal
        animals = self.get_animal_inventory(status=AnimalState.INVENTORIED)
    
        # If no animals available to swap, we can bail
        if len(animals) == 0:
            return False
    
        # Sort animals best to worse
        animals_ordered = sorted(animals,
                                 key=lambda a: (-a[Animal.LEVEL], a[Animal.RARITY], a[Animal.ID]))
        return animals_ordered[0][Animal.ID]

    # -------------------------------------------------------------------------------------------------------------
    def earn_animal(self, animal):
        """Player earned an animal
        
        Parameters:
            animal (Dict) - animal object
            
        Returns Int - Animal unique auto-number id"""
        if isinstance(animal, int):
            animal = self.game.get_animal_by_animal_id(animal).copy()
        
        # Get unique ID for the animal
        animal_unique_id = self.get_animal_unique_id()
        animal[Animal.ID] = animal_unique_id
        animal[Animal.LEVEL] = 1
        animal[Animal.STATUS] = AnimalState.INVENTORIED
        
        # Add animal to inventory dictionary
        self.animal_inventory[animal_unique_id] = animal
        self.earn_secondary_currency(animal[Animal.TREATS_EARNED])
        
        # Auto slot animal if possible in a habitat
        if self.game.animal_socket_available():
            self.game.animal_socket_add(animal[Animal.ID])
        
        self.track[Track.ANIMALS_EARNED] += 1
        self.track[Track.ANIMAL_IDS] += f'{animal[Animal.TYPE_ID]},'
        
        # if player has exceeded inventory cap, must donate
        active = len(self.get_animal_inventory(AnimalState.ACTIVE))
        inventory = len(self.get_animal_inventory(AnimalState.INVENTORIED))
        
        # Over cap, so must donate
        if active + inventory > self.game.settings[Setting.ANIMAL_INVENTORY_CAP]:
            donate_id = self.get_animal_to_donate()
            self.donate_animal(donate_id)
        
        return animal_unique_id
    
    # -------------------------------------------------------------------------------------------------------------
    def feed_animal(self, animal_id, candy_level):
        """Player earned an animal
        
        Parameters:
            animal_id (Int) - animal id
            candy_level (Int) - Candy level feed to animal
            
        Returns Boolean"""
        self.animal_inventory[animal_id][Animal.LEVEL] = candy_level + 1
        self.track[Track.FEED_ANIMAL] += f'({animal_id}, {candy_level}),'
        
        return True
    
    # -------------------------------------------------------------------------------------------------------------
    def donate_animal(self, animal_id):
        """Player donated an animal
        
        Parameters:
            animal_id (Int) - animal id
            
        Returns Boolean"""
        
        # Remove the animal from the habitat if necessary
        if animal_id in self.animal_inventory:
            self.game.animal_socket_remove(animal_id)
            self.animal_inventory[animal_id][Animal.STATUS] = AnimalState.DONATED
            
            self.track[Track.DONATE_ANIMAL] += 1
            
            if self.game.animal_socket_available():
                animal = self.get_animal_to_socket()
                
                if animal:
                    self.game.animal_socket_add(animal[Animal.ID])
        
        return True
    
    # -------------------------------------------------------------------------------------------------------------
    def get_acquired_animals(self):
        """List all unique data_animals player has acquired
        Returns List<Animal Dict Objects>"""
        acquired_animals = []
        
        for animal_id, animal in self.animal_inventory.items():
            acquired_animals.append(animal[Animal.TYPE_ID])
        
        acquired_animals = list(set(acquired_animals))
        return acquired_animals
    
    # -------------------------------------------------------------------------------------------------------------
    def get_acquired_sets(self):
        """List all Animal Set #'s player has unlocked
        Returns List<Int> - Animal Sets layer has animals in"""
        sets = []
        
        for animal_id, animal in self.animal_inventory.items():
            sets.append(animal[Animal.SET_ID])
        
        sets = list(set(sets))
        return sets
    
    # -------------------------------------------------------------------------------------------------------------
    def get_max_set(self):
        """List max unlocked Set #
        Returns Int - Max Animal Set unlocked"""
        return max(self.get_acquired_sets())

    # -------------------------------------------------------------------------------------------------------------
    def get_sets_count(self):
        """List all Animal Set #'s player has completed
        Returns List<Int> - All Animal Sets completed"""
    
        # For completing sets, we need need to exclude duplicates of animals
        # and only count unique copies
        unique_animals = self.get_acquired_animals()
        
        sets_count = np.zeros(24)
        for animal_id in unique_animals:
            set_id = self.game.get_animal_set(animal_id)
            sets_count[set_id] += 1
    
        return sets_count
    
    # -------------------------------------------------------------------------------------------------------------
    def get_completed_sets(self):
        """List all Animal Set #'s player has completed
        Returns List<Int> - All Animal Sets completed"""
        sets_count = self.get_sets_count()
        
        sets_completed = []
        
        for idx, s in enumerate(sets_count):
            if s == 5:
                sets_completed.append(idx)
        
        return sets_completed
    
    # -------------------------------------------------------------------------------------------------------------
    def get_max_completed_set(self):
        """List max unlocked Set #
        Returns Int - Max Animal Set Completed"""
        if len(self.get_completed_sets()) == 0:
            return 0
        else:
            return max(self.get_completed_sets())
    
    # -------------------------------------------------------------------------------------------------------------
    def animal_inventory_has(self, animal_id):
        """Check if the animal is in the player's inventory
        
        Parameters:
            animal_id (Int) - animal ID
        Returns Boolean"""
        if animal_id in self.animal_inventory:
            # Need to return the opposite of Active status.  ie "has" means it is NOT active
            return self.animal_inventory[animal_id][Animal.STATUS] == AnimalState.INVENTORIED
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    def get_animal_inventory(self, status=False):
        """Player earned an animal
        
        Parameters:
            status (Boolean) - AnimalState.ACTIVE, .INVENTORIED, .DONATED, .ALL
            
        Returns List<Animal Dict Objects>"""
        animals = []
        
        # Loop thru all animals and build list that matches requests status
        for animal in self.animal_inventory.values():
            if status == AnimalState.ALL:
                animals.append(animal)
            elif animal[Animal.STATUS] == status:
                animals.append(animal)
        
        return animals
    
    # =============================================================================================================
    # Currency PREMIUM
    # =============================================================================================================
    def get_premium_currency(self):
        """Return player's premium balance
        Returns Int"""
        return self.curr_premium[Currency.BALANCE]
    
    # ---------------------------------------------------------------------------------------------------------------
    def earn_premium_currency(self, amount):
        """Add premium to player's balance
        
        Returns Boolean"""
        self.curr_premium[Currency.BALANCE] += amount
        self.curr_premium[Currency.MAX] += amount
        self.curr_premium[Currency.EARNED] += amount
        
        self.track[Track.PREMIUM_EARNED] += amount
        
        return True
    
    # ---------------------------------------------------------------------------------------------------------------
    def spend_premium_currency(self, amount):
        """Subtract premium from player's balance
        
        Returns Boolean"""
        if amount <= self.curr_premium[Currency.BALANCE]:
            self.curr_premium[Currency.BALANCE] -= amount
            self.curr_premium[Currency.SPENT] += amount
            
            self.track[Track.PREMIUM_SPENT] += amount
            return True
        else:
            return False
    
    # =============================================================================================================
    # Currency SECONDARY
    # =============================================================================================================
    def get_secondary_currency(self):
        """Return current Secondary Currency balance
        
        Returns Int"""
        return self.curr_secondary[Currency.BALANCE]
    
    # ---------------------------------------------------------------------------------------------------------------
    def earn_secondary_currency(self, amount):
        """Add Secondary currency to player balance
        
        Returns Boolean"""
        self.curr_secondary[Currency.BALANCE] += amount
        self.curr_secondary[Currency.MAX] += amount
        self.curr_secondary[Currency.EARNED] += amount
        
        self.track[Track.SECONDARY_EARNED] += amount
        
        return True
    
    # ---------------------------------------------------------------------------------------------------------------
    def spend_secondary_currency(self, amount):
        """Spend Secondary Currency - deduct from player balance
        
        Returns Boolean"""
        if amount <= self.curr_secondary[Currency.BALANCE]:
            self.curr_secondary[Currency.BALANCE] -= amount
            self.curr_secondary[Currency.SPENT] += amount
            
            self.track[Track.SECONDARY_SPENT] += amount
            
            return True
        
        return False
    
    # =============================================================================================================
    # Currency SOFT
    # =============================================================================================================
    def get_soft_currency(self):
        """Return current soft balance
        
        Returns Int"""
        return self.curr_soft[Currency.BALANCE]
    
    # ---------------------------------------------------------------------------------------------------------------
    def get_soft_currency_max(self):
        """Return max soft earned
        
        Returns Int"""
        return self.curr_soft[Currency.MAX]
    
    # ---------------------------------------------------------------------------------------------------------------
    def earn_soft_currency(self, amount):
        """Add soft to player's balance
        
        Returns Boolean"""
        self.curr_soft[Currency.BALANCE] += amount
        self.curr_soft[Currency.MAX] += amount
        self.curr_soft[Currency.EARNED] += amount
        
        self.track[Track.SOFT_EARNED] += amount
        
        return True
    
    # ---------------------------------------------------------------------------------------------------------------
    def spend_soft_currency(self, amount):
        """Subtract soft to player's balance
        
        Returns Boolean"""
        if amount <= self.curr_soft[Currency.BALANCE]:
            self.curr_soft[Currency.BALANCE] -= amount
            self.curr_soft[Currency.SPENT] += amount
            
            self.track[Track.SOFT_SPENT] += amount
            
            return True
        
        return False
    
    # -------------------------------------------------------------------------------------------------------------
    def get_soft_per_sec(self):
        """Get soft currency earned each second
        Returns Int"""
        income = [a[Animal.REVENUE] for a in self.animal_inventory.values() if a[Animal.STATUS] == AnimalState.ACTIVE]
        return sum(income)
    
    # =============================================================================================================
    # EGGS
    # =============================================================================================================
    def earn_egg(self, egg_id, egg_type):
        """Player earned an egg (i.e. new animal)
        Parameters:
            egg_id (Int) - egg ID
            egg_type (Int) - egg type
            
        Returns Boolean"""
        animal_type = self.game.open_egg(egg_type)
        animal_id = self.earn_animal(animal_type)
        
        self.track[Track.EGG_COMPLETE] += f'({egg_id},{egg_type}),'
        if self.game.animal_socket_available:
            self.game.animal_socket_add(animal_id)
        
        return animal_id
    
    # =============================================================================================================
    # PLAYER Track
    # =============================================================================================================
    def levelup_player(self, level):
        """Player increased their player_level
        Parameters:
            level (Int) - player level
        Returns Boolean"""
        
        old_level = self.level
        delta = level - old_level
        self.level = level
        self.track[Track.PLAYER_LEVEL_UP] += delta
        
        soft, egg_type = self.game.get_player_level_reward(old_level)
        
        self.earn_soft_currency(soft)
        
        if egg_type > 0:
            self.earn_egg(0, egg_type)
        
        return True
    
    # =============================================================================================================
    # REPORTING - Reset track values
    # =============================================================================================================
    def reset_reporting_counters(self):
        """Clear the counters used to track earn/spend per snapshot reporting cycle"""
        for k in self.track.keys():
            self.track[k] = 0
        
        self.track[Track.ANIMAL_IDS] = ''
        self.track[Track.BUY_CANDY] = ''
        self.track[Track.EGG_COMPLETE] = ''
        self.track[Track.FEED_ANIMAL] = ''
        self.track[Track.MERGE_CANDY] = ''
        self.track[Track.SPIN_WHEEL_1] = ''
        self.track[Track.SPIN_WHEEL_2] = ''
        self.track[Track.SWAP_ANIMAL] = ''
    
    # =============================================================================================================
    # SESSION TRACKING - Sessions per day, session length, etc
    # =============================================================================================================
    def get_sessions_per_day(self):
        """Using real session data - return session for day (drawn from Poisson)"""
        sessions = np.random.poisson(self.session_params[Session.PER_DAY], 1)
        
        # Note we enforce at least 1 session per day
        return sessions or 1
    
    # -------------------------------------------------------------------------------------------------------------
    def get_offline_duration(self):
        """Using real session data - return time until next session (drawn from Poisson)"""
        
        session_rate = self.get_sessions_per_day()
        
        lambda_rate = 1 / session_rate
        return math.floor(np.random.exponential(lambda_rate) * 86400)

    # -------------------------------------------------------------------------------------------------------------
    def get_session_duration(self, sess_num):
        """Using real session data - return session duration for given session number
        
        Parameters:
            sess_num (int) - session number
            
        Returns Int"""
        # Calculate duration lower bound from parameters in GoogleSheet
        # Supports log, linear or fixed lower bound
        if self.session_params[Session.DURATION_MIN][0] == 'log':
            alpha = float(self.session_params[Session.DURATION_MIN][1])
            beta = float(self.session_params[Session.DURATION_MIN][2])
            dur_min = alpha * np.log(sess_num) + beta
        elif self.session_params[Session.DURATION_MIN][0] == 'linear':
            alpha = float(self.session_params[Session.DURATION_MIN][1])
            beta = float(self.session_params[Session.DURATION_MIN][2])
            dur_min = alpha * sess_num + beta
        else:
            dur_min = float(self.session_params[Session.DURATION_MIN][1])

        # Calculate duration upper bound from parameters in GoogleSheet
        # Supports log, linear or fixed lower bound
        if self.session_params[Session.DURATION_MAX][0] == 'log':
            alpha = float(self.session_params[Session.DURATION_MAX][1])
            beta = float(self.session_params[Session.DURATION_MAX][2])
            dur_max = alpha * np.log(sess_num) + beta
        elif self.session_params[Session.DURATION_MAX][0] == 'linear':
            alpha = float(self.session_params[Session.DURATION_MAX][1])
            beta = float(self.session_params[Session.DURATION_MAX][2])
            dur_max = alpha * sess_num + beta
        else:
            dur_max = float(self.session_params[Session.DURATION_MAX][1])

        # Get a random duration between bounds.  Note, probably should
        # change this to get a normal between bounds so durations are
        # weighted to the middle
        
        # For Session 1-2, we override the default
        if sess_num == 1:
            session_dur = get_random_uniform(204, 1126, RANDOM.INTEGER)
        elif sess_num == 2:
            session_dur = get_random_uniform(208, 901, RANDOM.INTEGER)
        else:
            session_dur = get_random_uniform(dur_min, dur_max, RANDOM.INTEGER)

        return math.floor(session_dur)
        
    # -------------------------------------------------------------------------------------------------------------
    def get_general_time(self):
        """Get a normal distribution between a min and max"""
        return round(get_random_normal(self.player_time_general_min, self.player_time_general_max), 2)
    
    # =============================================================================================================
    # VIDEO Watching
    # =============================================================================================================
    def check_reset_video_count(self):
        """Clear the daily video limit counter"""
        if self.game.time_video_reset > self.game.settings[Setting.VIDEO_LIMIT_RESET]:
            self.videos_watched = 0
            self.game.time_video_reset = 0
    
    # -------------------------------------------------------------------------------------------------------------
    def get_video_count(self):
        """Get videos watched this day"""
        return self.videos_watched
    
    # -------------------------------------------------------------------------------------------------------------
    def increment_video_count(self):
        """Clear the counters used to track earn/spend per reporting cycle"""
        self.videos_watched += 1
    
    # -------------------------------------------------------------------------------------------------------------
    def get_video_choice(self):
        """Return boolean whether player watches an optional video"""
        if self.method_video == Video.ALWAYS:
            return True
        
        elif self.method_video == Video.NEVER:
            return False
        
        elif self.method_video == Video.RANDOM:
            return get_random_boolean()
        
        elif self.method_video == Video.EXPERT:
            # future expert system
            return False
    
    # =============================================================================================================
    # XP - Experience Points
    # =============================================================================================================
    def get_xp(self):
        """Return player's XP"""
        return self.xp
    
    # ---------------------------------------------------------------------------------------------------------------
    def earn_xp(self, amount):
        """Add XP to player's balance"""
        self.xp += amount
        check_level = self.game.get_player_xp_level(self.xp)
        
        if check_level > self.level:
            self.levelup_player(check_level)
    
    # =============================================================================================================
    # Core Logic where Player Chooses Action to do
    # =============================================================================================================
    @staticmethod
    def get_actions_by_type(actions, action_type):
        """Given a specific ActionType, return list of matching actions from Queue"""
        filter_actions = []
        
        for i, action in enumerate(actions):
            if action[Params.ACTION] == action_type:
                filter_actions.append(action)
        
        return filter_actions
    
    # ------------
    @staticmethod
    def remove_action_by_id(actions, action_id):
        """Given action_id, rebuild Action Queue without that action_id"""
        return [a for a in actions if a[Params.ACTION_ID] != action_id]
    
    # ------------
    def clear_action(self, action):
        """Remove action from the Queue
        Parameters:
            action (Dict)
            
        Return Boolean"""
        self.gcd = action[Params.TIMER]
        self.last_action = action
        self.game.state[State.ACTIONS] = self.remove_action_by_id(self.game.state[State.ACTIONS],
                                                                  action[Params.ACTION_ID])
        self.track[Track.ACTION_COUNT] += 1
        
        return True
    
    # ------------
    def choose_action(self):
        """If any actions in queue, choose the correct one and do it based on Player options.
        Note: Player can only do one action per sim cycle (sim_fps), so this logic should mirror hat we would expect a
        player to do in order.  We can pass in variant candy to experiment with players making different choices and
        that impact on overall progression through the economy.
        """
        
        # --- Global Cool Down in effect from prev action
        # If the player did some previous action that triggered wait time, don't do anything this cycle
        if self.gcd > 0:
            self.gcd -= round(1 / self.game.settings[Setting.SIM_FPS], 2)
            self.gcd = round(self.gcd, 2)
            return False
        
        # --- Nothing to do
        if len(self.game.state[State.ACTIONS]) == 0:
            return False
        
        # --- Loop thru possible choices and pick an action to do
        # TODO - Use player_behavior_action to reorder this list
        for possible_action in [Actions.FREE_CRATE,
                                Actions.FEED_ANIMAL,
                                Actions.MERGE_CANDY,
                                Actions.SWAP_ANIMALS,
                                Actions.BUY_CANDY,
                                Actions.COLLECT_REWARD,
                                Actions.SPIN_WHEEL,
                                Actions.DONATE_ANIMAL]:
            
            # Get actions from queue matching the ActionType
            filter_actions = self.get_actions_by_type(self.game.state[State.ACTIONS], possible_action)
            
            # If we have some actions of the given type
            if filter_actions and len(filter_actions) > 0:
                
                # If there are several possible options for the same action, sort them in priority order
                if possible_action == Actions.FEED_ANIMAL:
                    sort_method = self.behavior_feed_order
                    
                    if sort_method == 0:
                        random.shuffle(filter_actions)
                    elif sort_method == 1:
                        filter_actions = sorted(filter_actions,
                                                key=lambda i: (i[Params.DATA][Params.ANIMAL_LEVEL],
                                                               i[Params.DATA][Params.ANIMAL_RARITY]),
                                                reverse=True)
                    elif sort_method == 2:
                        filter_actions = sorted(filter_actions,
                                                key=lambda i: (i[Params.DATA][Params.ANIMAL_RARITY],
                                                               i[Params.DATA][Params.ANIMAL_LEVEL]),
                                                reverse=True)
                    elif sort_method == 3:
                        filter_actions = sorted(filter_actions,
                                                key=lambda i: (i[Params.DATA][Params.ANIMAL_LEVEL],
                                                               i[Params.DATA][Params.ANIMAL_RARITY]),
                                                reverse=False)
                    elif sort_method == 4:
                        filter_actions = sorted(filter_actions,
                                                key=lambda i: (i[Params.DATA][Params.ANIMAL_RARITY],
                                                               i[Params.DATA][Params.ANIMAL_LEVEL]),
                                                reverse=False)
                
                # grab action off top of list
                action = filter_actions.pop(0)
                
                # ==========================================
                # Do the chosen ACTION
                # ==========================================
                
                # --- FREE_CRATE ---
                if possible_action == Actions.FREE_CRATE:
                    self.game.click_free_crate(action[Params.DATA])
                
                # --- COLLECT_REWARD ---
                elif possible_action == Actions.COLLECT_REWARD:
                    self.game.click_collect_reward(action[Params.DATA])
                
                # --- FEED_ANIMAL ---
                elif possible_action == Actions.FEED_ANIMAL:
                    self.game.click_feed_animal(action[Params.DATA])
                
                # --- MERGE_CANDY ---
                elif possible_action == Actions.MERGE_CANDY:
                    self.game.click_merge_candy(action[Params.DATA])
                
                # --- BUY_CANDY ---
                elif possible_action == Actions.BUY_CANDY:
                    result = self.game.click_buy_candy(action[Params.DATA])
                    
                # --- SPIN_WHEEL ---
                elif possible_action == Actions.SPIN_WHEEL:
                    self.game.click_spin_wheel(action[Params.DATA])
                
                # --- SWAP_ANIMALS ---
                elif possible_action == Actions.SWAP_ANIMALS:
                    self.game.click_swap_animals(action[Params.DATA])
                
                # --- DONATE_ANIMAL ---
                elif possible_action == Actions.DONATE_ANIMAL:
                    self.game.click_donate_animal(action[Params.DATA])
                
                # --- Unhandled action type
                else:
                    print(f'Unhandled Action: {possible_action}')
                    self.clear_action(action)
                    return False
                
                self.clear_action(action)
                return True
        
        return False
