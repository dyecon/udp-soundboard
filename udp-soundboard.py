# UDP Soundboard

# How to play sound
# 1. Add mp3 or wav files to 'sounds/' (python version) or '_internal/sounds/' (standalone).
# 2. Run the UDP soundboard and select the desired audio output device.
# 3. Send a UDP packet in the format of '{sound name} {volume}' to 127.0.0.1:5001
#   For example, to play chime.mp3 at 70% volume, send "chime 0.7"
#   Note that if the volume parameter is omitted, the sound will play at DEFAULT_VOLUME.

# A standalone app can be created with the following command:
# pyinstaller --add-data="sounds/:sounds/" udp-soundboard.py
# see following page for info on external files: https://pyinstaller.org/en/stable/runtime-information.html#placing-data-files-at-expected-locations-inside-the-bundle

import sys
import socket
import numpy as np
import threading
from pathlib import Path

try:
    import sounddevice as sd
except ImportError:
    print("module 'sounddevice' is not installed. Exiting.")
    sys.exit(1)
try:
    import soundfile as sf
except ImportError:
    print("module 'soundfile' is not installed. Exiting.")
    sys.exit(1)


##### Settings #####
UDP_IP = "127.0.0.1"
UDP_PORT = 5001
TIMEOUT = 1.0

SOUNDS = {}
SAMPLE_RATE = 44100
BLOCK_SIZE = 256
DEFAULT_VOLUME = 0.5


##### Output device selection #####
def select_output_device():
    print("\n--- Available Audio Output Devices ---")
    
    devices = sd.query_devices()
    output_devices = []
    # Filter and display only devices with output channels
    for idx, dev in enumerate(devices):
        if dev["max_output_channels"] > 0:
            output_devices.append((idx, dev['name']))
            print(f"[{len(output_devices) - 1}] {dev['name']}")

    if not output_devices:
        raise RuntimeError("No output devices found.")

    # Loop until the user provides a valid selection
    while True:
        try:
            choice = int(input("\nEnter the number of the device you want to use: "))
            if 0 <= choice < len(output_devices):
                selected_idx = output_devices[choice][0]
                return selected_idx
            else:
                print(f"Please enter a number between 0 and {len(output_devices) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

OUTPUT_DEVICE_INDEX = select_output_device()
sd.default.device[1] = OUTPUT_DEVICE_INDEX
print(f"\nOutput device set to: {sd.query_devices()[OUTPUT_DEVICE_INDEX]['name']}")


##### Load sounds #####
#sounds_dir = Path("sounds") # when running as normal script
sounds_dir = Path(__file__).resolve().with_name("sounds") # when running as pyinstaller executable
if sounds_dir.exists() and sounds_dir.is_dir():
    # Iterate through the directory for .mp3 and .wav files
    # rglob("*") searches recursively; glob("*") searches only the top folder
    for file_path in sounds_dir.glob("*"):
        if file_path.suffix.lower() in [".mp3", ".wav"]:
            # Use the filename (without extension) as the key
            # Converting to bytes
            key = file_path.stem.encode()
            SOUNDS[key] = {
                "path": str(file_path),
                "volume": DEFAULT_VOLUME
            }
audio_bank = {}
for key, info in SOUNDS.items():
    data, sr = sf.read(info["path"], dtype="float32")
    if sr != SAMPLE_RATE:
        raise RuntimeError(f"{info['path']} must be {SAMPLE_RATE} Hz")

    if data.ndim == 1:
        data = np.column_stack([data, data])

    audio_bank[key] = {
        "data": data,
        "volume": float(info["volume"])
    }
print(f"Loaded {len(SOUNDS)} sounds.")


##### Audio mixer #####
# Allow sounds to overlap
active_sounds = []
lock = threading.Lock()

def trigger_sound(key, volume_override=None):
    base = audio_bank[key]["volume"]
    volume = base if volume_override is None else base * volume_override
    with lock:
        active_sounds.append({
            "data": audio_bank[key]["data"],
            "pos": 0,
            "volume": volume
        })


##### AUDIO CALLBACK #####
def audio_callback(outdata, frames, time, status):
    outdata.fill(0)

    with lock:
        finished = []

        for sound in active_sounds:
            data = sound["data"]
            pos = sound["pos"]
            vol = sound["volume"]

            remaining = len(data) - pos
            count = min(frames, remaining)

            outdata[:count] += data[pos:pos + count] * vol
            sound["pos"] += count

            if sound["pos"] >= len(data):
                finished.append(sound)

        for sound in finished:
            active_sounds.remove(sound)

    np.clip(outdata, -1.0, 1.0, out=outdata)


##### Start Audio Stream #####
stream = sd.OutputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    device=OUTPUT_DEVICE_INDEX,
    channels=2,
    dtype="float32",
    callback=audio_callback
)
stream.start()
print("Audio stream running")


##### UDP server #####
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(TIMEOUT)
print(f"UDP mixer listening on {UDP_IP}:{UDP_PORT} (press ctrl-C to quit)")
try:
    while True:
        try:
            msg, _ = sock.recvfrom(64)
        except socket.timeout:
            continue # return to main thread every {TIMEOUT} seconds to allow KeyboardInterrupt
       
        parts = msg.strip().lower().split()
        if not parts:
            continue
        
        key = parts[0]
        if key in audio_bank:
            volume_override = None
            if len(parts) > 1:
                try:
                    volume_override = float(parts[1])
                except ValueError:
                    pass
            trigger_sound(key, volume_override)
except KeyboardInterrupt:
    print("\nInterruped by user. Exiting...\n")
    sys.exit(0)