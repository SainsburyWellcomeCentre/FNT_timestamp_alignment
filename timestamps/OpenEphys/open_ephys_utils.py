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


# Get the path of the record node under root_folder
def get_record_node_path(root_folder):
    # Traverse the directory tree
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Check if 'settings.xml' is in the current directory
        if 'settings.xml' in filenames:
            return dirpath
    return None

# Get path to recording session under root_folder
def get_session_path(root_folder):
    # Traverse the directory tree
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Check if any file ends with 'settings.xml'
        for filename in filenames:
            if filename.endswith('settings.xml'):
                # Get the folder one level up
                session_path = os.path.dirname(dirpath)
                return session_path
    return None

class openephys_session():

    def __init__(self, animal_ID, session_ID):

        self.animal_ID = animal_ID
        self.session_ID =  session_ID

        session_folder = INPUT / animal_ID / session_ID
        ephys_session_path = get_session_path(session_folder)

        self.session = Session(ephys_session_path)
        print(self.session)

        self.recording = self.session.recordnodes[0].recordings[0]

        mousepath = OUTPUT / animal_ID
        mousepath.mkdir(exist_ok = True)

        sesspath = mousepath / session_ID
        sesspath.mkdir(exist_ok = True)

        self.sesspath = sesspath

    def read_TTLs(self):

        self.sync_data()

        self.recording.compute_global_timestamps(overwrite=False)
        event_df = self.recording.events
        TTL_pulses = event_df[(event_df['stream_name'] == 'PXIe-6341') & (event_df['line'] == 4)]
        TTL_pulses = TTL_pulses.reset_index(drop=True)
        self.TTL_pulses = TTL_pulses

    def sync_data(self):

                # Sync line corresponding to heartbeat signal of ephys clock (1 pulse per second of duration 0.5 seconds). 
        # Use this as the master clock (set main = True).
        self.recording.add_sync_line(1,                          # 'Heartbeat' signal line number
                                100,                        # processor ID
                                'ProbeA',                   # stream name
                                main=True)                  # use as the main stream


        # Sync line corresponding to TTL pulses
        self.recording.add_sync_line(1,                          # TTL line number
                                102,                        # processor ID
                                'PXIe-6341',                # stream name
                                main=False)                 # synchronize to main stream

    def  plot_TTLs(self):
        fig, ax = plt.subplots()
        ax.plot(self.TTL_pulses['timestamp'], self.TTL_pulses['state'])
        ax.set_xlim(0, 100)
        ax.set_xlabel('Timestamp (s)')
        ax.set_ylabel('TTL in PXIe board')
        fig.suptitle(f'{self.animal_ID},{self.session_ID}')
        fig.savefig(self.sesspath / 'TTLs_PXIe_board.png')
    
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



        


