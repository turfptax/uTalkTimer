from lib import cc_display, cc_buzz, cc_network, cc_menu, cc_timekeeper, cc_queue, cc_logger
import json
import uasyncio as asyncio
import time

def load_settings():
    try:
        with open('config/settings.json') as f:
            return json.load(f)
    except (ValueError, OSError) as e:
        print(f"Error loading settings: {e}")
        # Return default settings if there is an error
        return {
            "session_duration": 3600,
            "default_speaker_time": 60,
            "num_participants": 9
        }

def save_settings(settings):
    with open('config/settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

async def main_loop(display, buzz, network, menu, timekeeper):
    while True:
        #current_time = network.get_current_time()
        current_time = timekeeper.get_current_time()
        num_peers = len(list(network.get_peers()))
        timer = timekeeper.get_device_timer()
        device_mode = timekeeper.get_device_mode()
        if device_mode == 'active_speaker':
            if timer > 0:
                timekeeper.reduce_time_left()
                timer = timekeeper.get_device_timer()
                if timer <= 10 and timer > 0:
                    buzz.short_buzz()
                elif timer <= 0:
                    buzz.long_buzz()
                    await menu.end_time()
                # Update the display
                display.update(
                    mode=device_mode,
                    current_time=current_time,
                    num_peers=num_peers,
                    speaker_time=timekeeper.device_timer,
                    total_time=timekeeper.total_session_time,  # Ensure total_time is integer
                    invert=(timekeeper.device_timer < 0),
                    allotted_time_left=timekeeper.allotted_time_left  # Ensure allotted_time_left is integer
                )
                #timekeeper.update_time() # Reset last update time after display update
        else:
            # Session Timer Countdown:
            timer = timekeeper.get_device_timer()
            timekeeper.reduce_session_time()
            # Update display for inactive modes to ensure menu is visible
            total_session_time = timekeeper.get_total_session_time()
            allotted_time = timekeeper.get_allotted_time()
            allotted_time_left = timekeeper.get_allotted_time_left()
            

            # Update display for inactive modes to ensure menu is visible
            display.update(
                mode=device_mode,
                current_time=current_time,
                num_peers=num_peers,
                speaker_time=60,
                total_time=total_session_time,
                menu_items=menu.menus[menu.current_menu],
                current_selection=menu.current_selection,
                allotted_time_left=allotted_time_left
            )
        timekeeper.update_time()
        await asyncio.sleep(1)

async def main():
    settings = load_settings()
    
    # Initialize components
    display = cc_display.Display()
    buzz = cc_buzz.Buzz()
    
    # Setup the timekeeper reference
    timekeeper = cc_timekeeper.Timekeeper()
    queue = cc_queue.Queue()
    logger = cc_logger.Logger()
    
    # Initialize Menu first without the network reference
    menu = cc_menu.Menu(display, None, buzz, settings, timekeeper, queue, logger)
    
    # Initialize Network and pass the menu reference
    network = cc_network.Network(menu)
    
    # Now set the network reference in the menu
    menu.network = network

    # Setup network and buttons
    network.setup()
    menu.setup_buttons()

    # Create and run tasks
    tasks = [
        asyncio.create_task(main_loop(display, buzz, network, menu, timekeeper)),
        asyncio.create_task(network.receiver())  # Assuming receiver is an async function
    ]
    
    await asyncio.gather(*tasks)

def run():
    asyncio.run(main())
