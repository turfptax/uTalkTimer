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

    def update_time(self, current_time):
        hours = current_time // 3600
        remaining_seconds = current_time % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        
        self.oled.fill_rect(0, 44, 128, 16, 0)  # Clear the area for the time
        self.font_writer.set_textpos(0, 44)
        self.font_writer.set_clip(False,False)
        self.font_writer.printstring(time_str)
        self.oled.show()

    def update_hud(self, num_peers):
        self.oled.fill_rect(84, 56, 44, 8, 0)  # Clear the area for the HUD
        self.oled.text(f"Ps:{num_peers}", 84, 56)
        self.oled.show()

    def update(self, current_time, num_peers):
        current_ticks = time.ticks_ms()
        if time.ticks_diff(current_ticks, self.last_time_update) >= 1000:  # Update every second
            self.update_time(current_time)
            self.update_hud(num_peers)
            self.last_time_update = current_ticks

    def update_menu(self, menu_items, current_selection):
        
        gc.collect()
        self.oled.fill_rect(0, 0, 128, 48, 0)  # Clear the menu area only
        for idx, item in enumerate(menu_items):
            prefix = '>' if idx == current_selection else ' '
            self.oled.text(f"{prefix}{item}", 0, idx * 8)
        self.oled.show()

