import pyperclip
import whisper
import sounddevice as sd
import soundfile as sf
from pynput.keyboard import Key, Listener, KeyCode
import threading
import queue
import os
import logging
from pathlib import Path
import datetime
import subprocess


log_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(
    filename="logfile.log",
    level=logging.DEBUG,
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class VoiceNoteTranscriber:
    SAMPLE_RATE = 44100
    CHANNELS = 1
    AUDIO_FORMAT = "WAV"
    FILENAME = "tmp.wav"
    NOTES_FILE = "notes.txt"
    WHISPER_MODEL = "small.en"

    def __init__(self):
        self.queue = queue.Queue()
        self.recording = False
        self.file_written = threading.Event()
        self.cmd_pressed = False
        self.alt_pressed = False
        self.mode = None
        self.file_path = Path(__file__).parent / self.FILENAME
        self.resume_playback = False

    def audio_callback(self, indata, frames, time, status):
        """Callback function for each audio block from the microphone."""
        if status:
            logging.error(status)
        self.queue.put(indata.copy())

    def file_writing_thread(self):
        """Write data from queue to file until *None* is received."""
        with sf.SoundFile(
            self.file_path,
            mode="x",
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            format=self.AUDIO_FORMAT,
        ) as f:
            while True:
                data = self.queue.get()
                if data is None:
                    break
                f.write(data)
        self.file_written.set()
        logging.info("Audio file saved")

    def start_recording(self):
        """Start recording audio."""
        self.recording = True
        self.file_written.clear()
        threading.Thread(target=self.file_writing_thread).start()
        with sd.InputStream(
            callback=self.audio_callback,
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
        ):
            while self.recording:
                sd.sleep(1000)
        self.queue.put(None)

    def add_text_to_file(self, text, file_path):
        """Append text to a specified file."""
        with open(file_path, "a") as file:
            file.write("\n\n" + text)

    def process_recording(self):
        """Process the recorded audio."""
        self.recording = False
        self.file_written.wait()
        if self.file_path.exists():
            try:
                text = whisper.transcribe(
                    str(self.file_path), model=self.WHISPER_MODEL
                )["text"]
                logging.info(f"transcription: {text}")
                if self.mode == "file":
                    self.add_text_to_file(text, Path(__file__).parent / self.NOTES_FILE)
                elif self.mode == "clip":
                    pyperclip.copy(text)
            except Exception as e:
                logging.error(f"Error during transcription: {e}")
        else:
            logging.error("Error: Audio file not found.")

    def get_spotify_state(self):
        """Check if Spotify is playing."""
        script = 'tell application "Spotify" to player state as string'
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        return result.stdout.strip()

    def toggle_spotify_playback(self):
        """Pause/Play Spotify."""
        script = 'tell application "Spotify" to playpause'
        subprocess.run(["osascript", "-e", script])

    def on_press(self, key: (Key | KeyCode | None)):
        """Handle key press events."""
        logging.info(key)
        if key in [Key.cmd, Key.cmd_r, Key.cmd_l]:
            self.cmd_pressed = True
        elif key in [Key.ctrl, Key.ctrl_r, Key.ctrl_l]:
            self.ctrl_pressed = True
        elif (
            key in [KeyCode.from_char("j"), KeyCode.from_char("l")]
            and self.cmd_pressed
            and self.ctrl_pressed
            and not self.recording
        ):
            self.resume_playback = self.get_spotify_state() == "playing"
            if self.resume_playback:
                self.toggle_spotify_playback()
            if self.file_path.exists():
                os.remove(self.file_path)
            self.mode = "file" if key == "l" else "clip"
            logging.info(
                f"Recording now, mode: {self.mode}, resume playback: {self.resume_playback}"
            )
            threading.Thread(target=self.start_recording).start()

    def on_release(self, key):
        """Handle key release events."""
        if key in [Key.cmd, Key.cmd_r] and self.recording:
            self.cmd_pressed = False
            self.ctrl_pressed = False
            if self.resume_playback:
                self.toggle_spotify_playback()
            self.process_recording()


def main():
    transcriber = VoiceNoteTranscriber()
    logging.debug(f"Script started at {datetime.datetime.now()}")
    with Listener(
        on_press=transcriber.on_press, on_release=transcriber.on_release
    ) as listener:
        listener.join()


if __name__ == "__main__":
    main()
