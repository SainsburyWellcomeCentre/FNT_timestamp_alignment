# Flexible Navigation Task Timestamp Alignment Pipeline

Pipeline for checking TTL pulses and aligning harp timestamps and ephys timestamps to a single master clock. The outputs should be saved as intermediate variables which can be read from the ephys postprocessing pipeline (https://github.com/SainsburyWellcomeCentre/FNT_ephys_postprocessing).

## Package Contents
 
### Main Pipeline

An end-to-end pipeline which accepts raw outputs from Bonsai and harp binary files and returns plots and diagnostic information on TTL pulses. 

Assuming the session has ephys data in which the TTL pulses exist and work as expected, it also returns: 
- Three .csv files containing harp data streams (sound events, poke events, photodiode signal) with both harp and ephys timestamps. 
- A .csv file containing the same data as the input (experimental-data.csv), but with all timestamps transformed from harp to   ephys time.

#### Inputs

The inputs can be found within the session folder (containing all raw data for a single session), under {Raw Data Directory} / {Animal ID} / {Session ID}, for a specified animal and session ID.

- **Behavior.harp**, containing harp binary files with information on:
    - harp timestamps of nose pokes in and out of ports
    - raw signal from photodiode, timestamped in harp time.
- **Sounds.harp**, containing timestamps of sound card events (saved in "SoundCard_32.bin")
- **Experimental-data**, containing experimental-data.csv which describes all key Bonsai-triggered events, with the following columns:
    - TrialNumber: Trial number from session start (Note: currently there is a bug that starts trial number at 2!)
    - TrialStart: Timestamp of Bonsai event triggering the start of the trial
    - TrialEnd: Timestamp of Bonsai event triggering the end of the trial
    - TrainingStage, TrainingSubstage: Stage and substage of the session. For full documentation on training stages, see repo containing Bonsai workflow (https://github.com/SainsburyWellcomeCentre/flexible-navigation-task).
    - TrialCompletionCode: A string specifying the outcome of the trial (Whether it was rewarded or aborted, and the choice of port).
    - DotXLocation, DotYLocation: The X and Y locations of the dot projected into the arena for that trial.
    - DotOnsetTime, DotOffsetTime: Timestamps of Bonsai events trigger dot onset/ offset times.
    - AudioCueIdentity: The identity of the audio cue played for that trial. The identity for a givn 
    - AudioCueOnsetTime, AudioCueOffsetTime: Timestamp of Bonsai event triggering the last instance of an audio cue onset/ offset within the trial.

#### Outputs

- **poke_events.csv**: A .csv with the timestamps of all nose poke events recorded in ports 0 and 1, with columns: 
    - Time: timestamp of poke events in port 0 (DIPort0) and 1 (DIport1). 
    - ephys_timestamp: 
    - DIPort0: true or false values indicating the status of port 0, where true indicates a nose poke in and false indicates a nose poke out.
    - DIPort1: true or false values indicating the status of port 1, where a switch from true to false indicates a nose poke in or out of port 1 respectively.
    
- **photodiode_data.csv**: A .csv file with two columns: 
    - Time: timestamp of analog signal in the harp clock.
    - ephys_timestamp: timestamp of analog signal in the ephys clock.
    - AnalogInput0: analogue signal (AnalogueInput0) from the photodiode.

- **audio_events.csv**: A data frame with all audio events which occur whenever a message is sent to the sound card to play an audio file, with the columns:  
    - Time: timestamp of audio events in the harp clock.
    - ephys_timestamp: timestamp of audio events in the ephys clock.
    - PlaySoundOrFrequency: specifies the index on which the audio file was set, where 14 indicates the audio cue for port 0, 10 indicates the audio cue for port 1 and 18 indicates an audio file for silence.  

Note that there are no event "onsets" and "offsets" as with the poke events, but rather a continuous stream of events, with audio onsets indicated by the onset of silence!

- **experimental-data_ephys-timestamps.csv**: A .csv file containing the identical data and column names original data (experimental-data.csv), but with all timestamps transformed from the harp to the ephys clock, including:
    - TrialStart
    - TrialEnd
    - DotOnsetTime
    - DotOffsetTime
    - AudioCueOnsetTime
    - AudioCueOffsetTime

### Examples

- `extract_harp_data_streams.ipynb`: a Python notebook showing how binary files can be read into python (using the harp Python environment) to create data frames (which can subsequently be saved as .csv files in the main pipeline)
- `align_harp_to_ephys_master_clock.ipynb`: a Python notebook showing how to align timestamps to a common clock, including:
    - Using the "heartbeat signal" in the ephys clock to correct for any dropped frames in the neuropixels data.
    - Reading in and plotting the TTLs from the harp and ephys data streams
    - Using this to align timestamps to a common clock

## User guide

To run the code, you need to first install this Github repository locally, and then create an environment from the local repository.

### Installation

For easy installation, open git bash and navigate to the directory in which you would like to download this git repository with ```cd <directory_path>```. 

You can now locally clone this repository by entering the following into your terminal window:
```
git clone https://github.com/m-lockwood/FNT_timestamp_alignment.git
```

You can now stay up-to-date with this branch by using ```git pull``` in the terminal (while in the repository directory).

### Environment

We will use a `requirements` file to make it work cross-platform. Consider freezing versions. 

With the repo directory as your current directory:
```
conda create -n timestamp_alignment python=3.10.14
conda activate timestamp_alignment
pip install -e .
```

### Usage

To run the main pipeline, you need to first specify the following variables:
- **Animal and Session ID**: These can be specified at the top of `main.py`.
- **Raw data (root) directory**: Root folder under which all raw data from experiment is saved. This must contain data with the file structure {Raw Data Directory} / {Animal ID} / {Session ID}, and can be specified at the top of `get_harp_timestamps.py` and `open_ephys_utils.py` as `RAW_DATA_ROOT_DIR`
- **Output (root) directory**: Root folder in which all outputs should be saved. Can be specified at the top of `get_harp_timestamps.py` and `open_ephys_utils.py` as `OUTPUT_ROOT_DIR`.

You can now run `main.py` to produce the necessary outputs (specified above), which can be used in subsequent analysis (https://github.com/SainsburyWellcomeCentre/FNT_ephys_postprocessing).

NOTE: Currently the pipeline can only run all the way through on sessions with TTls present in both the ephys and harp data streams. In future versions of the pipeline, `main.py` should iterate through all sessions and if the TTLs cannot used to transform harp timestamps to ephys timestamps, the code should output all 3 harp .csvs in harp time. 