import pandas as pd
import time
import datetime

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Visualization

# Parallel Processing
import multiprocessing as mp
import psutil

# Custom Classes
from SimEngine.Game import Game
from SimEngine.Player import Player
from SimEngine.StringConstants import *
from SimEngine.UtilityFunctions import *

# ==================================================================================
# Enter variant details here:

SIMULATION_GOOGLE_SHEET_ID = '16U3BSAZFElWEqjf4HL0YzlscroQhvw_zaZcJfcYXOMg'
SIMULATION_VARIANTS_SHEET = 'variants!A1:G100'


# ==================================================================================
def worker(task_queue):
    """
    Worker process - this will be run in each CPU in it's own Kernel.

    NOTE: This method does NOT have access to globals or any information in the parent process.
    It ony knows what is passed in via the task queue.
    """
    
    while not task_queue.empty():
        run_number, v_id, v_data = task_queue.get()
        
        # Create a game
        game = Game()
        game.init_game(v_data)
        
        log_to_file(f'Simulation Start: ({run_number} | {v_id} | {v_data["sim_count"]} | {v_data["sim_length"]})', end='\n')
        
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
        df = game.snapshot.results_df
        df.fillna(0, inplace=True)
        df = df.applymap(convert_numbers)
        
        # Reorder Adviser Columns to End of DataFrame
        cols = df.columns
        cols_minus_adv = [df_col for df_col in cols if 'Adviser' not in df_col]
        cols_adviser = [df_col for df_col in cols if 'Adviser' in df_col]
        cols = cols_minus_adv + cols_adviser
        df = df[cols]
        
        df.to_csv(f'datasets/batch/{v_id}_{run_number}.csv', index=False)
        
        log_to_file(f'Simulation End: ({run_number} | {v_id} | {v_data["sim_count"]} | {v_data["sim_length"]})')
        flush_log()
        
        del game, player, run_number, v_id, v_data
    
    return True


# ==================================================================================
def add_tasks(task_queue, variants):
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
            if False and os.path.exists(f'datasets/cache/{d}.csv'):
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
            task_queue.put((num, v_id, v_data))
            num += 1
    
    return task_queue


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
    if False and os.path.isfile('datasets/cache/data_variants.csv'):
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
    
    # Define runtime settings
    NUM_CPUS = psutil.cpu_count(logical=False)
    
    # ----- Simulation parameters
    PROCESSORS = NUM_CPUS - 1  # number of concurrent jobs (based on # CPU's in system)
    SIM_CYCLES = sum([v['sim_count'] for v in VARIANTS.values()])
    
    CACHE_FOLDER = 'datasets/batch/*'
    OUTPUT_FOLDER = 'datasets/output/'
    
    # ==================================================================================
    
    # -----
    # If fewer sim cycles than CPU's, only initialize with the number of sim cycles
    PROCESSORS = SIM_CYCLES if (SIM_CYCLES < PROCESSORS) else PROCESSORS
    processes = []
    
    reset_log()
    log_to_file(f'Running {SIM_CYCLES} players with {PROCESSORS} CPUs!')
    flush_log()
    
    # -----
    # Clear our cache folder (note, each simulation cycle will save it's results there
    # and we will aggregate those files back together at the end of the run)
    purge_disk_cache(CACHE_FOLDER)
    
    # -----
    # Setup a task queue for all sim cycles (players) in simulation
    empty_task_queue = mp.Queue()
    full_task_queue = add_tasks(empty_task_queue, VARIANTS)
    
    # ---------------- RUN SIMULATION ----------------------------------
    start = time.time()
    
    for n in range(PROCESSORS):
        p = mp.Process(target=worker, args=(full_task_queue,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
    
    flush_log()
    
    log_to_file('Simulation Complete')
    log_to_file(f'Time taken = {time.time() - start:.10f}')
    
    # -----
    # Save simulation results to CSV
    log_to_file('Collecting candy for analysis and saving copies')
    Results_DF = pd.concat([pd.read_csv(f) for f in glob.glob('datasets/batch/*')], ignore_index=True)
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    fn = f'{OUTPUT_FOLDER}simulation_results_{ts}_{SIM_CYCLES}'
    
    Results_DF.to_csv(fn + '.csv')
    
    # This is a binary save format candy uses - it's way faster and smaller files sizes
    Results_DF.to_parquet(fn + '.gzip', compression='gzip')
    
    log_to_file('Dataset saved to datasets/ folder')
    flush_log()
    # ----------------- ALL DONE -----------------------------
