import os
from pathlib import Path
from open_ephys.analysis import Session
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle


# path behavioural data on Ceph repo
INPUT = Path("/ceph/sjones/projects/FlexiVexi/behavioural_data/")
OUTPUT = Path("/ceph/sjones/projects/FlexiVexi/Data Analysis/intermediate_variables")

# Get path to Open-Ephys recording
def get_record_node_path(root_folder):
    """
    Traverse the directory tree starting from the root_folder to find the path
    containing 'settings.xml'. This function returns the path to the directory
    containing 'settings.xml'.

    Parameters:
    root_folder (str or Path): The root directory to start the search. It can be a string or a Path object.

    Returns:
    Path: The path to the directory containing 'settings.xml'. If no such directory is found, it prints 'No recording found' and returns None.
    """
    # If root_folder is Path object
    if isinstance(root_folder, Path):
        # Traverse the directory tree
        for dirpath in root_folder.rglob('*'):
            # Check if 'settings.xml' is in the current directory
            if (dirpath / 'settings.xml').exists():
                return dirpath
        print('No recording found')
    
    # If root_folder is a string
    else: 
        # Traverse the directory tree
        for dirpath, dirnames, filenames in os.walk(root_folder):
            # Check if 'settings.xml' is in the current directory
            if 'settings.xml' in filenames:
                return dirpath
            else:
                print('No recording found')

# Get path to Open-Ephys session
def get_session_path(root_folder):
    """
    Traverse the directory tree starting from the root_folder to find the path
    containing any file that ends with 'settings.xml'. This function returns the
    parent directory of the directory containing 'settings.xml'.

    Parameters:
    root_folder (str or Path): The root directory to start the search. It can be a string or a Path object.

    Returns:
    Path: The parent path of the directory containing 'settings.xml'. If no such directory is found, it prints 'No recording found' and returns None.
    """
    # If root_folder is a Path object
    if isinstance(root_folder, Path): 
        # Traverse the directory tree
        for dirpath in root_folder.rglob('*'):
            # Ensure dirpath is a directory
            if dirpath.is_dir():
                # Check if any file ends with 'settings.xml'
                for file in dirpath.iterdir():
                    if file.is_file() and file.name.endswith('settings.xml'):
                        # Get the folder one level up
                        return dirpath.parent
        print('No recording found')
    
    # If root_folder is a string
    else: 
        # Traverse the directory tree
        folder_one_level_up = None
        for dirpath, dirnames, filenames in os.walk(root_folder):
            # Check if any file ends with 'settings.xml'
            for filename in filenames:
                if filename.endswith('settings.xml'):
                    # Get the folder one level up
                    folder_one_level_up = os.path.dirname(dirpath)
                    return folder_one_level_up
        if folder_one_level_up is None:
            print('No recording found')

