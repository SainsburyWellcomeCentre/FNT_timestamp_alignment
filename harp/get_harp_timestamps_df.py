import harp
import pandas as pd
from harp.model import Model, Register, Access
import os
from pathlib import Path
import matplotlib.pyplot as plt

# Import custom functions
import harp_utils as hu
                
# ----------------------------------------------------------------------------------
# Section 0: Define directory and analysis params
# ----------------------------------------------------------------------------------

# Define animal and session ID
animal_ID = 'FNT103'
session_ID = '2024-08-20T15-21-13'

# path behavioural data on Ceph repo
INPUT = Path("/ceph/sjones/projects/FlexiVexi/behavioural_data/")
OUTPUT = Path("/ceph/sjones/projects/FlexiVexi/Data Analysis/intermediate_variables")

# Specify mapping from sound index to reward port
SOUNDS = {'soundIdx0' :14,
'soundIdx1' : 10,
'soundOffIdx' : 18}

# ----------------------------------------------------------------------------------
# Section 1: Import data
# ----------------------------------------------------------------------------------

class harp_session():

    def __init__(self, animal_ID, session_ID, INPUT, OUTPUT, SOUNDS): 

        self.animal_ID = animal_ID
        self.session_ID = session_ID
        self.sounds = SOUNDS
        self.input_root_dir = INPUT
        self.output_root_dir = OUTPUT

        # Create reader for behavior.
        bin_b_path = INPUT / animal_ID / session_ID / "Behavior.harp"

        behavior_reader = harp.create_reader(bin_b_path)

        self.behavior_reader = behavior_reader

        mousepath = OUTPUT / animal_ID
        mousepath.mkdir(exist_ok = True)

        sesspath = mousepath / session_ID
        sesspath.mkdir(exist_ok = True)

        self.sesspath = sesspath
    
    def import_behavioral_data(self):

        # Import behavioral data as data frame
        session_path = INPUT / animal_ID / session_ID
        filepath = session_path / 'Experimental-data' / (session_ID + '_experimental-data.csv')
        print(filepath)
        self.trials_df = pd.read_csv(filepath)

    def read_ttl(self):

        self.ttl_state_df = hu.get_ttl_state_df(self.behavior_reader)

    def plot_ttl(self, seconds = 20):
        '''
        Plots the ttl signal for the first ·seconds· seconds
        '''
        # Plot ttl trace
        plt.figure(figsize=(12, 6))  # Set the figure size (width, height) in inches
        ttl_pulse = hu.get_square_wave(self.ttl_state_df)
        ttl_pulse.plot(x='timestamp', y='state', linewidth=0.5)
        plt.xlabel('timestamp (s)')
        plt.legend(loc='upper right')
        plt.title("Plot TTL pulses, " + session_ID)
        t0 = ttl_pulse['timestamp'].iloc[0]
        plt.xlim(t0+50, t0 + seconds)
        # Save the figure with the name as the session_ID in the current directory
        output_filename = f"TTLs_in_harp_{self.session_ID}.png"
        plt.savefig((self.sesspath / output_filename))
        
        # Show the plot
        plt.show()

session = harp_session(animal_ID, session_ID, INPUT, OUTPUT, SOUNDS)

session.read_ttl()
session.plot_ttl(100)