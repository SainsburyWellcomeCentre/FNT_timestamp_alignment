import harp
import pandas as pd
from harp.model import Model, Register, Access
import os

# Import custom functions
import harp_utils as hu
                
# ----------------------------------------------------------------------------------
# Section 0: Define directory and analysis params
# ----------------------------------------------------------------------------------

# Define animal and session ID
animal_ID = 'FNT098'
session_ID = '2024-03-19T13-15-30'

# path behavioural data on Ceph repo
input_root_dir = r"W:\projects\FlexiVexi\behavioural_data" 
output_root_dir = (r"C:\Users\megan\Documents\sjlab\flexible-navigation-task" +
              r"\Data Analysis\intermediate_variables")

# Specify mapping from sound index to reward port
soundIdx0 = 14
soundIdx1 = 10
soundOffIdx = 18

# ----------------------------------------------------------------------------------
# Section 1: Import data
# ----------------------------------------------------------------------------------

# Create reader for behavior.
bin_b_path = os.path.join(
    input_root_dir, 
    animal_ID, 
    session_ID, 
    "Behavior.harp"
)
behavior_reader = harp.create_reader(bin_b_path)

# Create reader for sound card.
# NOTE: explicitly defined model will be deprecated or redundant in future
bin_sound_path = os.path.join(
    input_root_dir, 
    animal_ID, 
    session_ID, 
    "SoundCard.harp", 
    "SoundCard_32.bin"
)
model = Model(
    device='Soundcard', 
    whoAmI=1280,
    firmwareVersion='2.2',
    hardwareTargets='1.1',
    registers={
        'PlaySoundOrFrequency': Register(
            address=32, 
            type="U16", 
            access=Access.Event
        )
    }
)
sound_reader = harp.create_reader(model, keep_type=True)

# Import behavioral data as data frame
session_path = os.path.join(input_root_dir, animal_ID, session_ID)
filepath = os.path.join(session_path, 'Experimental-data', \
                        session_ID + '_experimental-data.csv')
trials_df = pd.read_csv(filepath)

# -----------------------------------------------------------------------------
# Section 2: Create data frame df_trials with trial summary info and 
#            harp timestamps
# -----------------------------------------------------------------------------

# get trial_start_times for the specified stage
stage = trials_df['TrainingStage'].iloc[0]
if stage == 4:
    dot_onset_times = trials_df['DotOnsetTime_harp']
    trial_start_times = get_trial_start_times(4, dot_onset_times=dot_onset_times)
elif stage == 5:
    trial_start_times = get_trial_start_times(5, bin_sound_path=bin_sound_path, sound_reader=sound_reader)
# Replace TrialStart in trials_df with trial start times from harp
trials_df['TrialStart'] = trial_start_times

# Get dot onset and offset times given by TTL pulses
ttl_state_df = hu.get_ttl_state_df(behavior_reader)
first_dot_onset_time = trials_df['DotOnsetTime'].iloc[0]
dot_times_ttl, ttl_state_0 = hu.get_dot_times_from_ttl(
    behavior_reader, 
    first_dot_onset_time, 
    return_TTL_state_at_startup=True
)
print('TTL state upon start-up: ', ttl_state_0)
trials_df = pd.concat([trials_df, dot_times_ttl], axis=1)

# Get a data frame with port choice and timestamp of port choice for each trial 
# in trials_df.
port_choice = hu.get_port_choice(trials_df, behavior_reader)
trials_df = pd.concat([trials_df, port_choice], axis=1)

# Get timestamp of all sound onsets and offsets within each trial
trial_sounds_df = hu.parse_trial_sounds(
    trial_start_times, 
    sound_reader, 
    bin_sound_path
)
trials_df = pd.concat([trials_df, trial_sounds_df], axis=1)

# -----------------------------------------------------------------------------
# Section 3: Save trials_df as pickle file
# -----------------------------------------------------------------------------

session_output_dir = os.path.join(output_root_dir, animal_ID, session_ID)
if not os.path.exists(session_output_dir):
    os.makedirs(session_output_dir)
filename = animal_ID + '_' + session_ID + '_trial_data_harp.pkl'
trials_df.to_pickle(os.path.join(session_output_dir, filename))