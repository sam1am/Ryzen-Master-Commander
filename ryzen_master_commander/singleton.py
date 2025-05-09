import os
import sys
import fcntl
import tempfile

class SingleInstance:
    """
    Ensures only a single instance of the application runs at a time.
    """
    def __init__(self, app_name):
        self.app_name = app_name
        self.lockfile = os.path.join(tempfile.gettempdir(), f'{app_name}.lock')
        self.lock_handle = None
        
        # Try to get an exclusive lock on the file
        try:
            self.lock_handle = open(self.lockfile, 'w')
            fcntl.lockf(self.lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Another instance exists
            print(f"Another instance of {app_name} is already running.")
            sys.exit(1)
            
    def __del__(self):
        if self.lock_handle:
            fcntl.lockf(self.lock_handle, fcntl.LOCK_UN)
            self.lock_handle.close()
            try:
                os.unlink(self.lockfile)
            except:
                pass