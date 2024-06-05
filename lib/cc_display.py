from machine import SoftI2C, Pin, ADC
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
        self.bat = ADC(Pin(1))
        self.bat.atten(ADC.ATTN_11DB) # Set attenuation to 11dB for a range of 0-3.9V

    def show_text(self, text, line):
        self.oled.text(text, 0, line * 8)
        self.oled.show()

    def clear(self):
        self.oled.fill(0)
        self.oled.show()
        
    def get_battery_percentage(self, voltage):
        min_voltage = 3.2
        max_voltage = 4.2
        if voltage < min_voltage:
            return 0
        elif voltage > max_voltage:
            return 100
        else:
            percentage = (voltage - min_voltage) / (max_voltage - min_voltage) * 100
            return percentage

    def draw_battery(self, percentage):
        x = 64
        y = 1
        width = 10
        height = 7

        # Draw the battery outline
        self.oled.rect(x, y, width, height, 1)

        # Calculate the fill width based on the percentage
        fill_width = int(percentage / 100 * (width - 2))  # -2 to account for the outline thickness

        # Draw the filled part of the battery
        self.oled.fill_rect(x + 1, y + 1, fill_width, height - 2, 1)

    def show_battery(self):
        # Read the ADC value in microvolts
        adc_uv = self.bat.read_uv()

        # Convert microvolts to volts
        v_adc = adc_uv / 1e6

        # Calculate the battery voltage considering the voltage divider
        v_batt = v_adc * (3 / 2)

        # Calculate battery percentage
        battery_percentage = self.get_battery_percentage(v_batt)

        # Draw the battery level
        self.draw_battery(battery_percentage)

        # Print for debugging
        print(f"Battery Voltage: {v_batt:.2f}V - {battery_percentage:.2f}%")

    def update_inactive_display(self, menu_items, current_selection, current_time, num_peers):
        #self.oled.fill(0)
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


    def update_session_display(self, speaker_time, total_time, queue_status, mode, invert=False, allotted_time_left=0):
        self.oled.fill(0)
        self.update_time(speaker_time, invert)
        self.oled.text(f"Total: {total_time // 60:02}:{total_time % 60:02}", 0, 24)
        self.oled.text(f"Left: {allotted_time_left // 60:02}:{allotted_time_left % 60:02}", 0, 32)
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
        self.oled.fill_rect(65, 0, 64, 8, 0)  # Clear the area for the HUD
        battery = self.show_battery()
        self.oled.text(f"Ps:{num_peers}", 75, 0)
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

    def update(self, mode, current_time, num_peers, speaker_time=0, total_time=0, invert=False, menu_items=None, current_selection=0, queue_status=None, allotted_time_left=0):
        current_ticks = time.ticks_ms()
        if mode == 'inactive':
            if time.ticks_diff(current_ticks, self.last_time_update) >= 1000:  # Update every second
                self.update_inactive_display(menu_items, current_selection, current_time, num_peers)
                self.last_time_update = current_ticks
        elif mode in ['active_speaker', 'active_listener']:
            #print(speaker_time, total_time, queue_status, mode, invert, allotted_time_left)
            self.update_session_display(speaker_time, total_time, queue_status, mode, invert, allotted_time_left)