class openephys_session():

    def __init__(self, animal_ID, session_ID):

        raw_data_session_dir = os.path.join(RAW_DATA_ROOT_DIR, animal_ID, session_ID)
        output_session_dir = os.path.join(OUTPUT_ROOT_DIR, animal_ID, session_ID)

        # append Animal and Session ID to object
        self.animal_ID = animal_ID
        self.session_ID = session_ID

        # append the raw data and output directories for the session
        self.raw_data_session_dir = raw_data_session_dir
        self.output_session_dir = output_session_dir

        # Get ephys session object
        ephys_session_path = get_session_path(raw_data_session_dir)
        self.session = Session(ephys_session_path)
        print(self.session)

        self.recording = self.session.recordnodes[0].recordings[0]

        # Create output directory for session
        os.makedirs(output_session_dir, exist_ok = True)
    
    def get_PXI_processor_ID(self):
        idx = self.recording.events['stream_name'] == 'PXIe-6341'
        processor_IDs = self.recording.events['processor_id'][idx]
        PXI_processor_ID = int(processor_IDs.unique()[0])        
        return PXI_processor_ID
    
    def read_TTLs(self):

        self.sync_data()

        self.recording.compute_global_timestamps(overwrite=False)
        event_df = self.recording.events
        TTL_pulses = event_df[(event_df['stream_name'] == 'PXIe-6341') & (event_df['line'] == 4)]
        TTL_pulses = TTL_pulses.reset_index(drop=True)
        self.TTL_pulses = TTL_pulses

    def sync_data(self):

        # Get processor ID of PXIe-6341 stream
        PXI_processor_ID = self.get_PXI_processor_ID()

        # Sync line corresponding to heartbeat signal of ephys clock (1 pulse per second of duration 0.5 seconds). 
        # Use this as the master clock (set main = True).
        self.recording.add_sync_line(1,                     # 'Heartbeat' signal line number
                                100,                        # processor ID
                                'ProbeA',                   # stream name
                                main=True)                  # use as the main stream


        # Sync line corresponding to TTL pulses
        self.recording.add_sync_line(4,              # TTL line number
                                PXI_processor_ID,           # processor ID
                                'PXIe-6341',                # stream name
                                main=False)                 # synchronize to main stream

    def plot_TTLs(self, seconds = 20):
        plt.figure(figsize=(12, 6))  # Set the figure size (width, height) in inches
        ttl_pulse = pu.get_square_wave(self.TTL_pulses)
        ttl_pulse.plot(x='timestamp', y='state', linewidth=0.5)
        plt.xlabel('timestamp (s)')
        plt.legend(loc='upper right')
        plt.title("Plot TTL pulses in PXIe board, " + self.session_ID)
        plt.suptitle(f'{self.animal_ID},{self.session_ID}')        
        t0 = ttl_pulse['timestamp'].iloc[0]
        plt.xlim(t0+50, t0+50+seconds)
        plt.savefig(join(self.output_session_dir, 'TTLs_PXIe_board.png'))
    
    def sync_harp_ttls(self):

        #Make  ttl diff to find  onset moments
        ttl_diff = np.zeros_like(self.TTL_pulses['state'])
        ttl_diff[0] = 1 #The first event will always be a rise with  the first pulse
        ttl_diff[1:] = np.diff(self.TTL_pulses['state'])
        self.TTL_pulses['diff'] =  ttl_diff

        #Read harp timestamps
        harp_path = self.sesspath /  'TTLs_harp.csv'
        self.harp_ttl = pd.read_csv(harp_path)

        #Make harp diff
        harp_diff = np.zeros_like(self.harp_ttl['state'])
        harp_diff[0] = 0
        harp_diff[1:] = np.diff(self.harp_ttl['state'])
        self.harp_ttl['diff'] = harp_diff

        harp_onset =  self.harp_ttl[self.harp_ttl['diff']==1]
        pxie_onset = self.TTL_pulses[self.TTL_pulses['diff']==1]

        self.tm = timestamp_mapping(harp_onset, pxie_onset,  self.sesspath)
        self.tm.plot_residuals()

        with open((self.sesspath / 'timestamp_mapping.pkl'), 'wb') as file:
            pickle.dump(self.tm, file)

class timestamp_mapping():
    '''
    Calculates a mapping between harp and pxie timestamps. Will print
    some diagnostic plots and be unpickled  if neccessary to map arbitrary
    harp timestamps.  
    '''
    
    def __init__(self, harp_onset, pxie_onset, sesspath):
        self.sesspath = sesspath
        self.harp_onset = harp_onset
        self.pxie_onset = pxie_onset

        print(f'There are {len(self.harp_onset)} harp rises and {len(self.pxie_onset)} pxie rises')
        if len(self.harp_onset) != len(self.pxie_onset):
            print('CAREFUL! There does not seem to be an equal number of rise events.')

        #Fit the polynomial
        self.fit = np.polynomial.polynomial.Polynomial.fit(harp_onset['timestamp'], pxie_onset['global_timestamp'], 1)
        #Extract intercept and slope
        self.intercept = self.fit.convert().coef[0]
        self.slope = self.fit.convert().coef[1]
    
    def get_pxie_timestamp(self, new_data):
        '''
        Uses the linear fit to return pxie timestamps when given harp timestamps
        '''
        pxie_timestamp = self.fit(new_data)
        return pxie_timestamp
    
    def plot_residuals(self):
        '''
        Calculates and plots the residuals of the  conversion. USeful to check 
        if  there  are any outliers. 
        '''
        self.predicted = self.get_pxie_timestamp(self.harp_onset['timestamp'])
        self.residuals = np.array(self.pxie_onset['global_timestamp']) -  np.array(self.predicted)

        #and plot the stuff
        fig, ax =  plt.subplots()
        ax.hist(self.residuals)
        ax.set_xlabel('Actual-predicted pxie timestamp (s)')
        ax.set_ylabel('Count')
        fig.suptitle('Residuals from harp-pxie timestamp mapping')
        fig.savefig(self.sesspath / 'harp_residuals.png')
        


