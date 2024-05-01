# uTalkTimer
uTalkTimer: An async ESPNOW-based MicroPython library for efficient discussion management in meetings, featuring speaker time tracking, speech queuing, and voting functionalities.

## Installation and Setup

Follow these instructions to set up the environment and install all required dependencies for the uTalkTimer project.

### Prerequisites

Before you begin, ensure you have MicroPython installed on your ESP32 device. You will also need to install `mpremote` to interact with your MicroPython device from your computer.

#### Installing mpremote

You can install `mpremote` using pip. Open your terminal and run:

```bash
pip install mpremote
```

### Installing Required Libraries

The project depends on the `aioespnow` and `ssd1306` libraries for asynchronous ESPNOW communication and OLED display management, respectively. Follow the steps below to install these libraries on your MicroPython device.

1. **Connect to Your MicroPython Device**:

   First, connect to your device using `mpremote`. In your terminal, type:

   ```bash
   mpremote connect <port_or_address>
   ```

   Replace `<port_or_address>` with the appropriate connection port or network address of your MicroPython device.

2. **Copy Libraries**:

   Use `mpremote` to copy the required libraries to your device. Place the `aioespnow.mpy` and `ssd1306.mpy` files in the `/lib` folder on your device:

   ```bash
   mpremote cp aioespnow.mpy :/lib/
   mpremote cp ssd1306.mpy :/lib/
   ```

### Verifying the Installation

After installing the libraries, you can check if they are correctly placed by listing the files in the `/lib` directory on your device:

```bash
mpremote ls /lib
```

You should see `aioespnow.mpy` and `ssd1306.mpy` listed.

## Running the Project

Once all prerequisites and required libraries are installed, you can upload the main script to your device and run it using `mpremote`:

```bash
mpremote cp uTT.py :/main.py  # Copy the main project file
mpremote repl                 # Open the MicroPython REPL
```

In the REPL, you can manually import and run your project or simply reboot your device to start the main application.
