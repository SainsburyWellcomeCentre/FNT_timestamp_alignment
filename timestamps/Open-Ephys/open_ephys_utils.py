import os
from pathlib import Path
from open_ephys.analysis import Session


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

        self.recording.compute_global_timestamps(overwrite=False)
        event_df = self.recording.events
        TTL_pulses = event_df[(event_df['stream_name'] == 'PXIe-6341') & (event_df['line'] == 4)]
        TTL_pulses = TTL_pulses.reset_index(drop=True)
        self.TTL_pulses = TTL_pulses