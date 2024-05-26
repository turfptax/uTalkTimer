from lib import cc_display, cc_buzz, cc_network, cc_menu
import json
import asyncio
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
        num_peers = len(network.e.get_peers())
        menu.update()
        display.update(current_time, num_peers)
        buzz.update()
        await asyncio.sleep(0.1)  # Adjust the sleep duration as needed

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
