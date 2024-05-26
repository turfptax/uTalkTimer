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
            'main': ['Session Settings', 'During Session', 'Device Settings', 'Feedback and Logs'],
            'Session Settings': ['Set Duration', 'Set Participants', 'Start Session', 'Back'],
            'During Session': ['Current Speaker Timer', 'Request to Speak Next', 'End/Pause Session', 'Back'],
            'Device Settings': ['Buzz Notifications', 'Display Brightness', 'Sound Volume', 'Back'],
            'Buzz Notifications': ['Soft Buzz Time', 'Hard Buzz Time', 'Back'],
            'Feedback and Logs': ['View Session Logs', 'Provide Feedback', 'Back']
        }
        
        self.current_menu = 'main'
        self.current_selection = 0
        
        self.button1 = Pin(4, Pin.IN, Pin.PULL_UP)
        self.button2 = Pin(5, Pin.IN, Pin.PULL_UP)
        self.button3 = Pin(6, Pin.IN, Pin.PULL_UP)
        self.last_interrupt_time = 0

    def setup_buttons(self):
        self.button1.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        self.button2.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        self.button3.irq(trigger=Pin.IRQ_FALLING, handler=self.button_handler)
        print("Button interrupts set up")

    def button_handler(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_interrupt_time) > 400:  # Debounce period of 1200 ms
            self.last_interrupt_time = current_time
            self.handle_menu(pin)

    def handle_menu(self, pin):
        menu_items = self.menus[self.current_menu]
        if pin == self.button1:
            self.current_selection = (self.current_selection + 1) % len(menu_items)
        elif pin == self.button3:
            self.current_selection = (self.current_selection - 1) % len(menu_items)
        elif pin == self.button2:
            self.select_menu_item(self.current_menu, self.current_selection)

        self.display.update_menu(menu_items, self.current_selection)

    def select_menu_item(self, menu, index):
        menu_items = self.menus[menu]
        selected_item = menu_items[index]
        
        if selected_item == 'Back':
            self.current_menu = 'main'
        elif selected_item in self.menus:
            self.current_menu = selected_item
        else:
            # Handle the selection of a specific menu action
            asyncio.create_task(self.handle_action(selected_item))

        self.current_selection = 0

    async def handle_action(self, action):
        if action == 'Ping All':
            await self.network.send(b'\xff' * 6, 'PING-ALL')
        elif action == 'Raise Hand':
            print("Raise Hand")
        elif action == 'Start Timer':
            print("Start Timer")
        elif action == 'Set Duration':
            print("Set Duration")
        elif action == 'Set Participants':
            print("Set Participants")
        elif action == 'Start Session':
            print("Start Session")
        elif action == 'Current Speaker Timer':
            print("Current Speaker Timer")
        elif action == 'Request to Speak Next':
            print("Request to Speak Next")
        elif action == 'End/Pause Session':
            print("End/Pause Session")
        elif action == 'Soft Buzz Time':
            print("Soft Buzz Time")
        elif action == 'Hard Buzz Time':
            print("Hard Buzz Time")
        elif action == 'Display Brightness':
            print("Display Brightness")
        elif action == 'Sound Volume':
            print("Sound Volume")
        elif action == 'View Session Logs':
            print("View Session Logs")
        elif action == 'Provide Feedback':
            print("Provide Feedback")

    def update(self):
        # Update menu if needed
        pass
