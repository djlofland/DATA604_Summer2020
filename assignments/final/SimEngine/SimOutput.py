import pandas as pd
from .StringConstants import *
from .UtilityFunctions import *


class SimOutput:
    """Extend SimEngine Game and add CSV output reporting"""
    
    # -----------------------------------------------------------
    # STATIC PROPERTIES GO HERE (Shared by all player instances)
    
    # ------------------------------------------------------------------------------------------------------------
    def __init__(self, game):
        """
        SimOutput Constructor
        """
        self.game = game
        self.player = None
        # self.results_df = pd.DataFrame()  # Hold player simulation output
        self.results = []
    
    # ---------------------------------------------------------------------------------------------------------------
    def init(self, player):
        self.player = player
    
    # ---------------------------------------------------------------------------------------------------------------
    def save_snapshot(self):
        # log out the current game and player states
        # advisers = len(self.player.advisers.keys())
        # adviser_cards = sum([c[Param.COUNT] for k, c in self.player.advisers.items()]) if advisers > 0 else 0
        # adviser_max = max([c[Param.LEVEL] for k, c in self.player.advisers.items()]) if advisers > 0 else 0
        # adviser_unleveled = sum([c[Param.UNLEVELED] for k, c in self.player.advisers.items()]) if advisers > 0 else 0
        
        snapshot = {
            'day'                : int(self.game.day),
            'session'            : int(self.game.session),
            'time_real'          : int(self.game.time_real),
            'time_inapp'         : int(self.game.time_inapp),
            'time_sess'          : int(self.game.time_session),
            'id'                 : self.player.player_id,
            'variant'            : self.player.variant_label,
            'player_level'       : self.player.level,
            'player_xp'          : self.player.get_xp(),
            'anim_total'         : len(self.player.animal_inventory),
            'anim_socketed'      : len(self.game.state[State.ANIMAL_SOCKETS]),
            'anim_earned'        : self.player.track[Track.ANIMALS_EARNED],
            'anim_ids'           : self.player.track[Track.ANIMAL_IDS],
            'anim_sets_unlck'    : len(self.player.get_acquired_sets()),
            'anim_sets_max'      : self.player.get_max_set(),
            'anim_sets_cmplt'    : len(self.player.get_completed_sets()),
            'anim_sets_max_cmplt': self.player.get_max_completed_set(),
            'egg_id'             : self.game.get_curr_egg_id(),
            'egg_prog'           : self.game.get_curr_egg_progress(),
            'egg_goal'           : self.game.get_curr_egg_goal() or 0,
            'soft_earned'        : self.player.track[Track.SOFT_EARNED],
            'soft_spent'         : self.player.track[Track.SOFT_SPENT],
            'soft_bal'           : self.player.curr_soft[Currency.BALANCE],
            'secondary_earned'   : self.player.track[Track.SECONDARY_EARNED],
            'secondary_spent'    : self.player.track[Track.SECONDARY_SPENT],
            'secondary_bal'      : self.player.curr_secondary[Currency.BALANCE],
            'premium_earned'     : self.player.track[Track.PREMIUM_EARNED],
            'premium_spent'      : self.player.track[Track.PREMIUM_SPENT],
            'premium_bal'        : self.player.curr_premium[Currency.BALANCE],
            'candy_count'        : len(self.game.state[State.CANDY_SLOTS]),
            'a'                  : [a[Params.ACTION] for a in self.game.state[State.ACTIONS]],
            'actions'            : self.player.track[Track.ACTION_COUNT],
            'actions_buy'        : self.player.track[Track.BUY_CANDY],
            'actions_merge'      : self.player.track[Track.MERGE_CANDY],
            'actions_feed'       : self.player.track[Track.FEED_ANIMAL],
            'actions_eggs'       : self.player.track[Track.EGG_COMPLETE],
            'actions_level'      : self.player.track[Track.PLAYER_LEVEL_UP],
            'actions_crate'      : self.player.track[Track.FREE_CRATE],
            'actions_spin_1'     : self.player.track[Track.SPIN_WHEEL_1],
            'actions_spin_2'     : self.player.track[Track.SPIN_WHEEL_2],
            'actions_swap'       : self.player.track[Track.SWAP_ANIMAL],
            'actions_donate'     : self.player.track[Track.DONATE_ANIMAL],
        }
        
        # Loop and add columns to track animal inventory
        for key, a in self.player.animal_inventory.items():
            active = False
            
            if a[Animal.STATUS] == AnimalState.ACTIVE or a[Animal.STATUS] == AnimalState.INVENTORIED:
                active = 'S' if a[Animal.STATUS] == AnimalState.ACTIVE else 'I'
            
            if active:
                if f'a_{a[Animal.TYPE_ID]}' in snapshot:
                    snapshot[f'a_{a[Animal.TYPE_ID]}'] += f'({key},{a[Animal.LEVEL]},{active}),'
                else:
                    snapshot[f'a_{a[Animal.TYPE_ID]}'] = f'({key},{a[Animal.LEVEL]},{active}),'
        
        # Loop and add columns to track completed Animal Sets
        sets_count = self.player.get_sets_count()
        for i in range(1, 24):
            if sets_count[i] > 0:
                snapshot[f'as_{i}'] = sets_count[i]
        
        self.results += [snapshot]
        self.player.reset_reporting_counters()
    
    @property
    def results_df(self):
        return pd.DataFrame(self.results)
