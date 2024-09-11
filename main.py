from timestamps.harp.get_harp_timestamps_df import harp_session
from timestamps.OpenEphys.open_ephys_utils import openephys_session

animal_ID = 'FNT103'
session_ID = '2024-08-26T14-37-42'

print(f"Starting analysis of {animal_ID} for session {session_ID}...")

#==============================================================================
# Read in harp and OpenEphys session data
#==============================================================================

harp = harp_session(animal_ID, session_ID)
oe = openephys_session(animal_ID, session_ID)

#==============================================================================
# Check TTLs
#==============================================================================
# NOTE: need to write some automated flag for whether to sync to master clock 
# or not for a given session

# Check TTls from harp exist and look as expected
harp.read_ttl()
harp.plot_ttl(100)

# Check TTls from OpenEphys exist and look as expected
oe.read_TTLs()
oe.plot_TTLs(100)

#==============================================================================
# Sync to master clock
#==============================================================================
# NOTE: need to add an if statement to check that TTLs exist in both harp and
# OpenEphys, and look as expected before syncing

oe.sync_harp_ttls()

# Sync harp data streams to ephys master clock
harp.sound_events['ephys_timestamp'] = oe.tm.get_pxie_timestamp(harp.sound_events['Time'])
harp.poke_events['ephys_timestamp'] = oe.tm.get_pxie_timestamp(harp.poke_events.index)
harp.photodiode_data['ephys_timestamp'] = oe.tm.get_pxie_timestamp(harp.photodiode_data.index)

# Construct a new data frame the same as trials_df but with harp clock 
# timestamps replaced with ephys clock timestamps
trials_df = harp.trials_df
timestamped_variables = [
    'TrialStart', 
    'TrialEnd', 
    'DotOnsetTime', 
    'DotOffsetTime', 
    'AudioCueStart', 
    'AudioCueEnd', 
    'NosepokeInTime'
]
for var in timestamped_variables:
    trials_df[var] = oe.tm.get_pxie_timestamp(trials_df[var])
harp.trials_df_ephys = trials_df

#==============================================================================
# Save intermediate aligned to ephys master clock 
#==============================================================================

# Save harp data and experimental-data .csv in ephys time
harp.save_harp_data_streams()

# Save trials_df with ephys timestamps
harp.save_experiment_csv()

print(f"Finished analysis of {animal_ID} for session {session_ID}.")