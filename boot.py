# boot.py for TTRV Version 2.0 PCB
# PCB3 in design phase
# 

import network
import aioespnow
import asyncio
import time
import gc
from machine import Pin, SoftI2C, PWM
import ssd1306

mem_free = 0
mem_alloc = 0
current_time = time.time()
time_markers = []
wlan = False
esp = False
ram = []
led = False
ledPIN = 15
scl = 9
sda = 8
oledWIDTH = 128
oledHEIGHT =  64
oledROTATION = 180

peers = []

bcast = b'\xff' *6
peer = b'\xec\xda;3Y\xb8'
menu = [['[0] Ping All',0,1],['[1] Raise Hand',1,1],['[2] Peer Table',2,1],['[3] Start Timer',3,0],['[4] Exit',4,1]]
user_list_menu = []

#motor test
motorPin = 21
pwm = PWM(Pin(motorPin))
pwm.freq(1000)
pwm.duty(0)

def initOLED(scl=scl,sda=sda,led=led,w=oledWIDTH,h=oledHEIGHT):
    print('scl = ',scl)
    print('sda = ',sda)
    oled = False
    i2c = False
    time.sleep(.5)
    i2c = SoftI2C(scl=scl,sda=sda)
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

def time_display(time,oled=oled):
    hours = time // 3600
    remaining_seconds = time % 3600
    minutes = remaining_seconds // 60
    time = remaining_seconds % 60
    oled.fill_rect(0,7*8,128,8,0)
    oled.text(f"{hours:02}:{minutes:02}:{time:02}",0,7*8)
    oled.show()
    return f"{hours:02}:{minutes:02}:{time:02}"
    
def pulse(number,pattern,pwm=pwm):
    patterns = [[(1023, 0.05), (0, 0.05)],
                [(1023,0.0025),(750,0.075),(500,0.0125),(0,0.0025)],
                [(500, 0.05), (750, 0.05), (1023, 0.1), (750, 0.075), (500, 0.05), (0, 0.0725)]]
    # Define patterns as [duty, duration]
    for i in range(number):
        for duty, duration in patterns[pattern]:
            pwm.duty(duty)
            time.sleep(duration)
    pwm.duty(0)

# Send a periodic ping to a peer
async def heartbeat(e,peer,period):
    while True:
        if not await e.asend(peer, b'ping'):
            print("Heartbeat: peer not responding:", peer)
        else:
            hb = True
        await asyncio.sleep(period)

def setup_network():
    print('setting up network')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    e = aioespnow.AIOESPNow()
    e.active(True)
    time.sleep(1)
    return(e)

def memory_monitor():
    global mem_free, mem_alloc
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    #print("Free Memory:", mem_free, "bytes")
    #print("Allocated Memory:", mem_alloc, "bytes")
        
async def timekeeper():
    global current_time, time_markers
    boot_time = time.time()
    time_markers.append(['Boot',boot_time])
    while True:
        # Update current time
        current_time = time.time()
        current_time = current_time - time_markers[-1][1]
        display_time = time_display(current_time)
        print('current_time', display_time)
        memory_monitor()
        # Update time markers (if needed)
        #time_markers.append(current_time - boot_time)  # Relative to boot time
        await asyncio.sleep(1)

def process_message(mac,msg):
    print('mac',mac,'msg',msg)
    if msg != b'ping' and msg != b'PING' and msg != b'RECV':
        frint(msg)
        pulse(1,0)
    if msg == b'RECV':
        pulse(1,0)

def add_peer(mac):
    global peers
    global esp
    try:
        esp.add_peer(mac)
        peers.append(mac)
    except Exception as e:
            print(f"Peer Add Error: {e}")

async def receiver(e):
    async for mac, msg in e:
        print("echo:",msg)
        process_message(mac,bytes(msg))
        try:
            if msg != 'RECV':
                await e.asend(mac, 'RECV')
        except OSError as err:
            if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                e.add_peer(mac)
                await e.asend(mac, msg)

last_interrupt_time = 0
def button_handler(pin):
    global last_interrupt_time
    current_time = time.ticks_ms()
    print(current_time,last_interrupt_time)
    if time.ticks_diff(current_time, last_interrupt_time) > 900:  # Debounce period of 400 ms
        print(f"Button {pin} pressed, handling interrupt")
        #asyncio.create_task(handle_button_press(pin))
        main_menu(pin)
        
def button_pressed(pin):
    print("Button on pin", pin, "pressed")

def setup_button_interrupts():
    global button1, button2, button3
    button1 = Pin(4, Pin.IN, Pin.PULL_UP)
    button2 = Pin(5, Pin.IN, Pin.PULL_UP)
    button3 = Pin(6, Pin.IN, Pin.PULL_UP)
    button1.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button2.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    button3.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    print("Button interrupts set up")

def bytes_to_mac_address(bytes_key):
    # Convert each byte to a two-digit hex string and join them with colons
    return ':'.join(f'{b:02x}' for b in bytes_key)

def show_peers(peers_table):
    for key, (value1,value2) in peers_table.items():
        mac_address = bytes_to_mac_address(key)
        frint(mac_address)
        frint(value1)

def main_menu(pin):
    global menu
    global button1, button2, button3
    global current_active
    global e
    global time_markers
    time.sleep(.3)
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
        if current_active == 0:
            print('Ping All')
            #frint('Pinging All')
            #asyncio.create_task(send_message(b'\xff'*6,'PING'))
            #e.asend(b'\xff'*6,'PING-ALL')
            e.send(b'\xff'*6,'PING-ALL')
            frint('sent p-broadcast')
            time.sleep(.5)
        if current_active == 1:
            print('Raise Hand')
            #esp.send(b'x\ff'*6,'Raise Hand')
            frint('Raise Hand')
            time.sleep(.5)
        elif current_active == 2:
            print('-----User List-----')
            frint('-----PEERS-----')
            peers_table = e.peers_table
            show_peers(peers_table)
            print(e.peers_table)
            print(e.get_peers())
            print('end Peers Table')
            time.sleep(.5)
        elif current_active == 3:
            print('Start Timer')
            time_markers.append(['START',time.time()])
            #esp.send(b'x\ff'*6,'Start Timer')
            frint('Start Timer')
            time.sleep(.5)
        elif current_active == 4:
            print('Exit')
            frint('Exit')
            time.sleep(.5)

async def main(e, peer, timeout, period):
    count = 0
    stop = False
    while not stop:
        print(f'---------------------------------------------count: {count}')
        asyncio.create_task(heartbeat(e, peer, period))
        asyncio.create_task(receiver(e))
        asyncio.create_task(timekeeper())
        await asyncio.sleep(timeout)
        count += 1

print('start init of program')
e = setup_network()
print('e',e)
if e.peer_count()[0] == 0:
    try:
        e.add_peer(bcast)
    except Exception as e:
        print(f'Initial peer add error: {e}')
setup_button_interrupts()
print('post initializes')


asyncio.run(main(e,bcast,120,10))
