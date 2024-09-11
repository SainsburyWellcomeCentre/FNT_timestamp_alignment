import pandas as pd
import numpy as np
import harp
import os

# -----------------------------------------------------------------------------
# General utils
# -----------------------------------------------------------------------------

# Retrieve trial start times based on either
#  - audio cues (for stage 5), or
#  - dot onset times (for stage 4)
#   NOTE!: depracated as long as we are happy with using TrialStart from 
#   experimental-data.csv for trial start times
def get_trial_start_times(stage, **kwargs):

    """
    Retrieve trial start times based on the specified stage.

    Parameters:
    stage (int): The stage of the trial. Only stages 4 and 5 are supported.
        - Stage 4: Requires 'dot_onset_times' in kwargs.
        - Stage 5: Requires 'bin_sound_path' and 'sound_reader' in kwargs.
    **kwargs: Additional keyword arguments required based on the stage.
        - dot_onset_times (list or array-like): Onset times of dots for stage 4.
        - bin_sound_path (str): Path to the binary sound file for stage 5.
        - sound_reader (callable): Function to read the sound file for stage 5.

    Returns:
    pd.Series: A series of trial start times.

    Raises:
    ValueError: If required arguments for the specified stage are not provided or if an invalid stage is specified.

    Notes:
    - For stage 4, the function directly returns the provided 'dot_onset_times'.
    - For stage 5, the function processes the sound events to derive trial start times.
      It removes events for playing silence and considers the start of each audio cue as the trial start time.
    - There might be a need to introduce a check for trials in stage 5 where the sound starts playing but the trial is not completed. In such cases, the last trial should be discarded.
    """

    if stage == 4:
        dot_onset_times = kwargs.get('dot_onset_times')
        if dot_onset_times is None:
            raise ValueError("Stage 4 requires 'dot_onset_times' argument.")
        # Process dot onset and offset times
        trial_start_times = dot_onset_times
        return trial_start_times

    elif stage == 5:
        bin_sound_path = kwargs.get('bin_sound_path')
        sound_reader = kwargs.get('sound_reader')
        if bin_sound_path is None or sound_reader is None:
            raise ValueError("Stage 5 requires 'bin_sound_path' and 'sound_reader' arguments.")
        # Derive the sound of all audio events
        sound_of_all_audio_events = sound_reader(bin_sound_path)
        print(f"Processing stage 5 with sound_of_all_audio_events: {sound_of_all_audio_events}")
        all_sounds = hu.get_all_sounds(sound_reader, bin_sound_path)
        # remove events for playing silence
        all_sounds = all_sounds[all_sounds['PlaySoundOrFrequency'] != soundOffIdx]
        # take trial start time is the start of each audio (since there is one audio cue per trial)
        trial_start_times = all_sounds['timestamp']
        # NOTE: might need to introduce a check for trials in stage 5 where the sound starts playing 
        # but the trial is not completed. In this case we should discard the last trial.
        return trial_start_times
    else:
        raise ValueError("Invalid stage. Only stages 4 and 5 are supported.")

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
            
# -----------------------------------------------------------------------------
# TTL utils
# -----------------------------------------------------------------------------

# Get a data frame with timestamps of all instances of initiating and 
# terminating a TTL pulse
def get_ttl_state_df(behavior_reader):

  # Get data frame with timestamps of all instances of initiating TTL pulse
    ttl_on  = behavior_reader.OutputSet.read(keep_type=True)['DO2']
    ttl_on = ttl_on[ttl_on==True]
    ttl_on_df = pd.DataFrame({
        'timestamp': ttl_on.index,
        'state': 1
    })

    # Get data frame with timestamps of all instances of terminating a TTL pulse
    ttl_off = behavior_reader.OutputClear.read(keep_type=True)['DO2']
    ttl_off = ttl_off[ttl_off==True]
    ttl_off_df = pd.DataFrame({
        'timestamp': ttl_off.index,
        'state': 0
    })

    # Concatenate data frames into single stream of events describing state of TTL
    ttl_state_df = pd.concat([ttl_on_df,ttl_off_df], ignore_index=True)
    ttl_state_df = ttl_state_df.sort_values(by='timestamp')
    ttl_state_df = ttl_state_df.reset_index(drop=True)
    
    return ttl_state_df

