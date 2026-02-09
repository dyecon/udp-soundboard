# udp-soundboard
UDP-based soundboard that plays sounds on a specified output device. Sounds played in quick succession will be overlayed on top of each other.
> [!NOTE]
> The specified audio output device must have its volume turned up in system settings.

## Usage
### Method 1: Python
1. Install dependencies:
    ```
    python -m pip install sounddevice soundfile
    ```
2. Add MP3 or WAV files to the `sounds` directory
3. Run the script:
    ```
    python udp-soundboard.py
    ```
    Then follow the on-screen instructions to select an audio output device.
4. To play a sound, send a UDP message to 127.0.0.1:5001 in the format of `{sound name} {volume}`. For example, to play `chime.mp3` at 70% volume, send `chime 0.7`. 
Omit the volume parameter to use the default volume (defined by `DEFAULT_VOLUME`).

### Method 2: Standalone
The standalone version does not require Python to be installed on your system.
1. Download the latest release from [Releases](https://github.com/dyecon/udp-soundboard/releases) and unzip it.
2. Add MP3 or WAV files to the `_internal/sounds` directory.
3. Double-click the executable to launch the app, then follow the on-screen instructions to select an audio output device.
> [!NOTE]
> macOS users may need to run the following command to launch the app:
> ```
>  xattr -d com.apple.quarantine -r /path/to/project/
> ``` 
> Replace `/path/to/project` with the folder containing both the executable and the _internal directory. 
4. To play a sound, send a UDP message to 127.0.0.1:5001 in the format of `{sound name} {volume}`. For example, to play `chime.mp3` at 70% volume, send `chime 0.7`.
Omit the volume parameter to use the default volume (defined by `DEFAULT_VOLUME`).

### Method 3: Build standalone app from source
1. Install dependencies:
    ```
    python -m pip install sounddevice soundfile pyinstaller
    ```
2. In the directory where `udp-soundboard.py` is located, run:
    ```sh
    pyinstaller --add-data="sounds/:sounds/" udp-soundboard.py
    ```
    This will create an executable in dist/udp-soundboard/.
3. Add audio files and run the program as described in method 2.

## Known issues
- May not run on Windows ARM due to issues with the PortAudio library.

## Credits
Included audio file: [Get ruby SE](https://opengameart.org/content/get-ruby-se)  by mieki256 (public domain)
