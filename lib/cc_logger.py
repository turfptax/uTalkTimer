import os
import time

class Logger:
    def __init__(self, log_dir="logs"):
        print('Example Usage: logger.log_event("2024-05-29T10:00:00Z", "session_start", "Session started")')
        self.log_dir = log_dir
        self.filename = self.get_new_log_filename()

        if self.log_dir not in os.listdir() :
            os.mkdir(self.log_dir)

        with open(self.filename, "w") as file:
            file.write("timestamp,event_type,details\n")  # Write CSV header

    def get_new_log_filename(self):
        # List all files in the log directory
        files = os.listdir(self.log_dir)
        log_files = [f for f in files if f.startswith("log_") and f.endswith(".csv")]

        # Determine the new log file number
        if log_files:
            log_numbers = [int(f[4:-4]) for f in log_files]
            new_log_number = max(log_numbers) + 1
        else:
            new_log_number = 1

        return "{}/log_{}.csv".format(self.log_dir, new_log_number)

    def log_event(self,event_type, details):
        print(f"Logging Event Type: {event_type} Details: {details}")
        with open(self.filename, "a") as file:
            file.write("{},{},{}\n".format(time.time(), event_type, details))

# Example usage:
#logger = Logger()

# Logging events
#logger.log_event("2024-05-29T10:00:00Z", "session_start", "Session started")
#logger.log_event("2024-05-29T10:05:00Z", "speaker_start", "Alice starts speaking")
#logger.log_event("2024-05-29T10:15:00Z", "speaker_end", "Alice stops speaking")
