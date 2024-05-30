# cc_buzz.py
from machine import PWM, Pin
import time

class Buzz:
    def __init__(self):
        print('Initializing Buzz class')
        self.motor_pin = Pin(21, Pin.OUT)
        self.motor_pin.value(0)
        self.pwm = PWM(self.motor_pin)
        self.pwm.freq(1000)
        self.pwm.duty(64)
        time.sleep(.1)
        self.pwm.duty(0)
        
        
        #print('setting PWM duty to 0')
        #self.pwm.duty(0)
        #time.sleep(.1)
        
        #print(f"Pin state after initialization: {self.motor_pin.value()}")
        #self.pwm.duty(0)
        #time.sleep(1)
    
    def short_buzz(self):
        self.pwm.duty(128)  # 25% duty cycle
        time.sleep(0.1)     # Buzz for 0.1 seconds
        self.pwm.duty(0)

    def long_buzz(self):
        self.pwm.duty(128)  # 25% duty cycle
        time.sleep(1)       # Buzz for 1 second
        self.pwm.duty(0)

    #def buzz(self, pattern):
    #    patterns = [[(1023, 0.05), (0, 0.05)],
    #                [(1023, 0.0025), (750, 0.075), (500, 0.0125), (0, 0.0025)],
    #                [(500, 0.05), (750, 0.05), (1023, 0.1), (750, 0.075), (500, 0.05), (0, 0.0725)]]
    #    for duty, duration in patterns[pattern]:
    #        self.pwm.duty(duty)
    #        time.sleep(duration)
    #    self.pwm.duty(0)

    def update(self):
        # Update buzzing if needed
        pass
