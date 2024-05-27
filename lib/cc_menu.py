from machine import Pin
import time
import asyncio

class Menu:
    def __init__(self, display, network, settings):
        self.display = display
        self.network = network
        self.settings = settings
        
        # Define the menu structure
        self.menus = {
            'main': ['Session Settings', 'During Session', 'Device Settings', 'Feedback and Logs', 'Exit'],
            'Session Settings': ['Set Duration', 'Set Participants', 'Start Session', 'Back'],
            'Set Duration': ['30 minutes', '60 minutes', 'Custom', 'Back'],
            'During Session': ['Current Speaker Timer', 'Request to Speak Next', 'End/Pause Session', 'Back'],
            'Device Settings': ['Buzz Notifications', 'Display Brightness', 'Sound Volume', 'Back'],
            'Buzz Notifications': ['Soft Buzz Time', 'Hard Buzz Time', 'Back'],
            'Feedback and Logs': ['View Session Logs', 'Provide Feedback', 'Back']
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
            'Raise Hand': self.raise_hand
        }

        self.current_menu = 'main'
        self.current_selection = 0
        self.device_mode = 'inactive'
        self.speaker_timer = 60  # Default to 1 minute
        self.total_session_time = 0
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

    def handle_menu(self, pin):
        if self.device_mode == 'main_menu':
            self.handle_main_menu(pin)
        elif self.device_mode == 'inactive':
            self.handle_main_menu(pin)  # Use the main menu handler
        elif self.device_mode == 'active_listener':
            self.handle_active_session_listener(pin)
        elif self.device_mode == 'active_speaker':
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

    async def menu_timeout(self):
        await asyncio.sleep(5)  # 5 seconds timeout
        self.device_mode = 'inactive'
        self.current_menu = 'main'
        self.current_selection = 0
        self.display.update_menu(self.menus[self.current_menu], self.current_selection)

    async def vote_to_add_time(self):
        print("Add Time")
        await self.network.broadcast(b'ADD_TIME')
        self.network.log_event('add_time', self.network.device_mac)
        pass

    async def raise_hand(self):
        print("Raise Hand")
        await self.network.broadcast(b'RAISE_HAND')
        self.network.log_event('raise_hand', self.network.device_mac)
        pass

    async def end_time(self):
        print("End Time")
        await self.network.broadcast(b'END_TIME')
        self.network.log_event('end_time', self.network.device_mac)
        self.device_mode = 'active_listener'
        self.network.respond_next_speaker()

    def select_menu_item(self, menu, selection):
        item = self.menus[menu][selection]
        if item == 'Back':
            self.current_menu = 'main'
        elif item in self.menus:
            self.current_menu = item
        else:
            action = self.actions.get(item)
            if action:
                action()

        self.current_selection = 0
        self.display.update_menu(self.menus[self.current_menu], self.current_selection)

    def set_duration(self):
        pass

    def set_participants(self):
        pass

    def start_session(self):
        self.device_mode = 'active_speaker'
        self.speaker_timer = self.settings.get('default_speaker_time', 60)
        self.total_session_time = 0
        self.is_speaker_active = True

    async def set_30_minutes(self):
        self.total_session_time = 30 * 60  # 30 minutes
        self.settings['session_duration'] = self.total_session_time
        self.save_settings()
        await self.network.broadcast(f'SESSION_DURATION:{self.total_session_time}'.encode())
        self.network.log_event('set_duration', self.network.device_mac, duration=self.total_session_time)
        print("Session duration set to 30 minutes")

    async def set_60_minutes(self):
        self.total_session_time = 60 * 60  # 60 minutes
        self.settings['session_duration'] = self.total_session_time
        self.save_settings()
        await self.network.broadcast(f'SESSION_DURATION:{self.total_session_time}'.encode())
        self.network.log_event('set_duration', self.network.device_mac, duration=self.total_session_time)
        print("Session duration set to 60 minutes")
        
    def save_settings(self):
        with open('config/settings.json', 'w') as f:
            json.dump(self.settings, f)

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
