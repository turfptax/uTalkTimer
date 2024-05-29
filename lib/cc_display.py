from machine import SoftI2C, Pin
import ssd1306
import writer
import freesans20
import time
import gc

class Display:
    def __init__(self):
        self.i2c = SoftI2C(scl=Pin(9), sda=Pin(8))
        print('i2c.scan():',self.i2c.scan())
        self.oled = ssd1306.SSD1306_I2C(128, 64, self.i2c)
        self.oled.rotate(False)
        self.oled.fill(0)
        self.oled.show()
        self.font_writer = writer.Writer(self.oled, freesans20)
        self.last_time_update = 0

    def show_text(self, text, line):
        self.oled.text(text, 0, line * 8)
        self.oled.show()

    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def update_inactive_display(self, menu_items, current_selection, current_time, num_peers):
        self.oled.fill(0)
        self.update_time(current_time)
        self.update_hud(num_peers)
        self.update_menu(menu_items, current_selection)
        self.oled.show()

    def update_time(self, current_time, invert=False):
        if current_time is None:
            current_time = 0  # Default to 0 if current_time is None

        minutes = current_time // 60
        seconds = current_time % 60
        time_str = f"{minutes:02}:{seconds:02}"

        self.oled.fill_rect(0, 0, 128, 16, 0)  # Clear the area for the time
        if invert:
            self.oled.invert(True)
        self.font_writer.set_textpos(0, 0)
        self.font_writer.set_clip(False, False)
        self.font_writer.printstring(time_str)
        if invert:
            self.oled.invert(False)
        self.oled.show()


    def update_session_display(self, speaker_time, total_time, queue_status, mode, invert=False, device_speaker_time_left=0):
        self.oled.fill(0)
        self.update_time(speaker_time, invert)
        self.oled.text(f"Total: {total_time // 60:02}:{total_time % 60:02}", 0, 24)
        self.oled.text(f"Left: {device_speaker_time_left // 60:02}:{device_speaker_time_left % 60:02}", 0, 32)
        if mode == 'active_speaker':
            self.oled.text("VOTE  END   MENU", 0, 48)
            self.oled.text("ADD   TIME        ", 0, 56)
        elif mode == 'active_listener':
            self.oled.text("VOTE  RAISE MENU", 0, 48)
            self.oled.text("ADD   HAND        ", 0, 56)
        #for idx, (name, count, total_time) in enumerate(queue_status):
        #    self.oled.text(f"{name}({count}): {total_time}s", 0, 40 + idx * 8)
        self.oled.show()

    def update_hud(self, num_peers):
        self.oled.fill_rect(100, 0, 28, 8, 0)  # Clear the area for the HUD
        self.oled.text(f"Ps:{num_peers}", 90, 0)
        self.oled.show()

    def update_menu(self, menu_items, current_selection):
        self.oled.fill_rect(0, 16, 128, 48, 0)  # Clear the menu area
        max_items_per_column = 7
        for idx, item in enumerate(menu_items):
            column = idx // max_items_per_column
            row = idx % max_items_per_column
            prefix = '>' if idx == current_selection else ' '
            self.oled.text(f"{prefix}{item}", column * 64, 16 + row * 8)
        self.oled.show()

    def update(self, mode, current_time, num_peers, speaker_time=None, total_time=None, invert=False, menu_items=None, current_selection=0, queue_status=None, device_speaker_time_left=0):
        current_ticks = time.ticks_ms()
        if current_time is None:
            current_time = 0  # Default to 0 if current_time is None
        if speaker_time is None:
            speaker_time = 0  # Default to 0 if speaker_time is None
        if total_time is None:
            total_time = 0  # Default to 0 if total_time is None
        if mode == 'inactive':
            if time.ticks_diff(current_ticks, self.last_time_update) >= 1000:  # Update every second
                self.update_inactive_display(menu_items, current_selection, current_time, num_peers)
                self.last_time_update = current_ticks
        elif mode in ['active_speaker', 'active_listener']:
            #print(speaker_time, total_time, queue_status, mode, invert, device_speaker_time_left)
            self.update_session_display(speaker_time, total_time, queue_status, mode, invert, device_speaker_time_left)
