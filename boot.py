import network
import aioespnow
import asyncio
from machine import Pin, I2C, PWM
import time
import ssd1306
import gc

ram = []
led = False
ledPIN = 15
sclPIN = 9
sdaPIN = 8
oledWIDTH = 128
oledHEIGHT =  64
oledROTATION = 180

# Initiate Device Buttons Pins 4,5,6 esp32-c3 supermini
LeftPin = 4
MiddlePin = 5
RightPin = 6

#motor test
motorPin = 0
pwm = PWM(Pin(motorPin))
pwm.freq(1000)

def initOLED(scl=Pin(sclPIN),sda=Pin(sdaPIN),led=led,w=oledWIDTH,h=oledHEIGHT):
  print('scl = ',scl)
  print('sda = ',sda)
  oled = False
  i2c = False
  try:
    i2c = I2C(scl=scl,sda=sda)
  except:
    print('i2c failed check pins scl sda')
    try:
      print('i2c.scan() = ',i2c.scan())
    except:
      print('i2c.scan() failed')
  if i2c:
    try:
      oled = ssd1306.SSD1306_I2C(w,h,i2c)
      print("SSD1306 initialized[Y]")  
      print('oled = ',oled)
    except:
      print("failed to initialize onboard SSD1306")
  oled.rotate(False)
  return oled

oled = initOLED()

def frint(text,oled=oled,ram=ram):
  if oled:
    if text:
      text = str(text)
      if len(text) <= 16:
        ram.append(text)
      else:
        ram.append(text[0:5]+'..'+text[len(text)-9:])
    oled.fill(0)
    n = 0
    for i in ram[-8:]:
      oled.text(i,0,n*8)
      n+=1
    if len(ram) > 9:
      ram = ram[-9:]
    gc.collect()
    oled.show()
    print('f:> ',ram[-1])
  else:
    print('f:< ',text)

def pulse(number,pattern,pwm=pwm):
    patterns = [[(1023, 0.10), (0, 0.10)],
                [(1023,0.05),(750,0.15),(500,0.25),(0,0.05)],
                [(500, 0.10), (750, 0.10), (1023, 0.2), (750, 0.15), (500, 0.10), (0, 0.15)]]
    # Define patterns as [duty, duration]
    for i in range(number):
        for duty, duration in patterns[pattern]:
            pwm.duty(duty)
            time.sleep(duration)
    pwm.duty(0)

def setup_network(interface_type=network.STA_IF):
    print('setting up network')
    wlan = network.WLAN(interface_type)
    wlan.active(True)
    if interface_type == network.STA_IF:
        wlan.disconnect()  # Only for ESP8266
    return wlan

def init_espnow():
    print('initializing espnow()')
    esp = aioespnow.AIOESPNow()
    esp.active(True)
    return esp

def button_pressed_handler(pin):
    print("Button pressed, handling interrupt")
    asyncio.create_task(send_led_on_message())

async def send_led_on_message():
    peer = b'\xFF\xFF\xFF\xFF\xFF\xFF'  # Adjust this to your actual peer address
    print("Sending 'PING' command")
    await esp.asend(peer, b'PING')

async def wait_for_message(esp):
    waits = 0
    while True:
        try:
            print("Waiting for a message...")
            frint('waiting...')
            waits += 1
            print(f"waits: {waits}")
            mac, msg = esp.recv()  # Asynchronously wait for a message
            if msg:
                print(f"Received message: {msg}")
                print(f"Mac: {mac}")
        except Exception as e:
            print("An error occurred:", e)
            # Handle the error or perform a controlled reset/retry

def process_message(msg):
    try:
        if msg == b'ping':
            print("Ping received, responding...")
            # Your response code here
    except Exception as e:
        print("Error processing message:", e)

    
def update_display_menu():
    # This function would update the display based on the current menu state
    print("Display updated with current menu state")
    #mainMenu()
    
def mainMenu():
    bcast = b'\xff' *6
    global left
    global right
    global middle
    global oled
    global wlan
    menu = [['[0] Ping All',0,0],['[1] Receive 20',1,1],['[2] Talk Next',2,1],['[3] Start Timer',3,1],
            ['[4] Exit',3,1]]
    end = False
    while not end:
      oled.fill(0)
      for i,x in enumerate(menu):
          oled.fill_rect(0,i*8,128,8,abs(x[2]-1))
          oled.text(x[0],0,i*8,x[2])
      oled.show()
      if middle.value() == 0 and menu[0][2] == 0:
          frint('Ping All')
          ping(bcast)
          return
      if middle.value() == 0 and menu[3][2] == 0:
          return
      if middle.value() == 0 and menu[4][2] == 0:
          return
      if middle.value() == 0 and menu[2][2] == 0:
          while True:
              frint('oops')
          if middle.value() == 0:
              return
      if middle.value() == 0 and menu[1][2] == 0:
          frint('Receive 20 Secs')
          frint(receive(20000))
          return
      if right.value() == 0 or left.value() == 0:
          for i,x in enumerate(menu):
              
              if x[2] == 0:
                  if right.value() == 0:
                      menu[i][2] = 1
                      menu[i-len(menu)+1][2] = 0
                      time.sleep(.3)
                  if left.value() == 0:
                      menu[i][2] = 1
                      menu[i-1][2] = 0
                      time.sleep(.3)
                      
# Global variable to avoid bouncing issues
last_interrupt_time = 0

def button_handler(pin):
    global last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time) > 200:  # Debounce period of 200 ms
        print(f"Button {pin} pressed, handling interrupt")
        frint('button')
        asyncio.create_task(handle_button_press(pin))
        last_interrupt_time = current_time
        
def setup_button_interrupts():
    global button1, button2, button3
    button1 = Pin(4, Pin.IN, Pin.PULL_UP)
    button2 = Pin(5, Pin.IN, Pin.PULL_UP)
    button3 = Pin(6, Pin.IN, Pin.PULL_UP)
    button1.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button2.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button3.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    print("Button interrupts set up")

async def handle_button_press(pin):
    print(pin)
    if pin == button1:
        print("Updating menu for Button 1")
        # Update menu or trigger action for Button 1
    elif pin == button2:
        print("Updating menu for Button 2")
        # Update menu or trigger action for Button 2
    elif pin == button3:
        print("Updating menu for Button 3")
        # Update menu or trigger action for Button 3

def main():
    frint('main()')
    setup_button_interrupts()
    pulse(1,2)
    
    wlan = setup_network()
    esp = init_espnow()
    button_pin = Pin(5, Pin.IN, Pin.PULL_UP)

    loop = asyncio.get_event_loop()
    loop.create_task(wait_for_message(esp))
    #try:
    while True:
        loop.run_forever()
    #except KeyboardInterrupt:
    #    print("Program interrupted by user")
    #    loop.close()  # Properly close the loop if interrupted
    frint('after stuff')
    print('after stuff')

if __name__ == "__main__":
    main()