# Get dot onset and offset times given by TTL pulses
def get_dot_times_from_ttl(behavior_reader,t0, return_TTL_state_at_startup = False):
    
    ttl_state_df = get_ttl_state_df(behavior_reader)

    # take first element of ttl_state_df
    ttl_state_0 = ttl_state_df['state'].iloc[0]

    ## Find index of timestamp in ttl_state_df closest to the first dot_onset_time in df_trials
    dot_onset_TTL_idx = (np.abs(ttl_state_df['timestamp'] - t0)).idxmin()

    ## Remove all TTL pulses that occur before the index found above
    ttl_state_df = ttl_state_df.iloc[dot_onset_TTL_idx:]

    ## Remove last rows such that df has a length that is a multiple of 6
    n = len(ttl_state_df) % 6
    ttl_state_df = ttl_state_df.iloc[:-n]
    
    dot_times_ttl = pd.DataFrame({
        'DotOnsetTime_harp_ttl': ttl_state_df['timestamp'].iloc[::6].tolist(),
        'DotOffsetTime_harp_ttl': ttl_state_df['timestamp'].iloc[2::6].tolist()
    })

    # If return_first_dot_onset_TTL_idx is False (default), return only the the dot onset 
    # and offset times
    if not return_TTL_state_at_startup:
        return(dot_times_ttl)
    
    # If return_first_dot_onset_TTL_idx is True, return both the dot onset and offset 
    # times and the state of ttl_state_df upon start-up
    #  (i)  if ttl_state_0 == 0, there is no TTL pulse upon start-up
    #  (ii) if ttl_state_0 == 1, there is a TTL pulse upon start-up
    elif return_TTL_state_at_startup:
        return(dot_times_ttl, ttl_state_0)

# -----------------------------------------------------------------------------
# Nose poke utils
# -----------------------------------------------------------------------------

# Get a data frame 'all_pokes' with the timestamp of all nosepoke events in the 
# behavior harp stream. This includes the timestamps and IDs of entering and 
# exiting a nose port, denoted by True and False, respectively.

def get_all_pokes(behavior_reader, ignore_dummy_port=True):

    # Read the behavior harp stream, Digital Input states for the nosepoke 
    # timestamps and IDs.
    all_pokes = behavior_reader.DigitalInputState.read()

    if ignore_dummy_port:

        # Remove all nose pokes to dummy port (DI3) and empty data stream DIPort2
        all_pokes.drop(columns=['DI3','DIPort2'],inplace = True) 
    else:
        # Remove empty data stream DIPort2
        all_pokes.drop(columns=['DIPort2'],inplace = True)

    return all_pokes

