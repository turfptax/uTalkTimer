class Queue:
    def __init__(self):
        self.queue = []

    def add_to_queue(self, name, mac):
        self.queue.append((name, mac))
        print(f"Added to queue: {name} ({mac})")

    def get_next_speaker(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def get_queue(self):
        return self.queue

    def clear_queue(self):
        self.queue = []
        print("Queue cleared")
