from lib import cc_display, cc_buzz, cc_network, cc_menu
import json
import uasyncio as asyncio
import time

def load_settings():
    with open('config/settings.json') as f:
        return json.load(f)

def save_settings(settings):
    with open('config/settings.json', 'w') as f:
        json.dump(settings, f)

async def main_loop(display, buzz, network, menu):
    start_time = time.time()
    while True:
        current_time = int(time.time() - start_time)
        num_peers = len(list(network.get_peers()))
        
        if menu.device_mode == 'active_speaker':
            if menu.speaker_timer > 0:
                menu.speaker_timer -= 1
            else:
                # End the current speaker's time and move to the next
                await menu.end_time()

        queue_status = network.get_queue_status(menu.speaker_timer)
        display.update(menu.device_mode, current_time, num_peers, menu.speaker_timer, menu.total_session_time, invert=(menu.speaker_timer < 0), menu_items=menu.menus[menu.current_menu], current_selection=menu.current_selection, queue_status=queue_status)
        buzz.update()
        await asyncio.sleep(1)  # Update every second

async def main():
    settings = load_settings()
    
    # Initialize components
    display = cc_display.Display()
    buzz = cc_buzz.Buzz()
    network = cc_network.Network()
    menu = cc_menu.Menu(display, network, settings)

    # Setup network and buttons
    network.setup()
    menu.setup_buttons()

    # Create and run tasks
    tasks = [
        asyncio.create_task(main_loop(display, buzz, network, menu)),
        asyncio.create_task(network.receiver())  # Assuming receiver is an async function
    ]
    
    await asyncio.gather(*tasks)

def run():
    asyncio.run(main())
