# Pi Productivity Dashboard

This project turns a Raspberry Pi into a personal productivity and focus-assistance system. It integrates a web dashboard, posture monitoring, task management, and hardware like a Sense HAT and an e-paper display to help you stay on track.

## Features

- **Web Dashboard**: A web interface to view the camera feed, sensor data from the Sense HAT, and manage tasks.
- **Posture Monitoring**: Uses the Raspberry Pi camera and OpenCV to periodically check your posture and provide feedback.
- **Task Management**: Syncs with the Motion app via its API to fetch and display your tasks.
- **Focus Modes**: Utilizes the Sense HAT LED matrix for different timer-based modes (e.g., Study, Leisure).
- **E-Paper Display**: Shows a persistent, low-power summary of your pending tasks.
- **OCR for Notes**: Lets you capture handwritten notes with the camera and turn them into digital text and tasks.

## Hardware Requirements

- Raspberry Pi (3B+ or newer recommended)
- Raspberry Pi Camera Module
- Sense HAT
- Waveshare 2.7inch e-Paper HAT

## Setup and Installation

These instructions are for a Raspberry Pi running the latest **Raspberry Pi OS (64-bit)**.

### 1. Update System & Install Dependencies

First, make sure your system is up-to-date and install the necessary libraries for computer vision, text recognition, and hardware interfacing.

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y \
    libcamera-dev \
    python3-opencv \
    python3-spidev \
    python3-rpi.gpio \
    tesseract-ocr \
    libatlas-base-dev
```

**Note:** We install `opencv`, `spidev`, and `rpi.gpio` using `apt-get` because these packages require deep integration with the Raspberry Pi hardware. Using the system-provided versions is more stable than installing them with `pip`.

### 2. Enable Hardware Interfaces

Use the Raspberry Pi Configuration tool to enable the camera and I2C interfaces.

```bash
sudo raspi-config
```

Navigate to **3 Interface Options** and enable:

- **I1 Legacy Camera** (Enable legacy camera support for Picamera2)
- **I2C** (For the Sense HAT and e-paper display)

Reboot your Raspberry Pi when prompted.

### 3. Clone the Project

Clone this project repository to your Raspberry Pi.

```bash
git clone https://github.com/alebmorais/pi_productivity.git ~/pi_productivity
cd ~/pi_productivity
```

### 4. Set Up Python Environment

It is highly recommended to use a Python virtual environment to manage dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

*To exit the virtual environment later, just type `deactivate`.*

Now, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

The application requires API keys and other settings, which are managed in a `.env` file.

First, define the project's root directory. This is important for the application to locate its files.

```bash
export PI_PRODUCTIVITY_DIR=~/pi_productivity
```

**Note:** You may want to add this line to your `~/.bashrc` file to make it permanent.

Next, create the `.env` file:

```bash
nano .env
```

Add the following lines, replacing the placeholder values with your own:

```ini
MOTION_API_KEY="your_motion_api_key_here"
```

Press `Ctrl+X`, then `Y`, and `Enter` to save and exit.

## Running the Application

With your virtual environment still active (`source .venv/bin/activate`), run the main application:

```bash
python main.py
```

This single command starts the web server, initializes the hardware, and begins all background monitoring tasks.

- **Web Dashboard**: Open a browser on a device on the same network and go to `http://<your-pi-ip-address>:8000`.
- **Sense HAT**: The joystick can be used to cycle through different modes.
- **E-Paper Display**: The display will automatically update with your tasks from Motion.

To stop the application, press `Ctrl+C` in the terminal.

## Customization

You can easily customize the behavior of the application by editing the constants at the top of the `main.py` file:

- `MOTION_ENABLE_OCR`: Set to `True` to automatically create Motion tasks from captured text, or `False` to disable.
- `OCR_DEFAULT_DUE_DAYS`: The default number of days from now to set a task's due date if not specified in the OCR text.
- `POSTURE_INTERVAL`: The time in seconds between automatic posture checks.
- `OCR_INTERVAL`: The time in seconds between automatic OCR captures (if a dedicated OCR loop is active).
- `MOTION_SYNC_INTERVAL`: The time in seconds between synchronizations with the Motion API.

## Troubleshooting

- **Motion API Errors (401/400)**: Double-check that your `MOTION_API_KEY` in the `.env` file is correct and does not contain any extra characters.
- **Camera Not Detected**: Ensure the camera is securely connected and that you have enabled the legacy camera interface in `raspi-config`.
- **Hardware Not Responding (Sense HAT / E-Paper)**: Check that the HATs are properly seated on the GPIO pins and that I2C is enabled. A reboot can sometimes resolve detection issues.
