# Import main libraries and define data folder
import harp
import os
import timestamps.harp.utils as hu
import pandas as pd

#==============================================================================

# Choose example session to analyze
animal_ID = 'FNT099'
session_ID = '2024-05-13T11-03-59'
session_ID = '2024-05-17T10-12-40'

# path raw data on Ceph
raw_data_dir = "W:\\projects\\FlexiVexi\\raw_data"

#==============================================================================

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

# Path to Bonsai .csv file with trial-level information
trial_info_path = os.path.join(
    raw_data_dir,
    animal_ID,
    session_ID,
    "Experimental-data",
    "trial_info.csv"
)

# Specify mapping from sound index to reward port 
# (This shouldn't change unless you reprogram the sound card!)
soundIdx0 = 14
soundIdx1 = 10
soundOffIdx = 18

# Output folder to save intermediate variables (Use session folder in raw data 
# directory)
session_output_folder = os.path.join(
    raw_data_dir, 
    animal_ID, 
    session_ID, 
    "harp_data"
)
if not os.path.exists(session_output_folder):
    os.makedirs(session_output_folder)

#==============================================================================
# Save poke events data frame as .csv
#==============================================================================

# Read in harp binaries to get poke events data frame
poke_events = hu.get_all_pokes(behavior_reader)

# Save poke events data frame as .csv
poke_events_filename = animal_ID + '_' + session_ID + '_' + 'poke_events.csv'
poke_events_filepath = os.path.join(session_output_folder, poke_events_filename)
poke_events.to_csv(poke_events_filepath)

#==============================================================================
# Save Photodiode data Series as .csv
#==============================================================================

# Read in harp binaries to get photodiode data series
photodiode_data = hu.get_photodiode_data(behavior_reader)

# Save photodiode data series as .csv
photodiode_filename = animal_ID + '_' + session_ID + '_' + 'photodiode_data.csv'
photodiode_filepath = os.path.join(session_output_folder, photodiode_filename)
photodiode_data.to_csv(photodiode_filepath)

#==============================================================================
# Save sound events data frame as .csv
#==============================================================================

# Read the harp sound card stream, for the timestamps and audio ID
sound_events = hu.get_all_sounds(bin_sound_path)

# save sound events data frame as .csv
sound_filename = animal_ID + '_' + session_ID + '_' + 'sound_events.csv'
sound_filepath = os.path.join(session_output_folder, sound_filename)
sound_events.to_csv(sound_filepath, index=False)

#==============================================================================
# Save Bonsai-triggered event timestamps as .csv
#==============================================================================
# NOTE: This is necessary for constructing trial information data frame 
# downstream.

def get_experimental_data(root_dir):
    """
    Recursively searches for the 'experimental-data.csv' file within the given root directory.

    Args:
        root_dir (str): The root directory to start the search from.

    Returns:
        str: The full path to the 'experimental-data.csv' file if found, otherwise None.
    """
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith("experimental-data.csv"):
                return os.path.join(root, file)

# Import behavioral data as data frame
experimental_data_filepath = get_experimental_data(
    os.path.join(
        raw_data_dir, 
        animal_ID, 
        session_ID
    )
)
trials_df = pd.read_csv(experimental_data_filepath)