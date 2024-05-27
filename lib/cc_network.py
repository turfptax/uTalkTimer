import network
import aioespnow
import asyncio
import time

class Network:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.e = aioespnow.AIOESPNow()
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
        if msg == b'RECV':
            return
        self.add_peer(mac)  # Ensure the peer is added before sending a response
        try:
            await self.send(mac, b'RECV')
        except OSError as e:
            print(f"Error sending RECV to {mac}: {e}")

        # Handle different types of messages here
        if msg.startswith(b'STATUS:'):
            self.update_status(msg[7:].decode())
        elif msg.startswith(b'REQUEST_SPEAK:'):
            self.add_to_queue(mac)
        elif msg.startswith(b'VOTE:'):
            self.handle_vote(msg[5:].decode())
        elif msg == b'SESSION_START':
            self.update_status('active_listener')
            self.log_event('start_session', mac)
        elif msg.startswith(b'RAISE_HAND'):
            self.log_event('raise_hand', mac)

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

    def log_event(self, event_type, mac, vote_type=None, duration=None):
        timestamp = time.time()
        name = self.mac_to_name.get(mac, mac.hex()) if mac else 'System'
        event = [name, mac, timestamp, event_type]
        if vote_type:
            event.append(vote_type)
        if duration:
            event.append(duration)
        self.session_ledger.append(event)
        print(f"Logged event: {event}")

    def request_next_speaker(self):
        print("Requesting next speaker")
        # Broadcast a request for the next speaker
        asyncio.create_task(self.broadcast(b'REQUEST_NEXT_SPEAKER'))

    def respond_next_speaker(self):
        # Determine the next speaker based on the session ledger
        next_speaker = self.get_next_speaker()
        if next_speaker:
            mac = next_speaker[1]
            print(f"Next speaker: {next_speaker[0]}")
            asyncio.create_task(self.broadcast(f'NEXT_SPEAKER:{mac}'.encode()))

    def get_next_speaker(self):
        # Logic to determine the next speaker from the ledger
        for event in self.session_ledger:
            if event[3] == 'raise_hand':
                return event
        return None

    def calculate_speaking_times(self, speaker_timer):
        speaking_times = {}
        for event in self.session_ledger:
            if event[3] == 'start_session' or event[3] == 'raise_hand':
                name = event[0]
                if name not in speaking_times:
                    speaking_times[name] = 0
                speaking_times[name] += speaker_timer
        return speaking_times

    def get_queue_status(self, speaker_timer):
        status = []
        speaking_times = self.calculate_speaking_times(speaker_timer)
        for mac in self.queue:
            name = self.mac_to_name.get(mac, mac.hex())
            count = sum(1 for event in self.session_ledger if event[1] == mac and event[3] == 'raise_hand')
            total_time = speaking_times.get(name, 0)
            status.append((name, count, total_time))
        return status
