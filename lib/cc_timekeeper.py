import time

class Timekeeper:
    def __init__(self):
        self.start_time = time.time()
        self.last_update = time.time()-1
        
        self.total_session_time = 0 # Total Session length usually 60 min
        self.allotted_time_left = 0
        ###self.device_speaker_time_left = 0
        
        self.device_timer = -100 # countown timer for talking turn usually 60 seconds
        self.current_time = 0
        self.allotted_time = 0
        ###self.total_time_per_speaker = 0
        
        self.base_time_slot = 60 # Basse time slot each speaker gets to talk total
        self.base_session_time = 3600 # Base time for the whole session
        ##self.default_timer = 60
        #self.default_session_time = 3600
        
        self.device_mode = 'inactive'
        self.times_spoken = 0
        self.gift = 15 #number of seconds to give (vote add)

    def initialize_timer(self, session_duration, time_per_speaker):
        self.start_time = time.time()
        self.last_update = self.start_time
        self.total_session_time = session_duration
        self.allotted_time = time_per_speaker
        self.allotted_time_left = time_per_speaker

    def update_time(self):
        current_time = time.time()
        self.last_update = current_time

    def reduce_time_left(self):
        elapsed_time = time.time()-self.last_update
        self.total_session_time -= elapsed_time
        self.allotted_time_left -= elapsed_time
        self.device_timer -= elapsed_time
    
    def reduce_session_time(self):
        elapsed_time = time.time()-self.last_update
        self.total_session_time -= elapsed_time
    
    def calculate_speaker_timer(self):
        if self.allotted_time_left > 0:
            if self.allotted_time_left < 60:
                self.device_timer = self.allotted_time_left
            else:
                self.device_timer = self.base_time_slot
                # write code to pull from settings or menu
        print('calculated device timer: ',self.device_timer)
        return self.device_timer
    
    def calculate_speaker_times(self,peers):
        result = int(self.base_session_time/peers)
        self.allotted_time = result
        self.allotted_time_left = result
        return result
    
    def give_time(self):
        if self.allotted_time_left >= self.gift:
            self.allotted_time_left -= self.gift
        else:
            return False
        return self.gift
    
    def add_time(self,amount):
        self.device_timer += amount
        self.self.allotted_time_left += amount
        
    def set_base_session_time(self,amount):
        self.base_session_time = amount
        
    def add_times_spoken(self):
        self.times_spoken += 1
    
    def get_times_spoken(self):
        return self.times_spoken
        
    def set_total_session_time(self,amount):
        self.total_session_time=amount
    
    def set_allotted_time(self,amount):
        self.allotted_time = amount
    
    def set_allotted_time_left(self,amount):
        self.allotted_time_left = amount
    
    def update_allotted_time_left(self,amount):
        self.allotted_time_left += amount

    def set_device_timer(self,amount):
        self.device_timer = amount
    
    def set_device_mode(self,mode):
        if mode == 'active_speaker':
            self.times_spoken += 1
        self.device_mode = mode
    
    def get_device_mode(self):
        return self.device_mode
        
    def get_current_time(self):
        return int(time.time() - self.start_time)

    def get_total_session_time(self):
        return self.total_session_time

    def get_allotted_time(self):
        return self.allotted_time

    def get_allotted_time_left(self):
        return self.allotted_time_left
    
    def get_device_timer(self):
        return self.device_timer
    
    def update_device_timer(self,amount):
        self.device_timer += amount
