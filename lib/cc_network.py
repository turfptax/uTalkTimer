import network
import aioespnow
import asyncio
import time

class Network:
    def __init__(self, menu):
        self.wlan = network.WLAN(network.STA_IF)
        self.e = aioespnow.AIOESPNow()
        self.start_time = time.time()
        self.last_update = self.start_time
        self.adjustment_time = 0.0
        self.menu = menu
        self.peers = {}
        self.mac_to_name = {
            b'\xec\xda;3Y\xb8': 'David',
            b'\xab\xcd\xef\x12\x34\x56': 'Tory'
            # Add more mappings here
        }
        self.state = 'inactive'
        self.queue = []
        self.device_mac = self.wlan.config('mac')
        self.session_ledger = []  # Initialize the session ledger

    def setup(self):
        self.wlan.active(True)
        self.e.active(True)
        time.sleep(1)
        self.add_broadcast_peer()

    def add_broadcast_peer(self):
        try:
            self.e.add_peer(b'\xff' * 6)
        except Exception as e:
            if 'ESP_ERR_ESPNOW_EXIST' not in str(e):
                print(f"Error adding broadcast peer: {e}")

    def add_peer(self, mac):
        try:
            self.e.add_peer(mac)
        except Exception as e:
            if 'ESP_ERR_ESPNOW_EXIST' not in str(e):
                print(f"Error adding peer: {e}")

    async def send(self, peer, msg):
        await self.e.asend(peer, msg)

    async def broadcast(self, msg):
        await self.send(b'\xff' * 6, msg)

    async def receiver(self):
        async for mac, msg in self.e:
            print("Received:", msg)
            self.update_peer_list(mac)
            await self.process_message(mac, msg)

    async def process_message(self, mac, msg):
        print(f"Processing message from {mac}: {msg}")
        if msg == b'RECV':
            return
        self.add_peer(mac)  # Ensure the peer is added before sending a response
        try:
            await self.send(mac, b'RECV')
        except OSError as e:
            print(f"Error sending RECV to {mac}: {e}")
        msg_str = msg.decode('utf-8')
        print(f"Decoded message: {msg_str}")
        if msg_str.startswith('STATUS:'): #------------------ STATUS
            self.update_status(msg_str[7:])
        elif msg_str.startswith('VOTE:'): #------------------ VOTE
            self.handle_vote(msg_str[5:])
        elif msg_str.startswith('SET_NAME:'):
            parts = msg_str.split(',')
            if len(parts) == 2:
                try:
                    self.mac_to_name[mac] = parts[1]
                    print('added name to mac_to_name')
                except ValueError as e:
                    print(f"Error parsing SET_NAME Packet: {e}")
        elif msg_str.startswith('SESSION_START'): #------------------ SESSION START
            parts = msg_str.split(',')
            print(f"SESSION_START packet received with parts: {parts}")
            if len(parts) == 4:
                try:
                    self.menu.timekeeper.total_session_time = int(parts[1])
                    self.menu.timekeeper.total_time_per_speaker = int(parts[2])
                    
                    self.menu.timekeeper.device_speaker_time_left = int(parts[2])

                    self.menu.timekeeper.calculate_speaker_timer()
                    self.menu.timekeeper.set_device_mode('active_listener')
                
                    self.menu.is_speaker_active = False
                    self.log_event('start_session', mac)
                    print("Status updated to: active_listener")
                    print("Local Values updated for active_listener mode from SESSION_START Packet")
                except ValueError as e:
                    print(f"Error parsing session start packet: {e}")
            else:
                print("SESSION_START packet format is incorrect")
        elif msg_str.startswith('RAISE_HAND'): #------------------ RAISE HAND
            self.log_event('raise_hand', mac)
        elif msg_str.startswith('END_TIME'): #------------------ END TIME
            parts = msg_str.split(',')
            print(f"END_TIME packet received with parts: {parts}")
            if len(parts) == 3:
                try:
                    total_time_left = int(parts[1])
                    total_session_time_left = int(parts[2])
                except ValueError as e:
                    print(f"Error parsing END_TIME packet: {e}")
            else:
                print("END_TIME packet format is incorrect")
        elif msg_str.startswith('NEXT_SPEAKER'):
            print(f"NEXT_SPEAKER packet received: {msg_str}")
            parts = msg_str.split(',')
            next_speaker_mac_str = parts[1]
            next_speaker_mac = bytes.fromhex(next_speaker_mac_str)
            self.menu.timekeeper.total_session_time = int(parts[2])
            print(f"Next speaker MAC: {next_speaker_mac}",f"My MAC: {self.device_mac}")
            if next_speaker_mac == self.device_mac:  # Corrected
                self.menu.timekeeper.calculate_speaker_timer()
                self.menu.timekeeper.set_device_mode('active_speaker')
                self.menu.is_speaker_active = True
                self.log_event('start_speaker', self.device_mac)  # Corrected
                print("This device is the next speaker")
                # Broadcast status update
                status_packet = f'STATUS:active_speaker'.encode()
                await self.broadcast(status_packet)  # Corrected the function call
            else:
                print("This device is not the next speaker")
        elif msg_str.startswith('ADD_TIME'):
            parts = msg_str.split(',')
            print(f"ADD_TIME packet received with parts: {parts}")
            if len(parts) == 2:
                try:
                    added_time = int(parts[1])
                    #self.menu.timekeeper.add_time(added_time)
                    # Have to calculate and check if this person is recipient
                    self.log_event('add_time', mac)
                    print(f"Added time: {added_time}")
                    print("Display updated for added time")
                except ValueError as e:
                    print(f"Error parsing ADD_TIME packet: {e}")
            else:
                print("ADD_TIME packet format is incorrect")

    def log_event(self, event_type, mac, vote_type=None, duration=None, d_name=None):
        timestamp = time.time()
        name = self.mac_to_name.get(mac, mac.hex()) if mac else 'System'
        event = [name, mac, timestamp, event_type]
        if vote_type:
            event.append(vote_type)
        if duration:
            event.append(duration)
        self.session_ledger.append(event)
        print(f"Logged event: {event}")

    def update_peer_list(self, mac):
        if mac not in self.peers:
            self.peers[mac] = self.mac_to_name.get(mac, mac.hex())
    
    def get_peers(self):
        return list(self.peers.values())

    def update_status(self, new_status):
        self.state = new_status
        print(f"Status updated to: {new_status}")
        # Additional logic to update the display/menu based on the new status

    def add_to_queue(self, mac):
        if mac not in self.queue:
            self.queue.append(mac)
        print(f"Queue updated: {self.queue}")

    def handle_vote(self, vote_type):
        print(f"Vote received: {vote_type}")
        self.log_event('vote_add_time', None, vote_type=vote_type)
        # Logic to handle vote types and update the state accordingly

    def request_next_speaker(self):
        print("Requesting next speaker")
        # Broadcast a request for the next speaker
        asyncio.create_task(self.broadcast(b'REQUEST_NEXT_SPEAKER'))

    def respond_next_speaker(self):
        # Determine the next speaker based on the session ledger
        next_speaker = self.get_next_speaker()
        if next_speaker:
            mac = next_speaker[1]
            mac_hex = mac.hex()  # Convert MAC address to hex string
            print(f"Next speaker: {next_speaker[0]}")
            asyncio.create_task(self.broadcast(f'NEXT_SPEAKER:,{mac_hex},{self.menu.timekeeper.total_session_time}'.encode()))

    def get_next_speaker(self):
        # Logic to determine the next speaker from the ledger
        for event in self.session_ledger:
            if event[3] == 'raise_hand':
                return event
        return None
    
    def get_device_mode(self):
        return self.menu.device_mode
    
