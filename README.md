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

   First, make sure to close any active IDE connections to the ESP32 micropython device:

   ```bash
   mpremote mip install aioespnow
   mpremote mip install ssd1306
   ```

2. **Verify Libraries**:

   Use thonny or another IDE to varify that the two files are stored in a 'lib' directory with the .mpy extension:

   ```bash
   lib
       aioespnow.mpy
       ssd1306.mpy
   ```
You should see `aioespnow.mpy` and `ssd1306.mpy` listed.

3. **Transfer the following files to your device**:

- boot.py
- freesans20.py (for larger font support)
- writer.py (required for rendering freesans20)

### Verifying the Installation

After installing the libraries, you can check if they are correctly placed by listing the files in the `/lib` directory on your device by trying to import the libraries:

```bash
import aioespnow
import ssd1306
```

## Running the Project

Once all prerequisites and required libraries are installed, you can upload the main script to your device and run it using `mpremote`:

```bash
import uTT
```

In the REPL, you can manually import and run your project or simply reboot your device to start the main application.
