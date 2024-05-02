import network
import aioespnow
import asyncio
from machine import Pin, I2C, PWM
import time
import ssd1306
import gc
import utime

ram = []
led = False
ledPIN = 15
sclPIN = 9
sdaPIN = 8
oledWIDTH = 128
oledHEIGHT =  64
oledROTATION = 180

menu = [['[0] Ping All',0,1],['[1] Raise Hand',1,1],['[2] Talk Next',2,1],['[3] Start Timer',3,0],['[4] Exit',4,1]]
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
    bcast = b'\xff' *6
    try:
        esp.add_peer(bcast)
    except Exception as e:
        print(f"Failed to add peer: {e}")
    return esp

async def send_message(peer,msg):
    try:
        await esp.asend(peer, msg)
    except:
        print('message already utf-8?')
    

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
                msg = msg.decode('utf-8')
                print(f"Received message: {msg}")
                print(f"Mac: {mac}")
                frint(f"Received message: {msg}")
                frint(f"Mac: {mac}")
                process_message(mac,msg)
                pulse(1,0)
        except Exception as e:
            print("An error occurred:", e)
            # Handle the error or perform a controlled reset/retry

def add_peer(mac):
    try:
        esp.add_peer(mac)
    except Exception as e:
            print(f"Peer Add Error: {e}")
    
def process_message(mac,msg):
    try:
        if msg == 'ping':
            print("Ping received, responding...")
            asyncio.create_task(send_message(mac,'pong'))
            # Your response code here
    except Exception as e:
        print("Error processing message:", e)

    
def update_display_menu():
    # This function would update the display based on the current menu state
    print("Display updated with current menu state")
    #mainMenu()


# Global variable to avoid bouncing issues
last_interrupt_time = 0

def button_handler(pin):
    global last_interrupt_time
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_interrupt_time) > 200:  # Debounce period of 200 ms
        print(f"Button {pin} pressed, handling interrupt")
        #asyncio.create_task(handle_button_press(pin))
        handle_button_press(pin)
        last_interrupt_time = current_time

def button_pressed_handler(pin):
    print("Button pressed, handling interrupt")
    asyncio.create_task(send_led_on_message())
        
def setup_button_interrupts():
    global button1, button2, button3
    button1 = Pin(4, Pin.IN, Pin.PULL_UP)
    button2 = Pin(5, Pin.IN, Pin.PULL_UP)
    button3 = Pin(6, Pin.IN, Pin.PULL_UP)
    button1.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button2.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button3.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    print("Button interrupts set up")
    
current_active = 0

def handle_button_press(pin):
    global menu
    global button1, button2, button3
    global current_active
    time.sleep(.1)
    length = len(menu)
    for i, x in enumerate(menu):
        if x[2] == 0:
            current_active = i
            menu[i][2] = 1
    # menu = [[NameString,Index,Selector]] Selector is 0 if that menu item is selected
    if pin == button1 or pin == button3:
        if pin == button3:
            current_active -= 1
        if pin == button1:
            current_active += 1
        if current_active >= length:
            current_active = 0
        if current_active < 0:
            current_active = length-1
        menu[current_active][2] = 0
        for i,x in enumerate(menu):
              oled.fill_rect(0,i*8,128,8,abs(x[2]-1))
              oled.text(x[0],0,i*8,x[2])
        oled.show()
    elif pin == button2:
        frint('button2')
        if current_active == 0:
            print('Ping All')
            frint('Ping All')
            asyncio.create_task(send_message(b'\xff'*6,'PING'))
            oled.fill(0)
            oled.show()
        if current_active == 1:
            print('Raise Hand')
            frint('Raise Hand')
        elif current_active == 2:
            print('Talk Next')
            frint('Talk Next')
        elif current_active == 3:
            print('Start Timer')
            frint('Start Timer')
        elif current_active == 4:
            print('Exit')
            frint('Exit')
                    
async def periodic_task(interval):
    while True:
        print("Periodic action triggered")
        # Perform periodic action here
        await asyncio.wait_for_ms(interval)
        frint('TIME!')
    
def main():
    frint('main()')
    setup_button_interrupts()
    pulse(1,2)
    
    wlan = setup_network()
    esp = init_espnow()
    
    asyncio.create_task(periodic_task(1000))
    loop = asyncio.get_event_loop()
    loop.create_task(wait_for_message(esp))
    
    #try:
    #while True:
        #print('----------------------------------------------------------')
    loop.run_forever()
    #except KeyboardInterrupt:
    #    print("Program interrupted by user")
    #    loop.close()  # Properly close the loop if interrupted
    frint('after stuff')
    print('after stuff')

if __name__ == "__main__":
    main()
