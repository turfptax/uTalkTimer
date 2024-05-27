from machine import SoftI2C, Pin
import ssd1306
import writer
import freesans20
import time
import gc

class Display:
    def __init__(self):
        self.i2c = SoftI2C(scl=Pin(9), sda=Pin(8))
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

    def update_session_display(self, speaker_time, total_time, queue_status, mode, invert=False):
        self.oled.fill(0)
        self.update_time(speaker_time, invert)
        self.oled.text(f"Total: {total_time // 60:02}:{total_time % 60:02}", 0, 24)
        if mode == 'active_speaker':
            self.oled.text("VOTE  END   MENU", 0, 48)
            self.oled.text("ADD   TIME        ", 0, 56)
        elif mode == 'active_listener':
            self.oled.text("VOTE  RAISE MENU", 0, 48)
            self.oled.text("ADD   HAND        ", 0, 56)
        for idx, (name, count, total_time) in enumerate(queue_status):
            self.oled.text(f"{name}({count}): {total_time}s", 0, 32 + idx * 8)
        self.oled.show()

    def update_hud(self, num_peers):
        self.oled.fill_rect(100, 0, 28, 8, 0)  # Clear the area for the HUD
        self.oled.text(f"Ps:{num_peers}", 90, 0)
        self.oled.show()

    def update_menu(self, menu_items, current_selection):
        self.oled.fill_rect(0, 16, 128, 48, 0)  # Clear the menu area
        for idx, item in enumerate(menu_items):
            prefix = '>' if idx == current_selection else ' '
            self.oled.text(f"{prefix}{item}", 0, 16 + idx * 8)
        self.oled.show()

    def update(self, mode, current_time, num_peers, speaker_time=None, total_time=None, invert=False, menu_items=None, current_selection=0, queue_status=None):
        current_ticks = time.ticks_ms()
        if mode == 'inactive':
            if time.ticks_diff(current_ticks, self.last_time_update) >= 1000:  # Update every second
                self.update_inactive_display(menu_items, current_selection, current_time, num_peers)
                self.last_time_update = current_ticks
        elif mode in ['active_speaker', 'active_listener']:
            self.update_session_display(speaker_time, total_time, queue_status, mode, invert)
