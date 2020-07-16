import pandas as pd
import time
import datetime

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Custom Classes
from SimEngine.Game import Game
from SimEngine.Player import Player
from SimEngine.StringConstants import *
from SimEngine.UtilityFunctions import *

# --- make sure we have all necessary project folders ---
folders = ['./logs',
           './datasets',
           './datasets/batch', './datasets/cache', './datasets/output', './datasets/raw',
           './reports',
           './temp']

for folder in folders:
    if not os.path.exists(folder):
        os.mkdir(folder)

# ==================================================================================
# Enter variant details here:

SIMULATION_GOOGLE_SHEET_ID = '<enter GoogleDoc ID here>'
SIMULATION_VARIANTS_SHEET = 'variants!A1:G100'


# ==================================================================================
def worker(run_number, v_id, v_data):
    """
    Worker process
    """
    log_to_file(f'Simulation Start: ({run_number} | {v_id} | {v_data["sim_count"]} | {v_data["sim_length"]})')
    
    # Create a game
    game = Game()
    game.init_game(v_data)
    
    # initialize virtual player
    player = Player()
    player.init_player(player_id=run_number,
                       variant=v_id,
                       v_data=v_data,
                       game=game)
    
    game.set_player(player)
    game.start_sim(int(v_data['sim_length']) * int(v_data['sim_fps']))
    flush_log()
    
    # Save player simulation csv candy to folder
    results_df = game.snapshot.results_df
    results_df.fillna(0, inplace=True)
    results_df = results_df.applymap(convert_numbers)

    # Reorder Animal and Candy Columns to End of DataFrame
    cols = results_df.columns
    candy_cols = sorted([c_col for c_col in cols if c_col[:2] == 'c_'], key=lambda x: int(x[2:]))
    animal_cols = sorted([a_col for a_col in cols if a_col[:2] == 'a_'], key=lambda x: int(x[2:]))
    cols_c_a = candy_cols + animal_cols
    other_cols = [o_col for o_col in cols if o_col not in cols_c_a]
    
    cols = other_cols + cols_c_a
    results_df = results_df[cols]

    results_df.to_csv(f'datasets/batch/{v_id}_{run_number}.csv', index=False)
    
    log_to_file(f'Simulation End: ({run_number} | {v_id} | {v_data["sim_count"]} | {v_data["sim_length"]})')
    flush_log()
    
    del game, player, run_number, v_id, v_data


# ==================================================================================
def add_tasks(variants):
    """
    Method to populate list of initialization candy for every simulation run
    This method is run by the parent process so has access to globals
    """
    num = 0
    
    for v_id in variants.keys():
        v_data = variants[v_id]

        # --- load candy sheets
        data_sheets = [d for d in v_data.keys() if d[0:5] == 'data_']
        
        # Loop thru candy sheets and add them as dataframes to v_data (to be passed to the gane & player)
        for d in data_sheets:
            # Load the variant candy fro the Google sheet
            # The "False" will force candy sheets to be reloaded every time to replace cache
            if True and os.path.exists(f'datasets/cache/{d}.csv'):
                v_data[d] = pd.read_csv(f'datasets/cache/{d}.csv')
                v_data[d] = v_data[d].applymap(convert_numbers)
                
            else:
                data = load_data(SIMULATION_GOOGLE_SHEET_ID, v_data[d])
                v_data[d] = pd.DataFrame(data[1:], columns=data[0])
                v_data[d] = v_data[d].applymap(convert_numbers)
    
                v_data[d].to_csv(f'datasets/cache/{d}.csv', index=False)
                v_data[d] = pd.read_csv(f'datasets/cache/{d}.csv')
                v_data[d] = v_data[d].applymap(convert_numbers)

        # --- Add parameters to sim queue
        for i in range(v_data['sim_count']):
            worker(num, v_id, v_data)
            num += 1


# ==================================================================================
def load_data(file, sheet_range):
    """Load candy from GoogleSheets"""
    credentials = None
    
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/spreadsheets.readonly'])
            credentials = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    service = build('sheets', 'v4', credentials=credentials)
    
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=file, range=sheet_range).execute()
    values = result.get('values', [])
    
    return values


# ==================================================================================
if __name__ == "__main__":
    # ----
    # Load the variant candy fro the Google sheet
    # Note: The "False" forces us to always reload the variants tab and overwrite cache
    if True and os.path.isfile('datasets/cache/data_variants.csv'):
        variant_df = pd.read_csv('datasets/cache/data_variants.csv')
        variant_df = variant_df.applymap(convert_numbers)
    else:
        variant_data = load_data(SIMULATION_GOOGLE_SHEET_ID, SIMULATION_VARIANTS_SHEET)
        variant_df = pd.DataFrame(variant_data[1:], columns=variant_data[0])
        variant_df = variant_df.applymap(convert_numbers)
        variant_df.to_csv('datasets/cache/data_variants.csv', index=False)
    
    # --- Build VARIANTS Dictionary
    VARIANTS = {}
    for c, col in enumerate(variant_df):
        if c == 0:
            parameter = col
            continue
            
        VARIANTS[int(col)] = {}
        
        for row in variant_df.iterrows():
            VARIANTS[int(col)][row[1][0]] = row[1][c]
   
    # ----- Simulation parameters
    SIM_CYCLES = sum([v['sim_count'] for v in VARIANTS.values()])
    
    CACHE_FOLDER = 'datasets/batch/*'
    QUESTS_FOLDER = 'datasets/quests/*'
    OUTPUT_FOLDER = 'datasets/output/'
    
    # ==================================================================================
    reset_log()
    log_to_file(f'Running {SIM_CYCLES} players!')

    # -----
    # Clear our cache folder (note, each simulation cycle will save it's results there
    # and we will aggregate those files back together at the end of the run)
    purge_disk_cache(CACHE_FOLDER)
    purge_disk_cache(QUESTS_FOLDER)

    # ---------------- RUN SIMULATION ----------------------------------
    start = time.time()
    
    add_tasks(VARIANTS)
    flush_log()
    
    print('Simulation Complete')
    print(f'Time taken = {time.time() - start:.10f}')
    
    # -----
    # Save simulation results to CSV
    log_to_file('Collecting candy for analysis and saving copies')
    Results_DF = pd.concat([pd.read_csv(f, low_memory=False) for f in glob.glob('datasets/batch/*')], sort=False, ignore_index=True)

    # Note log_ts was defined in UtilityFunctions
    fn = f'{OUTPUT_FOLDER}simulation_results_{log_ts}_{SIM_CYCLES}'

    Results_DF.to_csv(fn + '.csv')
    
    # This is a binary save format candy uses - it's way faster and smaller files sizes
    # Results_DF.to_parquet(fn + '.gzip', compression='gzip')

    log_to_file('Dataset saved to datasets/ folder')
    flush_log()
    # ----------------- ALL DONE -----------------------------
