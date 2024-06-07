import os
import time

class Logger:
    def __init__(self, log_dir="logs"):
        print('Example Usage: logger.log_event("session_start", "Session started")')
        self.log_dir = log_dir
        self.filename = self.get_new_log_filename()

        if self.log_dir not in os.listdir() :
            os.mkdir(self.log_dir)

        with open(self.filename, "w") as file:
            file.write("timestamp,event_type,details\n")  # Write CSV header
        
        self.cleanup_old_logs()

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

    def log_event(self, event_type, details):
        print(f"Logging Event Type: {event_type} Details: {details}")
        with open(self.filename, "a") as file:
            file.write("{},{},{}\n".format(time.time(), event_type, details))

    def cleanup_old_logs(self):
        # List all files in the log directory
        files = os.listdir(self.log_dir)
        log_files = [f for f in files if f.startswith("log_") and f.endswith(".csv")]

        # If there are more than 10 log files, delete the oldest ones
        if len(log_files) > 10:
            log_files.sort(key=lambda f: int(f[4:-4]))  # Sort by log number
            files_to_delete = log_files[:-10]  # Keep only the last 10 logs

            for f in files_to_delete:
                os.remove("{}/{}".format(self.log_dir, f))
                print(f"Deleted old log file: {f}")

# Example Usage
logger = Logger()
logger.log_event("session_start", "Session started")
