import os
import glob
import numpy as np
from functools import lru_cache
import pandas as pd
import datetime
import math
from sympy import symbols, integrate

from SimEngine.StringConstants import *

from scipy.stats import truncnorm

# --- make sure we have a ./logs folder ---
if not os.path.exists('./logs'):
    os.mkdir('./logs')

log_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
log_file = open(f"logs/sim_{log_ts}.log", "w")
log_data = ''


# ------------------------------------------------------------------------------------------------------------
@lru_cache()
def pad_zeros(n, size):
    """Utility function to pad an integer with zeros and return as a string"""
    return str(n).zfill(size)


# ------------------------------------------------------------------------------------------------------------
def get_random_normal(min_value=0, max_value=10, sd=1):
    """Get a normal distribution between a min and max.  We will approximate a normal using a Beta
    Distribution"""
    
    # IF min and max are the same, just return that value
    if min_value == max_value:
        return min_value
    
    # In case someone swapped the min and max values - switch them back
    if min_value > max_value:
        temp = min_value
        min_value = max_value
        max_value = temp
    
    mean_value = (max_value + min_value) / 2
    a = (min_value - mean_value) / sd
    b = (max_value - mean_value) / sd
    
    if a == 0 and b == 0:
        return 0
    
    x = truncnorm.rvs(a, b, loc=mean_value, scale=sd, size=1)
    
    return x[0]


# ------------------------------------------------------------------------------------------------------------
def get_random_uniform(min_value=None, max_value=None, random_type=None):
    """Get a uniform distribution between a min and max"""
    if min_value is None and max_value is None and random_type is None:
        return np.random.random()
    
    elif min_value is None and max_value is None:
        return False
    
    random_value = False
    
    # IF min and max are the same, just return that value
    if min_value == max_value:
        return min_value
    
    # In case someone swapped the min and max values - switch them back
    if min_value > max_value:
        temp = min_value
        min_value = max_value
        max_value = temp

    if random_type == RANDOM.INTEGER:
        random_value = np.random.randint(min_value, max_value)
    
    elif random_type == RANDOM.FLOAT:
        random_value = np.random.random() * (max_value - min_value) + min_value
    
    else:
        random_value = np.random.random() * (max_value - min_value) + min_value

    return random_value


# ------------------------------------------------------------------------------------------------------------
def get_random_boolean():
    """Get a random boolean: True of False"""
    return bool(np.random.randint(0, 1))


# ------------------------------------------------------------------------------------------------------------
def convert_numbers(x):
    """Given a DF, convert all numeric values into numbers (int if possible)"""
    if x is None:
        return None
    
    if type(x) != str:
        if type(x) == float:
            if x.is_integer():
                return int(x)
        return x
    
    if x.replace('.', '', 1).isdigit():
        x = float(x)
        
        if x.is_integer():
            x = int(x)
    
    return x


# ------------------------------------------------------------------------------------------------------------
def purge_disk_cache(folder):
    """
    Method to clear all files from our cache folder
    """
    files = glob.glob(folder)
    
    for f in files:
        os.remove(f)


# ------------------------------------------------------------------------------------------------------------
def log_to_file(message, console=False, eol=True, end='\n'):
    global log_ts, log_data, log_file
    
    end = end if eol else ""
    log_data += f"{message}{end}"
    
    if len(log_data) > 100000:
        print(f"{log_data}", file=log_file)
        log_data = ""
    
    if console:
        print(f"{message}", end=end)


# ------------------------------------------------------------------------------------------------------------
def flush_log():
    global log_ts, log_data, log_file
    print(f"{log_data}", file=log_file)
    log_data = ""


# ------------------------------------------------------------------------------------------------------------
def reset_log():
    global log_ts, log_data, log_file
    log_data = ""
