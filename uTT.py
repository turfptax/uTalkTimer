# ThinkTankRemoveVote

import network
from machine import Pin, I2C, PWM
import time
import ssd1306
import gc
import espnow

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

left = Pin(LeftPin,Pin.IN,Pin.PULL_UP)
middle = Pin(MiddlePin,Pin.IN,Pin.PULL_UP)
right = Pin(RightPin,Pin.IN,Pin.PULL_UP)

buttons = [left,middle,right]

#motor test
motorPin = 0


pwm = PWM(Pin(motorPin))
pwm.freq(1000)

pulse_type = {}

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
    for i in ram[-4:]:
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

def wlan_init():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    frint('Wlan init')
    frint(f'network config:{wlan.ifconfig()}')
    return wlan

def espnow_init():
    esp = espnow.ESPNow()
    if not esp.active():
        esp.active(True)
    bcast = b'\xff' *6
    try:
        esp.add_peer(bcast)
    except Exception as e:
        print(f"Failed to add peer: {e}")
    return esp

def ping(mac):
    try:
        esp.send(mac,"ping")
    except Exception as e:
        print(f"Failed to ping: {e}")
        
def receive(time):
    _, msg = esp.recv()
    if msg:
        return msg
    else:
        return False


#INITIALIZE WLAN AND ESPNOW
wlan = wlan_init()
esp = espnow_init()    

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

frint('Think Tank')
frint('Remote Vote')
frint('& Time Keeper')
frint('(Virtual Yahia)')

pulse(1,2)
pi = 0


def mainloop(pi=pi,led=led,middle=middle,up=right,down=left):
    count = 0
    exit_bool = False
    button_thresh = 0
    while not exit_bool:
        if up.value() == 0 or down.value() == 0:
            mainMenu()
        if middle.value() == 0:
            button_thresh += 1
        else:
            button_thresh += -1
        if button_thresh > 20:
            exit_bool = True
        elif button_thresh < 0:
            button_thresh = 0
        if pi == 0:
            frint('first run')
        if pi >= 10:
            count += 1
            pi = 1
        else:
            pi += 1




