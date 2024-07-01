from machine import Pin
import time
import asyncio
import json

class Menu:
    def __init__(self, display, network,buzz, settings, timekeeper, queue, logger):
        self.timekeeper = timekeeper
        self.display = display
        self.network = network
        self.settings = settings
        self.buzz = buzz
        self.queue = queue
        self.logger = logger
        self.num_participants = settings.get('num_participants', 1)
        
        # List of names
        self.names = ['Ardy', 'BJ', 'David','Jacks', 'Mark',
                      'Rich', 'Sachi', 'Tory', 'Wayne', 'Wes', 'Yahia']
        # Define the menu structure
        self.menus = {
            'main': ['Session', 'During Session', 'Device Settings', 'Feedback & Logs', 'Set Name','Exit'],
            'Session': ['Set Duration', 'Set Participants', 'Start Session', 'Back'],
            'Set Duration': ['30 minutes', '60 minutes', 'Custom', 'Back'],
            'During Session': ['Current Speaker Timer', 'Request to Speak Next', 'End/Pause Session', 'Back'],
            'Device Settings': ['Buzz Notifications', 'Display Brightness', 'Sound Volume', 'Back'],
            'Buzz Notifications': ['Soft Buzz Time', 'Hard Buzz Time', 'Back'],
            'Feedback & Logs': ['View Session Logs', 'Provide Feedback', 'Back'],
            'Set Name': self.names + ['Back']
        }

        # Define the actions dictionary
        self.actions = {
            'Set Duration': self.set_duration,
            'Set Participants': self.set_participants,
            'Start Session': self.start_session,
            '30 minutes': self.set_30_minutes,
            '60 minutes': self.set_60_minutes,
            'Custom': self.set_custom_duration,
            'Current Speaker Timer': self.current_speaker_timer,
            'Request to Speak Next': self.request_to_speak_next,
            'End/Pause Session': self.end_pause_session,
            'Soft Buzz Time': self.set_soft_buzz_time,
            'Hard Buzz Time': self.set_hard_buzz_time,
            'Display Brightness': self.set_display_brightness,
            'Sound Volume': self.set_sound_volume,
            'View Session Logs': self.view_session_logs,
            'Provide Feedback': self.provide_feedback,
            'Ping All': self.ping_all,
            'Raise Hand': self.raise_hand,
            'Set Name': self.set_device_name
        }

        self.current_menu = 'main'
        self.current_selection = 0
        self.device_mode = 'inactive'
        self.device_name = 'noname'
        self.is_speaker_active = False
        
        self.button1 = Pin(4, Pin.IN, Pin.PULL_UP)
        self.button2 = Pin(5, Pin.IN, Pin.PULL_UP)
        self.button3 = Pin(6, Pin.IN, Pin.PULL_UP)
        self.last_interrupt_time = 0
        self.menu_timeout_task = None

    def setup_buttons(self):
        self.button1.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        self.button2.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        self.button3.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        print("Button interrupts set up")

    def button_handler(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_interrupt_time) > 400:  # Debounce period of 400 ms
            self.last_interrupt_time = current_time
            self.handle_menu(pin)
            
    def calculate_allotted_time(self):
        self.total_session_time = self.settings.get('session_duration', 3600)  # Default to 1 hour
        num_participants = max(self.settings.get('num_participants', 1), 1)
        print('Num_participants',num_participants)
        print('total_session_time',self.total_session_time)
        if num_participants > 0:
            self.allotted_time = self.total_session_time // num_participants
        else:
            self.allotted_time = 360
        print(f"Calculated total time per speaker: {self.allotted_time} seconds")

    def handle_menu(self, pin):
        if self.device_mode == 'main_menu':
            self.handle_main_menu(pin)
        elif self.timekeeper.device_mode == 'inactive':
            self.handle_main_menu(pin)  # Use the main menu handler
        elif self.timekeeper.device_mode == 'active_listener':
            self.handle_active_session_listener(pin)
        elif self.timekeeper.device_mode == 'active_speaker':
            self.handle_active_session_speaker(pin)

    def handle_main_menu(self, pin):
        menu_items = self.menus[self.current_menu]
        if pin == self.button1:
            self.current_selection = (self.current_selection + 1) % len(menu_items)
        elif pin == self.button3:
            self.current_selection = (self.current_selection - 1) % len(menu_items)
        elif pin == self.button2:
            self.select_menu_item(self.current_menu, self.current_selection)

        self.display.update_menu(menu_items, self.current_selection)

    def handle_active_session_listener(self, pin):
        if pin == self.button1:
            asyncio.create_task(self.vote_to_add_time())
        elif pin == self.button2:
            asyncio.create_task(self.raise_hand())
        elif pin == self.button3:
            self.device_mode = 'main_menu'
            self.current_menu = 'main'
            self.current_selection = 0
            self.menu_timeout_task = asyncio.create_task(self.menu_timeout())

    def handle_active_session_speaker(self, pin):
        if pin == self.button1:
            asyncio.create_task(self.vote_to_add_time())
        elif pin == self.button2:
            asyncio.create_task(self.end_time())
        elif pin == self.button3:
            self.device_mode = 'main_menu'
            self.current_menu = 'main'
            self.current_selection = 0
            self.menu_timeout_task = asyncio.create_task(self.menu_timeout())
            
    async def set_device_name(self, name):
        self.device_name = name
        #self.settings['device_name'] = name
        print(f"Sending SET_NAME packet: SET_NAME:,{self.device_name}")
        self.logger.log_event('set_name', f"This Device:{self.network.device_mac},{name}")
        await self.network.broadcast(f'SET_NAME:,{self.device_name}'.encode())
        self.queue.update_roster(self.network.device_mac,'nice_name',name)
        self.current_menu = 'main'
        self.current_selection = 0

    async def set_30_minutes(self):
        self.timekeeper.set_base_session_time(30 * 60)  # 30 minutes
        session_duration_packet = f'SESSION_DURATION:,{self.timekeeper.base_session_time}'
        await self.network.broadcast(session_duration_packet.encode())
        self.logger.log_event('SET_SESSION_DURATION', session_duration_packet)

    async def set_60_minutes(self):
        self.timekeeper.set_base_session_time(60 * 60)
        session_duration_packet = f'SESSION_DURATION:,{self.timekeeper.base_session_time}'
        await self.network.broadcast(session_duration_packet.encode())
        self.logger.log_event('SET_SESSION_DURATION', session_duration_packet)


    async def start_session(self):
        total_session_time = self.timekeeper.base_session_time
        self.timekeeper.set_total_session_time(self.timekeeper.base_session_time)
        allotted_time = self.timekeeper.calculate_speaker_times(self.num_participants) # Calcualte Better!!!!!
        self.timekeeper.calculate_speaker_timer() # updates timekeeper
        
        session_start_time = time.time()
        session_start_packet = f'SESSION_START,{total_session_time},{allotted_time},{session_start_time}'.encode()
        print('session_start_packet',session_start_packet)
        print(f"Sending SESSION_START packet: {session_start_packet}")
        await self.network.broadcast(session_start_packet)
        self.logger.log_event( "SESSION_START", f"This Device:,{session_start_packet}")
        
        self.timekeeper.set_device_mode('active_speaker') # Change Device Mode and Display Update
        self.is_speaker_active = True
        print(f"-------Session started with duration {total_session_time} seconds-------")
        print(f"------------each speaker gets {allotted_time} seconds-------------------")

    def save_settings(self):
        with open('config/settings.json', 'w') as f:
            json.dump(self.settings, f)

    async def menu_timeout(self):
        await asyncio.sleep(5)  # 5 seconds timeout
        self.device_mode = 'inactive'
        self.current_menu = 'main'
        self.current_selection = 0
        self.display.update_menu(self.menus[self.current_menu], self.current_selection)

    async def vote_to_add_time(self):
        gift = self.timekeeper.give_time()
        if gift:
            add_time_packet = f"ADD_TIME:,{gift},{self.timekeeper.allotted_time_left}"
            await self.network.broadcast(add_time_packet.encode())
            self.logger.log_event('ADD_TIME',self.network.device_mac)
        else:
            print(f"Failed to give gift as gift returned:{gift}")

    async def raise_hand(self):
        print("Raise Hand")
        raise_hand_packet = f"RAISE_HAND:,{self.timekeeper.times_spoken}"
        await self.network.broadcast(raise_hand_packet.encode())
        self.queue.add_to_queue(self.network.device_mac,self.timekeeper.times_spoken)
        self.queue.update_roster(self.network.device_mac,'times_spoken',self.timekeeper.times_spoken)

    async def end_time(self):
        print("End Time")
        end_time_packet = f"END_TIME:,{self.timekeeper.total_session_time},{self.timekeeper.allotted_time_left},{self.timekeeper.times_spoken}"
        await self.network.broadcast(end_time_packet.encode())
        self.logger.log_event('END_TIME',f"This Device:,{self.network.device_mac}")
        #self.network.log_event('end_time', self.network.device_mac)
        self.timekeeper.calculate_speaker_timer()
        self.timekeeper.set_device_mode('active_listener')
        
        self.network.notify_next_speaker()

    def select_menu_item(self, menu, selection):
        item = self.menus[menu][selection]
        if item == 'Back':
            self.current_menu = 'main'
        elif item in self.menus:
            self.current_menu = item
        elif self.current_menu == 'Set Name':
            print('---------------------:',item)
            asyncio.create_task(self.set_device_name(item))
            print('after ------------ set name?')
        else:
            action = self.actions.get(item)
            if action:
                print(f"Executing action for {item}")
                asyncio.create_task(action())

        self.current_selection = 0
        self.display.update_menu(self.menus[self.current_menu], self.current_selection)

    def set_duration(self):
        pass

    def set_participants(self):
        pass

    def set_custom_duration(self):
        pass

    def current_speaker_timer(self):
        pass

    def request_to_speak_next(self):
        pass

    def end_pause_session(self):
        self.device_mode = 'inactive'

    def set_soft_buzz_time(self):
        pass

    def set_hard_buzz_time(self):
        pass

    def set_display_brightness(self):
        pass

    def set_sound_volume(self):
        pass

    def view_session_logs(self):
        pass

    def provide_feedback(self):
        pass

    def ping_all(self):
        pass