# Parse all pokes within a trial
def parse_trial_pokes(trial_start_times, poke_events):

    """
    Parses nose poke events within each trial and returns a DataFrame with the results 
    where each row gives the timestamps and port ID of all nosepokes which occured within 
    that trial.

    Args:
        trial_start_times (pd.Series): Series of trial start times.
        poke_events (pd.DataFrame): columns:
            - Time: Timestamp of the event.
            - DIPort0: Boolean in which a value changing from false to true indicates a 
            nose poke into port 0, and vice versa indicates a nosepoke out of port 0.
            - DIPort1: Boolean in which a value changing from false to true indicates a 
            nose poke into port 1, and vice versa indicates a nosepoke out of port 1.

    Returns:
        pd.DataFrame: DataFrame containing nose poke events for each trial.
    """
    num_trials = len(trial_start_times)
    NosePokeIn = [[] for _ in range(num_trials)]
    NosePokeOut = [[] for _ in range(num_trials)]
    PortID = [[] for _ in range(num_trials)]
    NumPokes = [0] * num_trials

    # Iterate through trial start times and extract data from harp stream
    for i, start_time in enumerate(trial_start_times):
        if i < num_trials - 1:
            end_time = trial_start_times[i + 1]
        else:
            end_time = start_time + 100  # 100 seconds after the last trial start time

        # Extract events that occur within the time range of this trial
        trial_events = poke_events[(poke_events.index >= start_time) & (poke_events.index <= end_time)]

        # Create lists for nose pokes within trial
        NosePokeIn_trial, NosePokeOut_trial, PortID_trial = [], [], []

        for _, nosePokeEvent in trial_events.iterrows():
            # Get the timestamp of the event (either a nose poke in or out of a port)
            event_time = nosePokeEvent.name

            # Nose poke into port 0
            if nosePokeEvent.DIPort0:
                NosePokeIn_trial.append(event_time)
                PortID_trial.append(0)

            # Nose poke into port 1
            elif nosePokeEvent.DIPort1:
                NosePokeIn_trial.append(event_time)
                PortID_trial.append(1)

            # Nose poke out of port 0 or port 1
            elif not nosePokeEvent.DIPort0 and not nosePokeEvent.DIPort1:
                NosePokeOut_trial.append(event_time)

        NosePokeIn[i] = NosePokeIn_trial
        NosePokeOut[i] = NosePokeOut_trial
        PortID[i] = PortID_trial
        NumPokes[i] = len(NosePokeIn_trial)

    trial_pokes_df = pd.DataFrame({
        'NosePokeIn': NosePokeIn,
        'NosePokeOut': NosePokeOut,
        'PortID': PortID,
        'NumPokes': NumPokes
    })

    return trial_pokes_df

# Get a data frame with port choice timestamp of port choice for each trial in 
# trials_df.
def get_port_choice(trials_df, behavior_reader):

    """
    Get a data frame with information about port choice for each trial in trials_df, with collumns:
    - ChoicePort: 0 if port 0 was chosen, 1 if port 1 was chosen, -1 if trial was aborted.
    - ChoiceTimestamp: The timestamp of the first nosepoke within the response window (NaN in aborted trials).

    Parameters:
    - trials_df (DataFrame): DataFrame containing trial information.
    - behavior_reader (callable): Used to read the behavior harp stream (obtained using harp.create_reader('path/to/harp/binary/files')).

    Returns:
    - DataFrame: DataFrame with additional columns 'ChoicePort' and 'ChoiceTimestamp', where each row corresponds to a trial in trials_df, 
        where 'ChoicePort' indicates the port choice (0 or 1 for ports 0 and 1, and -1 when the mouse did not choose a port) and 
        'ChoiceTimestamp' indicates the timestamp of the first nosepoke within the response window.
    """

    all_pokes = get_all_pokes(behavior_reader)

    # Flag all trials for which 'TrialCompletionCode' contains the string 'Aborted' or 'DotTimeLimitReached' as aborted
    AbortTrial = trials_df['TrialCompletionCode'].str.contains('Aborted|DotTimeLimitReached')
    completed_trials = ~AbortTrial

    # Pre-index ChoicePort and NosepokeInTime_harp
    ChoicePort = np.full(trials_df.shape[0], -1, dtype=int)  # Initialize with -1 to represent aborted trials
    ChoiceTimestamp = np.full(trials_df.shape[0],np.nan)

    # Get timestamp of first nose poke in response window of non-aborted trials)
    for trial, row in trials_df.iterrows():
        if completed_trials[trial]: # Skip aborted trials
            # Define start of response window as dot offset time
            response_window_start = row['DotOffsetTime_harp_ttl']
            
            # Define trial end as simultaneous with the start of the next trial
            # NOTE: # if last trial, take first response in 10s window after dot offset
            if trial == trials_df.shape[0]-1: 
                trial_end = trials_df.loc[trial, 'DotOnsetTime_harp_ttl']+100
            else:
                trial_end = trials_df.loc[trial+1, 'DotOnsetTime_harp_ttl'] 

            # Get all pokes in each trial between start of response window and trial end
            trial_pokes = all_pokes[(all_pokes.index >= response_window_start) & (all_pokes.index <= trial_end)]

            if not trial_pokes.empty:
                first_poke = trial_pokes.iloc[0]
                # mark choice port row t with 0 = left, 1 = right)
                ChoicePort[trial] = (0 if first_poke['DIPort0'] else 1)
                ChoiceTimestamp[trial] = first_poke.name
            else:
                Warning('No nosepoke detected in trial ' + str(trial))

    # Convert numpy arrays to pandas Series
    ChoicePort = pd.Series(ChoicePort, name='ChoicePort')
    ChoiceTimestamp = pd.Series(ChoiceTimestamp, name='ChoiceTimestamp')

    # Create data frame with port choice information
    port_choice_df = pd.concat([ChoicePort, ChoiceTimestamp], axis=1)
    
    return port_choice_df

