import harp
import pandas as pd
import os
import matplotlib.pyplot as plt

# Import custom functions
import timestamps.harp.utils as hu
import timestamps.utils.plot_utils as pu
                
# ----------------------------------------------------------------------------------
# Section 0: Define directory and analysis params
# ----------------------------------------------------------------------------------

# path raw data on Ceph repo
RAW_DATA_ROOT_DIR = "W:\\projects\\FlexiVexi\\raw_data"

# Path to save intermediate variables on Ceph repo
OUTPUT_ROOT_DIR = "W:\\projects\\FlexiVexi\\data_analysis\\intermediate_variables"

# Specify mapping from sound index to reward port
SOUND_MAPPING = {
    'soundIdx0' :14,
    'soundIdx1' : 10,
    'soundOffIdx' : 18
}

# ----------------------------------------------------------------------------------
# Section 1: Import data
# ----------------------------------------------------------------------------------

class harp_session():

    def __init__(self, animal_ID, session_ID, raw_data_dir = RAW_DATA_ROOT_DIR, output_dir = OUTPUT_ROOT_DIR, sound_mapping  = SOUND_MAPPING): 

        raw_data_session_dir = os.path.join(raw_data_dir, animal_ID, session_ID)
        output_session_dir = os.path.join(output_dir, animal_ID, session_ID)

        self.animal_ID = animal_ID
        self.session_ID = session_ID
        self.sound_mapping = sound_mapping
        self.raw_data_session_dir = raw_data_session_dir
        self.output_session_dir = output_session_dir

        # Q: WHY IS THIS NEEDED?
        self.raw_data_root_dir = raw_data_dir
        self.output_root_dir = output_dir

        # Create reader for behavior from behavior binary files
        bin_b_path = os.path.join(
            raw_data_dir, 
            animal_ID, 
            session_ID, 
            "Behavior.harp"
        )
        behavior_reader = harp.create_reader(bin_b_path)

        # Path to sound card binary file
        bin_sound_path = os.path.join(
            raw_data_dir,
            animal_ID,
            session_ID,
            "SoundCard.harp",
            "SoundCard_32.bin"
        )

        # Path to experimental-data .csv
        experimental_data_path = hu.get_experimental_data(
            os.path.join(
                raw_data_dir, 
                animal_ID, 
                session_ID
           )
        )
        
        # Q: NOT SURE IF THIS IS NECESSARY IF WE HAVE HARP INTERMEDIATE VARIABLES ALREADY?
        self.behavior_reader = behavior_reader
        self.experimental_data_path = experimental_data_path

        #==============================================================================
        # Append data from harp events and Bonsai .csv outputs to harp session
        #==============================================================================

        # Read the harp sound card stream, for the timestamps and audio ID
        self.sound_events = hu.get_all_sounds(bin_sound_path)

        # Read in harp binaries to get photodiode data series
        self.photodiode_data = hu.get_photodiode_data(behavior_reader)

        # Read in harp binaries to get poke events data frame
        self.poke_events = hu.get_all_pokes(behavior_reader)

        # Read in Bonsai .csv file with trial-level information as a pandas DataFrame
        self.trials_df = pd.read_csv(experimental_data_path)

        #==============================================================================
        # Create output directories
        #==============================================================================

        #Q: IS CREATING MOUSE_OUTPUT_DIR NECESSARY?
        os.makedirs(output_session_dir, exist_ok = True)

    def save_harp_data_streams(self):

        # Save poke events data frame as .csv
        poke_events_filename = self.animal_ID + '_' + self.session_ID + '_' + 'poke_events.csv'
        poke_events_filepath = os.path.join(self.output_session_dir, poke_events_filename)
        self.poke_events.to_csv(poke_events_filepath)

        # Save photodiode data series as .csv
        photodiode_filename = self.animal_ID + '_' + self.session_ID + '_' + 'photodiode_data.csv'
        photodiode_filepath = os.path.join(self.output_session_dir, photodiode_filename)
        self.photodiode_data.to_csv(photodiode_filepath)

        # Save sound events data frame as .csv
        sound_events_filename = self.animal_ID + '_' + self.session_ID + '_' + 'sound_events.csv'
        sound_events_filepath = os.path.join(self.output_session_dir, sound_events_filename)
        self.sound_events.to_csv(sound_events_filepath, index = False)
        
    # def save_experiment_csv(self):

    def import_behavioral_data(self):

        # Import behavioral data as data frame
        session_path = os.path.join(RAW_DATA_ROOT_DIR,self.animal_ID,self.session_ID)
        filepath = os.path.join(session_path,'Experimental-data' ,(self.session_ID + '_experimental-data.csv'))
        print(filepath)
        self.trials_df = pd.read_csv(filepath)

    def read_ttl(self):

        self.ttl_state_df = hu.get_ttl_state_df(self.behavior_reader)
        self.ttl_state_df.to_csv(os.path.join(self.output_session_dir, 'TTLs_harp.csv'))

    def plot_ttl(self, seconds = 20):
        '''
        Plots the ttl signal for the first ·seconds· seconds
        '''
        # Plot ttl trace
        plt.figure(figsize=(12, 6))  # Set the figure size (width, height) in inches
        ttl_pulse = pu.get_square_wave(self.ttl_state_df)
        ttl_pulse.plot(x='timestamp', y='state', linewidth=0.5)
        plt.xlabel('timestamp (s)')
        plt.legend(loc='upper right')
        plt.title("Plot TTL pulses, " + self.session_ID)
        t0 = ttl_pulse['timestamp'].iloc[0]
        plt.xlim(t0+50, t0 + seconds)
        # Save the figure with the name as the session_ID in the current directory
        output_filename = f"TTLs_in_harp_{self.session_ID}.png"
        plt.savefig(os.path.join(self.output_session_dir, output_filename))