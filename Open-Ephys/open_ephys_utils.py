import os

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