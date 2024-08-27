from timestamps.harp.get_harp_timestamps_df import harp_session
from timestamps.OpenEphys.open_ephys_utils import openephys_session

animal_ID = 'FNT103'
session_ID = '2024-08-26T14-37-42'
#animal_ID = 'FNT104'
#session_ID = '2024-06-12T09-37-41'

harp = harp_session(animal_ID, session_ID)
harp.read_ttl()
harp.plot_ttl(100)

oe = openephys_session(animal_ID, session_ID)
oe.read_TTLs()
oe.plot_TTLs()
oe.sync_harp_ttls()