# -----------------------------------------------------------------------------
# Sound card utils
# -----------------------------------------------------------------------------

def get_all_sounds(bin_sound_path):
    
    # the explicitly defined model will be deprecated or redundant in future
    model = harp.model.Model(
        device='Soundcard',
        whoAmI=1280,
        firmwareVersion='2.2',
        hardwareTargets='1.1',
        registers={
            'PlaySoundOrFrequency': harp.model.Register(
                address=32,
                type="U16",
                access=harp.model.Access.Event
            )
        }
    )    
    sound_reader = harp.create_reader(model, keep_type=True)

    # Read the harp sound card stream, for the timestamps and audio ID
    all_sounds = sound_reader.PlaySoundOrFrequency.read(bin_sound_path)

    # Filter to only keep events (when sound actually happened, not write commands to the board) 
    all_sounds = all_sounds.loc[all_sounds['MessageType'] == 'EVENT']

    # Drop columns that are not needed
    all_sounds.drop(columns=['MessageType'], inplace=True)
    # Reset index
    all_sounds.reset_index(inplace=True)

    return all_sounds

def parse_trial_sounds(trial_start_times, sound_events, OFF_index=18):

    # Create lists to store the poke IDs and timestamps for all trials
    ON_S, OFF_S, ID_S = [], [], []

    # Iterate through trial start times and extract data from harp stream
    for i, start_time in enumerate(trial_start_times):
        if i < len(trial_start_times) - 1:
            end_time = trial_start_times[i + 1]
        else:
            end_time = start_time + 100  # 100 seconds after the last trial start time

        # Extract events that occur within the time range of this trial
        trial_events = sound_events[(sound_events.Time >= start_time) & (sound_events.Time <= end_time)]

        # Create trial lists for sounds this trial
        ON, OFF, ID = [], [], []
        for _, sound in trial_events.iterrows():
            event_time = sound.Time
            sound = sound[['PlaySoundOrFrequency']]
            sound = int(sound.iloc[0])

            # Find audio IDs from the value. Only find ID for OFFSET
            if sound != OFF_index:
                ON.append(event_time)
                ID.append(sound)
            else:
                OFF.append(event_time)

        ON_S.append(ON)
        OFF_S.append(OFF)
        ID_S.append(ID)
        
    trial_sounds_df = pd.DataFrame({'AudioCueStartTimes': ON_S, 'AudioCueEndTimes': OFF_S, 'AudioCueIdentities': ID_S})  # Create dataframe from all nosepoke events

    return trial_sounds_df

# -----------------------------------------------------------------------------
# Photodiode utils
# -----------------------------------------------------------------------------

def get_photodiode_data(behavior_reader):
    
    # Grab photodiode data
    photodiode_data = behavior_reader.AnalogData.read()

    # Keep only Time and AnalogInput0 columns
    photodiode_data = pd.DataFrame(photodiode_data['AnalogInput0'])

    return photodiode_data