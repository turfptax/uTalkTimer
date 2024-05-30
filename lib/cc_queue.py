class Queue:
    def __init__(self):
        self.roster = {}
        # [mac,nice_name,time_left,times_spoke]
        self.queue = []
        self.nice_name = 'nice_name'
        self.current_speaker = False

    def add_to_queue(self,mac,times_spoken):
        self.queue.append([mac,times_spoken,len(self.queue)])
        print(f"Added to queue: [{mac},{times_spoken}]")

    def get_next_speaker(self):
        print('Calculating Next Speaker cc_queue.py')
        print('self.queue',self.queue)
        if self.queue:
            self.queue.sort(key=lambda x: (-x[1],x[2]))# Sort negative middle column (descending) then last column (ascending)
            next_speaker = self.queue.pop(-1)
            print('next_speaker[0] is:',next_speaker[0])
            return next_speaker[0]
        else:
            print('nothing in the q')
            return False
        
    def update_roster(self,mac,attribute,value):
        if not mac in self.roster:
            self.roster[mac]= {attribute:value}
            print(f'Roster First Entry Created For:{mac} Attribute:{attribute} Value:{value}')
        else:
            self.roster[mac][attribute] = value
            print(f'Roster Update For:{mac} Attribute:{attribute} Value:{value}')

    def get_queue(self):
        return self.queue

    def clear_queue(self):
        self.queue = []
        print("Queue cleared")
